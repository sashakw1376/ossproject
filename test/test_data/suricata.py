# Copyright (C) 2022 Orange
# SPDX-License-Identifier: GPL-3.0-or-later

mapping_test_data = [
    {"product": "suricata", "version": "6.0.6", "version_strings": ["suricata-6.0.6"]},
    {
        "product": "suricata",
        "version": "3.2.1",
        "version_strings": ["3.2.1 RELEASE\nClosing Suricata"],
    },
]
package_test_data = [
    {
        "url": "http://rpmfind.net/linux/fedora/linux/development/rawhide/Everything/aarch64/os/Packages/s/",
        "package_name": "suricata-6.0.6-2.fc37.aarch64.rpm",
        "product": "suricata",
        "version": "6.0.6",
        "other_products": ["rust"],
    },
    {
        "url": "http://rpmfind.net/linux/fedora-secondary/development/rawhide/Everything/s390x/os/Packages/s/",
        "package_name": "suricata-6.0.6-2.fc37.s390x.rpm",
        "product": "suricata",
        "version": "6.0.6",
        "other_products": ["rust"],
    },
    {
        "url": "http://ftp.br.debian.org/debian/pool/main/s/suricata/",
        "package_name": "suricata_3.2.1-1+deb9u1_arm64.deb",
        "product": "suricata",
        "version": "3.2.1",
    },
    {
        "url": "http://ftp.br.debian.org/debian/pool/main/s/suricata/",
        "package_name": "suricata_4.1.2-2+deb10u1_amd64.deb",
        "product": "suricata",
        "version": "4.1.2",
        "other_products": ["rust"],
    },
]
