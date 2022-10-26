# Copyright (C) 2022 Orange
# SPDX-License-Identifier: GPL-3.0-or-later


"""
CVE checker for iperf3

https://www.cvedetails.com/product/116968/Iperf3-Project-Iperf3.html?vendor_id=27537

"""
from cve_bin_tool.checkers import Checker


class Iperf3Checker(Checker):
    CONTAINS_PATTERNS = []
    FILENAME_PATTERNS = []
    VERSION_PATTERNS = [r"iperf ([0-9]+\.[0-9]+\.?[0-9]*)"]
    VENDOR_PRODUCT = [("iperf3_project", "iperf3")]
