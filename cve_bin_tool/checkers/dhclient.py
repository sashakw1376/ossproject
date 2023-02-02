# Copyright (C) 2022 Intel Corporation
# SPDX-License-Identifier: GPL-3.0-or-later


"""
CVE checker for dhcp-client

This checker only supports .rpm distros as no useful version patterns were found for .deb

https://www.cvedetails.com/product/610/ISC-Dhcp-Client.html?vendor_id=64

"""
from __future__ import annotations

from cve_bin_tool.checkers import Checker


class DhclientChecker(Checker):
    CONTAINS_PATTERNS: list[str] = []
    FILENAME_PATTERNS: list[str] = [r"dhclient"]
    VERSION_PATTERNS = [
        r'"name":"dhcp","version":"([0-9]+.[0-9]+(.[0-9]+)?)',
        r"dhcp([0-9]+.[0-9]+(.[0-9]+)?)",
    ]
    VENDOR_PRODUCT = [("isc", "dhcp")]
