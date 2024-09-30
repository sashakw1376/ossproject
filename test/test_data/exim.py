# Copyright (C) 2022 Orange
# SPDX-License-Identifier: GPL-3.0-or-later

mapping_test_data = [
    {"product": "exim", "version": "4.96", "version_strings": ["exim/4.96"]},
    {
        "product": "exim",
        "version": "4.96",
        "version_strings": ["4.96\n<<eximversion>>"],
    },
    {"product": "exim", "version": "4.94.2", "version_strings": ["exim/4.94.2"]},
]
package_test_data = [
    {
        "url": "http://rpmfind.net/linux/fedora/linux/development/rawhide/Everything/aarch64/os/Packages/e/",
        "package_name": "exim-4.96-3.fc38.aarch64.rpm",
        "product": "exim",
        "version": "4.96",
        "other_products": ["berkeley_db"],
    },
    {
        "url": "http://rpmfind.net/linux/fedora-secondary/development/rawhide/Everything/ppc64le/os/Packages/e/",
        "package_name": "exim-4.96-3.fc38.ppc64le.rpm",
        "product": "exim",
        "version": "4.96",
        "other_products": ["berkeley_db"],
    },
    {
        "url": "http://ftp.de.debian.org/debian/pool/main/e/exim4/",
        "package_name": "exim4-daemon-light_4.89-2+deb9u7_arm64.deb",
        "product": "exim",
        "version": "4.89",
        "other_products": ["berkeley_db"],
    },
    {
        "url": "http://ftp.de.debian.org/debian/pool/main/e/exim4/",
        "package_name": "exim4-daemon-light_4.94.2-7_mips64el.deb",
        "product": "exim",
        "version": "4.94.2",
        "other_products": ["berkeley_db"],
    },
    {
        "url": "https://downloads.openwrt.org/releases/22.03.0/packages/x86_64/packages/",
        "package_name": "exim_4.95-1_x86_64.ipk",
        "product": "exim",
        "version": "4.95",
        "other_products": ["berkeley_db", "gnutls"],
    },
]
