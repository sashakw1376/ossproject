# Copyright (C) 2022 Orange
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

mapping_test_data: list[dict] = []
package_test_data = [
    {
        "url": "http://rpmfind.net/linux/fedora/linux/development/rawhide/Everything/aarch64/os/Packages/u/",
        "package_name": "unbound-1.16.3-2.fc38.aarch64.rpm",
        "product": "unbound",
        "version": "1.16.3",
    },
    {
        "url": "http://rpmfind.net/linux/fedora-secondary/development/rawhide/Everything/ppc64le/os/Packages/u/",
        "package_name": "unbound-1.16.3-2.fc38.ppc64le.rpm",
        "product": "unbound",
        "version": "1.16.3",
    },
    {
        "url": "http://ftp.fr.debian.org/debian/pool/main/u/unbound/",
        "package_name": "unbound_1.6.0-3+deb9u2_arm64.deb",
        "product": "unbound",
        "version": "1.6.0",
    },
    {
        "url": "https://downloads.openwrt.org/releases/packages-19.07/x86_64/packages/",
        "package_name": "unbound-daemon-heavy_1.13.1-1_x86_64.ipk",
        "product": "unbound",
        "version": "1.13.1",
    },
]
