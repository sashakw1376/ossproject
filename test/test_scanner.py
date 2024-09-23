# Copyright (C) 2021 Intel Corporation
# SPDX-License-Identifier: GPL-3.0-or-later

"""
CVE-bin-tool tests
"""
from __future__ import annotations

import contextlib
import importlib
import io
import logging
import os
import shutil
import sys
import tarfile
import tempfile
import unittest
import unittest.mock
from pathlib import Path
from test.utils import LONG_TESTS, download_file
from cve_bin_tool.util import windows_filename_check
import pytest
from pytest_mock import MockerFixture

from cve_bin_tool.checkers import __all__ as all_test_name
from cve_bin_tool.cvedb import CVEDB
from cve_bin_tool.version_scanner import VersionScanner

# load test data
test_data = list(
    map(lambda x: importlib.import_module(f"test.test_data.{x}"), all_test_name[2:])
)
mapping_test_data = map(lambda x: x.mapping_test_data, test_data)
package_test_data = []
for data in map(lambda x: x.package_test_data, test_data):
    for i in range(len(data)):
        if "other_products" not in data[i]:
            data[i]["other_products"] = []
    package_test_data.append(data)
all_the_tests = []
for i in test_data:
    prod = i.package_test_data
    if len(prod) != 0:
        prod_list = []
        for i in prod:
            if i["product"] not in prod_list:
                prod_list.append(i["product"])
        for i in prod_list:
            all_the_tests.append(i)

DISABLED_TESTS_ACTIONS: list[str] = []
DISABLED_TESTS_LOCAL: list[str] = []
DISABLED_TESTS_WINDOWS: list[str] = []


class TestScanner:
    """Runs a series of tests against our "faked" binaries.

    The faked binaries are very small c files containing the same string signatures we use
    in the cve-bin-tool.  They should trigger results as if they contained the library and
    version specified in the file name.

    At this time, the tests work only in python3.
    """

    @classmethod
    def setup_class(cls):
        cls.cvedb = CVEDB()
        if os.getenv("UPDATE_DB") == "1":
            cls.cvedb.get_cvelist_if_stale()
        else:
            print("Skip NVD database updates.")
        # Instantiate a scanner
        cls.scanner = VersionScanner(should_extract=True)
        # temp dir for mapping tests
        cls.mapping_test_dir = tempfile.mkdtemp(prefix="mapping-test-")
        # temp dir for tests that require downloads
        cls.package_test_dir = tempfile.mkdtemp(prefix="package_test-")

    @classmethod
    def teardown_class(cls):
        shutil.rmtree(cls.package_test_dir)
        shutil.rmtree(cls.mapping_test_dir)

    def test_false_positive(self):
        self.scanner.all_cves = []
        with tempfile.NamedTemporaryFile(
            "w+b",
            suffix="-test-false-positive.out",
            dir=self.mapping_test_dir,
            delete=False,
        ) as f:
            common_signatures = [
                # common strings generated by a compiler
                b"\x7f\x45\x4c\x46\x02\x01\x01\x03\n",
                b"GCC: (x86_64-posix-seh-rev0, Built by MinGW-W64 project) 8.1.0\n",
                b"GNU C17 8.1.0 -mtune=core2 -march=nocona -g -g -g -O2 -O2 -O2 -fno-ident -fbuilding-libgcc -fno-stack-protector\n",
                b"../../../../../src/gcca-8.1.0/libgcc/libgcc2.c\n",
                rb"C:\mingw810\x86_64-810-posix-seh-rt_v6-rev0\build\gcca-8.1.0\x86_64-w64-mingw32\libgcc\n",
                b"GCC: (Ubuntu 7.5.0-3ubuntu1~18.04) 7.5.0\n",
                # bare version strings.
                b"1_0",
                b"1_2_3",
                b"1.4",
                b"1.2.3",
                b"6.7a",
                b"8.9.10-11",
                b"1-2",
                b"1-2-4",
                b"1.2.3-rc.1",
            ]
            f.writelines(common_signatures)
            filename = f.name
        for params in self.scanner.scan_file(
            str(Path(self.mapping_test_dir) / filename)
        ):
            if params:
                pytest.fail(msg=f"Checker has detected false positive: {params}")

    @pytest.mark.parametrize(
        "product, version, version_strings",
        (
            pytest.param(
                d["product"],
                d["version"],
                d["version_strings"],
                marks=[
                    pytest.mark.skipif(
                        not LONG_TESTS(),
                        reason="Test reduction in short tests",
                    )
                ],
            )
            for list_data in mapping_test_data
            for d in list_data
        ),
    )
    def test_version_mapping(self, product, version, version_strings):
        """Helper function to scan a binary and check that it contains
        certain cves for a version and doesn't contain others."""

        # Run the scan
        version_strings = list(map(lambda s: f"{s}\n".encode("ascii"), version_strings))
        # first filename will test "is" and second will test "contains"
        filenames = [
            f"-{product}-{version}.out",
            f"{'.'.join(list(product))}-{version}.out",
        ]
        for filename in filenames:
            with tempfile.NamedTemporaryFile(
                "w+b",
                suffix=windows_filename_check(filename), #SASHA
                dir=self.mapping_test_dir,
                delete=False,
            ) as f:
                f.write(b"\x7f\x45\x4c\x46\x02\x01\x01\x03\n")
                f.writelines(version_strings)
                filename = f.name

            list_products = set()
            list_versions = set()
            expected_path = str(Path(self.mapping_test_dir) / filename)
            for scan_info in self.scanner.recursive_scan(expected_path):
                if scan_info:
                    product_info, file_path = scan_info
                    list_products.add(product_info.product)
                    list_versions.add(product_info.version)
                    assert file_path == expected_path
            assert product in list_products
            assert version in list_versions

    def make_condensed_from_download(self, download_path, condensed_path):
        """Extract a downloaded file recursively, find all the strings for each
        file. Create a new archive with only the strings that were found."""
        dot_extracted = ".extracted"
        file_lines_pairs = []

        class MakeCondensedVersionScanner(VersionScanner):
            def run_checkers(self, filename, lines):
                # Remove until .extracted plus 1 for the '/' after it. This will
                # give us the path to the file relative to the root of the
                # archive it came from
                # SASHA: TRY 1
                try:
                    filename_path = filename[
                        filename.index(dot_extracted) + len(dot_extracted) + 1 :
                    ]
                # Some files (e.g. OpenWRT Linux Kernel) are not an archive so
                # dot_extracted won't be found
                except ValueError:
                    filename_path = os.path.basename(filename)

                file_lines_pairs.append(
                    (
                        filename_path,
                        lines,
                    )
                )
                yield None

        # Run the recursive extraction
        for _ in MakeCondensedVersionScanner(should_extract=True).recursive_scan(
            download_path
        ):
            pass

        with contextlib.ExitStack() as stack:
            # gzip will add a last modified time by calling time.time, to ensure
            # that the hash is always the same, we set the time to 0
            stack.enter_context(unittest.mock.patch("time.time", return_value=1))
            # Create the archive
            with tarfile.open(condensed_path, mode="w|gz") as archive:
                for filepath, lines in file_lines_pairs:
                    # Create a bytes object for each file
                    fileobj = stack.enter_context(io.BytesIO())
                    fileobj.write(b"\x7f\x45\x4c\x46\x02\x01\x01\x03\n")
                    fileobj.write(lines.encode("ascii"))
                    # If we call write at all we need to seek back to the beginning
                    fileobj.seek(0)
                    # Create the TarInfo objects
                    tarinfo = tarfile.TarInfo(name=filepath)
                    tarinfo.size = len(fileobj.getvalue())
                    # Add the file to the archive
                    archive.addfile(tarinfo, fileobj=fileobj)

    def condensed_filepath(self, url, package_name):
        # Make directories for downloads and to store condensed versions
        tmp_dir = Path(__file__).parent.resolve()
        downloads_dir = tmp_dir / "downloads"
        condensed_dir = tmp_dir / "condensed-downloads"
        for dirpath in [downloads_dir, condensed_dir]:
            if not dirpath.is_dir():
                dirpath.mkdir()
        # Check if we've already made a condensed version of the file, if we
        # have, we're done.
        condensed_path = condensed_dir / (windows_filename_check(package_name) + ".tar.gz") #SASHA
        if condensed_path.is_file():
            return str(condensed_path)
        # Download the file if we don't have a condensed version of it and we
        # don't have it downloaded already
        download_path = downloads_dir / package_name
        if not download_path.is_file():
            download_file(url + package_name, download_path)
        # Make the condensed version of the file
        self.make_condensed_from_download(str(download_path), str(condensed_path))
        # Return the condensed version
        return str(condensed_path)

    @pytest.mark.parametrize(
        "url, package_name, product, version, other_products",
        (
            pytest.param(
                d["url"],
                d["package_name"],
                d["product"],
                d["version"],
                d["other_products"],
                marks=[
                    pytest.mark.skipif(
                        "ACTIONS" in os.environ
                        and os.environ["ACTIONS"] == "1"
                        and d["product"] in DISABLED_TESTS_ACTIONS,
                        reason=f"{d['product']} Long tests disabled due to issues working in github actions",
                    ),
                    pytest.mark.skipif(
                        "ACTIONS" not in os.environ
                        and d["product"] in DISABLED_TESTS_LOCAL,
                        reason=f"{d['product']} Long tests disabled locally",
                    ),
                    pytest.mark.skipif(
                        sys.platform == "win32"
                        and d["product"] in DISABLED_TESTS_WINDOWS,
                        reason=f"{d['product']} tests disabled for windows",
                    ),
                    pytest.mark.skipif(
                        sys.version_info[:2] == (3, 11)
                        and d["package_name"]
                        == "libvncserver1_0.9.12+dfsg-9ubuntu0.3_amd64.deb",
                        reason="Flaky test on Python 3.11",
                    ),
                ],
            )
            for list_data in package_test_data
            for d in list_data
        ),
    )
    @pytest.mark.skipif(not LONG_TESTS(), reason="Skipping long tests")
    def test_version_in_package(
        self, url, package_name, product, version, other_products
    ):
        """Helper function to get a file (presumed to be a real copy
        of a library, probably from a Linux distribution) and run a
        scan on it.  Any test using this should likely be listed as a
        long test."""
        # get file
        tempfile = self.condensed_filepath(url, package_name)
        # new scanner for the new test.
        # self.scanner = VersionScanner(self.cve_scanner, should_extract=True)
        # run the tests
        list_products = set()
        list_versions = set()
        for scan_info in self.scanner.recursive_scan(tempfile):
            if scan_info:
                product_info, file_path = scan_info
                list_products.add(product_info.product)
                list_versions.add(product_info.version)

        # Make sure the product and version are in the results
        assert (
            product in list_products
        ), f"""{product} not found in {package_name}.
        The checker signature or url may be incorrect."""
        assert version in list_versions
        product_not_present = all_the_tests.copy()
        product_not_present.remove(product)
        if other_products != []:
            for option in other_products:
                assert (
                    option in list_products
                ), f"""{option} not found in {package_name}. Remove {option} from other_products."""
                assert (
                    option in product_not_present
                ), f"""{option} not found in {product_not_present}. Remove {option} from other_products or add a test for {option} in test_data."""
                product_not_present.remove(option)
        for not_product in product_not_present:
            assert (
                not_product not in list_products
            ), f"""{not_product} found in {package_name}. If that's expected, make sure to add {not_product} to the expected list of other_products."""

    @pytest.mark.skipif(not LONG_TESTS(), reason="Skipping long tests")
    def test_version_in_package_make_download(self, mocker: MockerFixture):
        url = "https://kojipkgs.fedoraproject.org//packages/python3/3.8.2~rc1/1.fc33/aarch64/"
        package_name = "python3-3.8.2~rc1-1.fc33.aarch64.rpm"
        product = "python"
        version = "3.8.2"
        other_products = []

        mock_func = mocker.patch("pathlib.Path.is_file", return_value=True)

        self.test_version_in_package(
            url, package_name, product, version, other_products
        )

        assert mock_func.call_count > 0

    def test_does_not_scan_symlinks(self):
        """Test that the scanner doesn't scan symlinks"""
        if sys.platform.startswith("linux"):
            # we can only do this in linux since symlink is privilege operation in windows
            non_existant_link = Path("non-existant-link")
            non_existant_link_path = non_existant_link.resolve()
            non_existant_link.symlink_to("non-existant-file")
            try:
                with pytest.raises(StopIteration):
                    next(self.scanner.scan_file(str(non_existant_link_path)))
            finally:
                non_existant_link.unlink()

    def test_cannot_open_file(self, caplog):
        """Test behaviour when file cannot be opened"""
        self.scanner.logger.setLevel(logging.DEBUG)
        with pytest.raises(StopIteration):
            next(
                self.scanner.scan_file(
                    str(Path(self.mapping_test_dir) / "non-existant-file")
                )
            )
        assert str.find("Invalid file", caplog.text)

    def test_clean_file_path(self):
        filepath = "/tmp/cve-bin-tool/dhtei34fd/file_name.extracted/usr/bin/vulnerable_file"  # nosec
        # temp path is hardcoded for testing, not for usage
        expected_path = "/usr/bin/vulnerable_file"

        cleaned_path = self.scanner.clean_file_path(filepath)
        assert expected_path == cleaned_path
