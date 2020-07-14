import csv
import json
import os
import textwrap
import webbrowser
from collections import defaultdict
from datetime import datetime
from logging import Logger
from typing import List, Dict, Set

import plotly.graph_objects as go
from jinja2 import Environment, FileSystemLoader
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from .cve_scanner import CVEData
from .input_engine import Remarks
from .log import LOGGER


class OutputEngine(object):
    def __init__(
        self,
        all_cve_data: Set[CVEData],
        filename: str,
        logger: Logger = None,
        products_with_cve: int = 0,
        products_without_cve: int = 0,
        total_files: int = 0,
    ):
        self.logger = logger or LOGGER.getChild(self.__class__.__name__)
        self.all_cve_data = all_cve_data
        self.filename = os.path.abspath(filename) if filename else ""
        self.products_with_cve = products_with_cve
        self.products_without_cve = products_without_cve
        self.total_files = total_files

    def generate_filename(self, extension=None):
        """ Generates a random filename"""
        if extension:
            now = datetime.now().strftime("%Y-%m-%d.%H-%M-%S")
            self.filename = os.path.abspath(
                os.path.join(os.getcwd(), f"output.cve-bin-tool.{now}.{extension}")
            )

    def output_cves(self, outfile, output_type=None):
        """ Output a list of CVEs
        format self.checkers[checker_name][version] = dict{id: severity}
        to other formats like CSV or JSON
        """
        if output_type == "json":
            self.output_json(outfile)
        elif output_type == "csv":
            self.output_csv(outfile)
        elif output_type == "html":
            self.output_html(outfile)
        else:  # console, or anything else that is unrecognised
            self.output_console()

    def format_output(self) -> List[Dict[str, str]]:
        """
        summary: format output in the list of dictionary format.

        Returns:
            formatted_output: List[Dict[str, str]]
            - example:  [
                            {
                                "vendor": "haxx"
                                "product": "curl",
                                "version": "1.2.1",
                                "cve_number": "CVE-1234-1234",
                                "severity": "LOW"
                            },
                            ...
                        ]
        """
        formatted_output = []
        for product in self.all_cve_data:
            for cve in product.cves:
                formatted_output.append(
                    {
                        "vendor": product.vendor,
                        "product": product.product,
                        "version": product.version,
                        "remarks": product.remarks.name,
                        "cve_number": cve.cve_number,
                        "severity": cve.severity,
                    }
                )
        return formatted_output

    def output_json(self, outfile):
        """ Output a JSON of CVEs """
        formatted_output = self.format_output()
        json.dump(formatted_output, outfile, indent="    ")

    def output_csv(self, outfile):
        """ Output a CSV of CVEs """
        formatted_output = self.format_output()
        writer = csv.DictWriter(
            outfile,
            fieldnames=[
                "vendor",
                "product",
                "version",
                "cve_number",
                "severity",
                "remarks",
            ],
        )
        writer.writeheader()
        writer.writerows(formatted_output)

    def output_console(self, console=Console()):
        """ Output list of CVEs in a tabular format with color support """

        now = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")

        console.print(
            Markdown(
                textwrap.dedent(
                    f"""
                    # CVE BINARY TOOL
                    - cve-bin-tool Report Generated: {now}
                    """
                )
            )
        )

        # colors provide color name according to the severity
        colors = {
            "CRITICAL": "red",
            "HIGH": "blue",
            "MEDIUM": "yellow",
            "LOW": "green",
            "UNKNOWN": "white",
        }

        remarks_colors = {
            Remarks.Mitigated: "green",
            Remarks.Confirmed: "red",
            Remarks.NewFound: "blue",
            Remarks.Unexplored: "yellow",
            Remarks.Ignored: "white",
        }

        cve_by_remarks: defaultdict[Remarks, List[Dict[str, str]]] = defaultdict(list)
        # group cve_data by its remarks
        for product in self.all_cve_data:
            for cve in product.cves:
                cve_by_remarks[product.remarks].append(
                    {
                        "vendor": product.vendor,
                        "product": product.product,
                        "version": product.version,
                        "cve_number": cve.cve_number,
                        "severity": cve.severity,
                    }
                )

        for remarks in sorted(cve_by_remarks):
            color = remarks_colors[remarks]
            console.print(
                Panel(f"[{color}] {remarks.name} CVEs [/{color}]", expand=False)
            )
            # table instance
            table = Table()

            # Add Head Columns to the Table
            table.add_column("Vendor")
            table.add_column("Product")
            table.add_column("Version")
            table.add_column("CVE Number")
            table.add_column("Severity")

            for cve_data in cve_by_remarks[remarks]:
                color = colors[cve_data["severity"]]
                table.add_row(
                    f'[{color}]{cve_data["vendor"]} [/{color}]',
                    f'[{color}]{cve_data["product"]} [/{color}]',
                    f'[{color}]{cve_data["version"]} [/{color}]',
                    f'[{color}]{cve_data["cve_number"]} [/{color}]',
                    f'[{color}]{cve_data["severity"]} [/{color}]',
                )
            # Print the table to the console
            console.print(table)

    def output_file(self, output_type="csv"):

        """ Generate a file for list of CVE """
        if output_type == "console":
            # short circuit file opening logic if we are actually
            # just writing to stdout
            self.output_cves(self.filename, output_type)
            return

        # Check if we need to generate a filename
        if not self.filename:
            self.generate_filename(output_type)
        else:
            # check if the filename already exists
            if os.path.isfile(self.filename):
                self.logger.warning(
                    f"Failed to write at '{self.filename}'. File already exists"
                )
                self.logger.info(
                    "Generating a new filename with Default Naming Convention"
                )
                self.generate_filename(output_type)

            # try opening that file
            try:
                with open(self.filename, "w") as f:
                    f.write("testing")
                os.remove(self.filename)
            except Exception as E:
                self.logger.warning(E)
                self.logger.info("Switching Back to Default Naming Convention")
                self.generate_filename(output_type)

        # Log the filename generated
        self.logger.info(f"Output stored at {self.filename}")

        # call to output_cves
        with open(self.filename, "w") as f:
            self.output_cves(f, output_type)

    def output_html(self, outfile):
        """Returns a HTML report for CVE's
        """

        # Step 1: Load all the templates

        # Root folder where html_reports is present
        root = os.path.dirname(os.path.abspath(__file__))

        # Template Directory contains all the html files
        templates_dir = os.path.join(root, "html_reports", "templates")
        templates_env = Environment(loader=FileSystemLoader(templates_dir))
        base = templates_env.get_template("base.html")
        dashboard = templates_env.get_template("dashboard.html")
        cve_row = templates_env.get_template("row_cve.html")
        product_row = templates_env.get_template("row_product.html")

        # Step 2: Prepare Charts
        # Start generating graph with the data

        # dash graph1: Products Vulnerability Graph
        product_pie = go.Figure(
            data=[
                go.Pie(
                    labels=["Vulnerable", "No Known Vulnerability"],
                    values=[self.products_with_cve, self.products_without_cve],
                    hole=0.4,
                )
            ]
        )

        # Chart configuration for product_pie
        product_pie.update_layout(
            autosize=True, legend_orientation="h",
        )

        # dash graph2: Product CVE's Graph
        cve_bar = go.Figure()
        for product in self.all_cve_data:
            if product.cves:
                cve_bar.add_trace(
                    go.Bar(
                        x=[f"{product.product}-{product.version}"],
                        y=[len(product.cves)],
                        name=f"{product.product[:7]}",
                    )
                )

        # Chart configuration for cve_bar
        cve_bar.update_layout(yaxis_title="Number of CVE's",)

        products_found = ""
        # List of Products
        for product in self.all_cve_data:
            # Check if product contains CVEs
            if product.cves:

                # List cves contains template version of all the cves
                list_cves = ""

                # hid will be used as id by HTML report to remove collisions
                hid = f"{product.vendor}{product.product}{''.join(product.version.split('.'))}"

                analysis_data = {"critical": 0, "high": 0, "medium": 0, "low": 0}
                for i, cve in enumerate(product.cves):
                    # render CVE template with data and add to list_cves
                    list_cves += cve_row.render(
                        cve_number=cve.cve_number,
                        severity=cve.severity,
                        description=cve.description,
                        var_id=f"{hid}{i}",
                        fix_id=hid,
                    )

                    # generate analysis_data
                    if cve.severity.lower() == "critical":
                        analysis_data["critical"] += 1
                    elif cve.severity.lower() == "high":
                        analysis_data["high"] += 1
                    elif cve.severity.lower() == "medium":
                        analysis_data["medium"] += 1
                    elif cve.severity.lower() == "low":
                        analysis_data["low"] += 1
                    else:
                        pass

                # initialize a figure object for Analysis Chart
                analysis_pie = go.Figure(
                    data=[
                        go.Pie(
                            labels=["Critical", "High", "Medium", "Low"],
                            values=[
                                analysis_data["critical"],
                                analysis_data["high"],
                                analysis_data["medium"],
                                analysis_data["low"],
                            ],
                            hole=0.4,
                        )
                    ]
                )
                analysis_pie.update_traces(
                    hoverinfo="label+percent",
                    textinfo="value",
                    textfont_size=14,
                    marker=dict(
                        colors=["#f25f5c", "#ee6c4d", "#f4d35e", "#90a955"],
                        line=dict(color="white", width=2),
                    ),
                )
                analysis_pie.update_layout(
                    autosize=True,
                    height=300,
                    legend_orientation="h",
                    margin=dict(l=0, r=20, t=0, b=0),
                    # paper_bgcolor="LightSteelBlue",
                )

                products_found += product_row.render(
                    vendor=product.vendor,
                    name=product.product,
                    version=product.version,
                    cve_count=len(product.cves),
                    list_cves=list_cves,
                    severity_analysis=analysis_pie.to_html(
                        full_html=False, include_plotlyjs=False
                    ),
                    fix_id=hid,
                )

        # Dashboard Rendering
        dashboard = dashboard.render(
            graph_cves=cve_bar.to_html(full_html=False, include_plotlyjs=False),
            graph_products=product_pie.to_html(full_html=False, include_plotlyjs=False),
            total_files=self.total_files,
            files_with_cve=self.products_with_cve,
        )

        # try to load the bigger files just before the generation of report

        # Style directory conatains all the CSS files
        styles_dir = os.path.join(root, "html_reports", "css")
        styles_env = Environment(loader=FileSystemLoader(styles_dir))
        style_main = styles_env.get_template("main.css")
        style_bootstrap = styles_env.get_template("bootstrap.min.css")

        # Script directory will contain all the JS files
        scripts_dir = os.path.join(root, "html_reports", "js")
        scripts_env = Environment(loader=FileSystemLoader(scripts_dir))
        script_main = scripts_env.get_template("main.js")
        script_bootstrap = scripts_env.get_template("bootstrap.min.js")
        script_plotly = scripts_env.get_template("plotly-latest.min.js")
        script_jquery = scripts_env.get_template("jquery-3.4.1.slim.min.js")

        # Render the base html to generate report
        outfile.write(
            base.render(
                date=datetime.now().strftime("%d %b %Y"),
                dashboard=dashboard,
                products_found=products_found,
                style_main=style_main.render(),
                style_bootstrap=style_bootstrap.render(),
                script_main=script_main.render(),
                script_jquery=script_jquery.render(),
                script_bootstrap=script_bootstrap.render(),
                script_plotly=script_plotly.render(),
            )
        )

        self.logger.info(f"Report is stored at location {self.filename}")
        self.logger.info("Opening Report in Browser. Please Wait...")
        try:
            webbrowser.open(self.filename)
        except webbrowser.Error:
            self.logger.warning("Can't Open in Browser")
