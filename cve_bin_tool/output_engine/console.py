# Copyright (C) 2021 Intel Corporation
# SPDX-License-Identifier: GPL-3.0-or-later

import textwrap
from collections import defaultdict
from datetime import datetime
from typing import Any, DefaultDict, Dict

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ..cve_scanner import CVEData
from ..input_engine import Remarks
from ..linkify import linkify_cve
from ..theme import cve_theme
from ..util import ProductInfo, VersionInfo
from ..version import VERSION
from .util import format_path, format_version_range, get_cve_summary


def output_console(*args: Any):
    """wrapper function for _output_console to enable output to a file"""

    ls_args = list(args)
    output_file = ls_args[-1]
    ls_args.pop()

    if output_file:
        with open(output_file, "wt", encoding="utf-8") as f:
            console = Console(theme=cve_theme, file=f)
            ls_args.append(console)
            _output_console_nowrap(*ls_args)
    else:
        _output_console_nowrap(*ls_args)


def _output_console_nowrap(
    all_cve_data: Dict[ProductInfo, CVEData],
    all_cve_version_info: Dict[str, VersionInfo],
    time_of_last_update: datetime,
    affected_versions: int,
    exploits: bool = False,
    console: Console = Console(theme=cve_theme),
):
    """Output list of CVEs in a tabular format with color support"""

    console._width = 120
    now = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
    time_of_last_update = time_of_last_update.strftime("%Y-%m-%d  %H:%M:%S")

    console.print(
        Markdown(
            textwrap.dedent(
                f"""
                # CVE BINARY TOOL version: {VERSION}
                - Report Generated: {now}
                - Time of last update of CVE Data: {time_of_last_update}
                """
            )
        )
    )

    remarks_colors = {
        Remarks.Mitigated: "green",
        Remarks.Confirmed: "red",
        Remarks.NewFound: "blue",
        Remarks.Unexplored: "yellow",
        Remarks.Ignored: "white",
    }

    # Create table instance for CVE Summary
    table = Table()
    # Add Head Columns to the Table
    table.add_column("Severity")
    table.add_column("Count")
    summary = get_cve_summary(all_cve_data, exploits)
    summary_color = {
        "CRITICAL": "red",
        "HIGH": "blue",
        "MEDIUM": "yellow",
        "LOW": "green",
    }

    for severity, count in summary.items():
        color = summary_color[severity.split("-")[0]]
        cells = [
            Text.styled(severity, color),
            Text.styled(str(count), color),
        ]
        table.add_row(*cells)
    # Print the table to the console
    console.print(Panel("CVE SUMMARY", expand=False))
    console.print(table)

    cve_by_remarks: DefaultDict[Remarks, list[dict[str, str]]] = defaultdict(list)
    cve_by_paths: DefaultDict[Remarks, list[dict[str, str]]] = defaultdict(list)
    # group cve_data by its remarks and separately by paths
    for product_info, cve_data in all_cve_data.items():
        for cve in cve_data["cves"]:
            cve_by_remarks[cve.remarks].append(
                {
                    "vendor": product_info.vendor,
                    "product": product_info.product,
                    "version": product_info.version,
                    "cve_number": cve.cve_number,
                    "severity": cve.severity,
                    "score": cve.score,
                    "cvss_version": cve.cvss_version,
                }
            )
            path_elements = ", ".join(cve_data["paths"])
            for path_element in path_elements.split(","):
                path_entry = {
                    "vendor": product_info.vendor,
                    "product": product_info.product,
                    "version": product_info.version,
                    "paths": path_element,
                }
                if path_entry not in cve_by_paths[cve.remarks]:
                    cve_by_paths[cve.remarks].append(path_entry)
            if affected_versions != 0:
                try:
                    version_info = all_cve_version_info[cve.cve_number]
                except KeyError:  # TODO: handle 'UNKNOWN' and some cves more cleanly
                    version_info = VersionInfo("", "", "", "")
                cve_by_remarks[cve.remarks][-1].update(
                    {"affected_versions": format_version_range(version_info)}
                )

    for remarks in sorted(cve_by_remarks):
        color = remarks_colors[remarks]
        console.print(Panel(f"[{color}] {remarks.name} CVEs [/{color}]", expand=False))
        # table instance
        table = Table()

        # Add Head Columns to the Table
        table.add_column("Vendor")
        table.add_column("Product")
        table.add_column("Version")
        table.add_column("CVE Number")
        table.add_column("Severity")
        table.add_column("Score (CVSS Version)")
        if affected_versions != 0:
            table.add_column("Affected Versions")
        # table.add_column("CVSS Version")

        for cve_data in cve_by_remarks[remarks]:
            color = cve_data["severity"].split("-")[0].lower()
            cells = [
                Text.styled(cve_data["vendor"], color),
                Text.styled(cve_data["product"], color),
                Text.styled(cve_data["version"], color),
                linkify_cve(Text.styled(cve_data["cve_number"], color)),
                Text.styled(cve_data["severity"], color),
                Text.styled(
                    str(cve_data["score"])
                    + " (v"
                    + str(cve_data["cvss_version"])
                    + ")",
                    color,
                ),
            ]
            if affected_versions != 0:
                cells.append(Text.styled(cve_data["affected_versions"], color))
            table.add_row(*cells)
        # Print the table to the console
        console.print(table)
        for cve_data in cve_by_remarks[remarks]:
            if "*" in cve_data["vendor"]:
                console.print("* vendors guessed by the tool")
                break

        # Show table of vulnerable products mapped to filename paths
        for path_remarks in sorted(cve_by_paths):
            color = "yellow"
            console.print(
                Panel(f"[{color}] {path_remarks.name} CVEs [/{color}]", expand=False)
            )
            # Table instance
            table = Table()

            # Add Head Columns to the Table
            table.add_column("Vendor")
            table.add_column("Product")
            table.add_column("Version")
            table.add_column("Root")
            table.add_column("Filename")
            color = "green"
            for cve_data in cve_by_paths[path_remarks]:
                path_root = format_path(cve_data["paths"])
                cells = [
                    Text.styled(cve_data["vendor"], color),
                    Text.styled(cve_data["product"], color),
                    Text.styled(cve_data["version"], color),
                    Text.styled(path_root[0], color),
                    Text.styled(path_root[1], color),
                ]
                table.add_row(*cells)
        # Print the table to the console
        console.print(table)
