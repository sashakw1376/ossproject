# Copyright (C) 2022 Orange
# SPDX-License-Identifier: GPL-3.0-or-later


"""
CVE checker for upx

https://www.cvedetails.com/product/40873/Upx-Project-UPX.html?vendor_id=17080

"""
from typing import List

from cve_bin_tool.checkers import Checker


class UpxChecker(Checker):
    CONTAINS_PATTERNS: List[str] = []
    FILENAME_PATTERNS: List[str] = []
    VERSION_PATTERNS = [r"UPX ([0-9]+\.[0-9]+\.?[0-9]*)"]
    VENDOR_PRODUCT = [("upx_project", "upx")]
