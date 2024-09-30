# Copyright (C) 2022 Orange
# SPDX-License-Identifier: GPL-3.0-or-later

mapping_test_data = [
    {"product": "nmap", "version": "7.93", "version_strings": ["7.93\nNmap"]}
]
package_test_data = [
    {
        "url": "http://rpmfind.net/linux/fedora/linux/updates/35/Everything/aarch64/Packages/n/",
        "package_name": "nmap-7.93-2.fc35.aarch64.rpm",
        "product": "nmap",
        "version": "7.93",
        "other_products": ["lua"],
    },
    {
        "url": "http://rpmfind.net/linux/fedora/linux/updates/35/Everything/armhfp/Packages/n/",
        "package_name": "nmap-7.93-2.fc35.armv7hl.rpm",
        "product": "nmap",
        "version": "7.93",
        "other_products": ["lua"],
    },
    {
        "url": "http://ftp.fr.debian.org/debian/pool/main/n/nmap/",
        "package_name": "nmap_7.40-1_amd64.deb",
        "product": "nmap",
        "version": "7.40",
    },
    {
        "url": "https://downloads.openwrt.org/releases/packages-19.07/x86_64/packages/",
        "package_name": "nmap_7.70-1_x86_64.ipk",
        "product": "nmap",
        "version": "7.70",
    },
]
