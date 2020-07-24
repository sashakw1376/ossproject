import os
import plotly.graph_objects as go

from datetime import datetime
from collections import Counter
from jinja2 import Environment, FileSystemLoader
from typing import List, Dict, Set

from ..cve_scanner import CVEData
from ..log import LOGGER


def output_html(
    all_cve_data: Set[CVEData],
    filename: str,
    theme_dir: str,
    total_files: int,
    products_with_cve: int,
    products_without_cve: int,
    logger: LOGGER,
    outfile,
):
    """Returns a HTML report for CVE's
    """

    # Step 1: Load all the templates

    # Root folder where html_reports is present
    root = os.path.dirname(os.path.abspath(__file__))

    # Template Directory contains all the html files
    templates_dir = os.path.join(root, "html_reports")
    templates_env = Environment(loader=FileSystemLoader([theme_dir, templates_dir]))

    temp_base = "templates/base.html"
    temp_dash = "templates/dashboard.html"
    temp_product = "templates/row_product.html"
    temp_cve = "templates/row_cve.html"

    base = templates_env.get_template(temp_base)
    dashboard = templates_env.get_template(temp_dash)
    cve_row = templates_env.get_template(temp_cve)
    product_row = templates_env.get_template(temp_product)

    # Step 2: Prepare Charts
    # Start generating graph with the data

    # dash graph1: Products Vulnerability Graph
    product_pie = go.Figure(
        data=[
            go.Pie(
                labels=["Vulnerable", "No Known Vulnerability"],
                values=[products_with_cve, products_without_cve],
                hole=0.4,
            )
        ]
    )

    # Chart configuration for product_pie
    product_pie.update_layout(
        autosize=True, legend_orientation="h",
    )
    product_pie.update_traces(
        hoverinfo="label+percent",
        textinfo="value",
        textfont_size=14,
        marker=dict(colors=["#d80032", "#1a936f"], line=dict(color="white", width=2),),
    )

    # dash graph2: Product CVE's Graph
    cve_bar = go.Figure()
    for product in all_cve_data:
        if product.cves:
            cve_bar.add_trace(
                go.Bar(
                    x=[f"{product.vendor}-{product.product}({product.version})"],
                    y=[len(product.cves)],
                    name=f"{product.product}-{product.version}",
                )
            )

    # Chart configuration for cve_bar
    cve_bar.update_layout(yaxis_title="Number of CVE's",)

    products_found = ""
    # List of Products
    for product in all_cve_data:
        # Check if product contains CVEs
        if product.cves:

            # List cves contains template version of all the cves
            list_cves = ""

            # hid will be used as id by HTML report to remove collisions
            hid = f"{product.vendor}{product.product}{''.join(product.version.split('.'))}"

            for i, cve in enumerate(product.cves):
                # render CVE template with data and add to list_cves
                list_cves += cve_row.render(
                    cve_number=cve.cve_number,
                    severity=cve.severity,
                    description=cve.description,
                    var_id=f"{hid}{i}",
                    fix_id=hid,
                )

            analysis_data = Counter(cve.severity for cve in product.cves)

            # initialize a figure object for Analysis Chart
            analysis_pie = go.Figure(
                data=[
                    go.Pie(
                        labels=list(analysis_data.keys()),
                        values=list(analysis_data.values()),
                        hole=0.4,
                    )
                ]
            )
            colors_avail = {
                "CRITICAL": "#f25f5c",
                "HIGH": "#ee6c4d",
                "MEDIUM": "#f4d35e",
                "LOW": "#90a955",
                "UNKNOWN": "#808080",
            }
            colors = [colors_avail[label] for label in analysis_data.keys()]
            analysis_pie.update_traces(
                hoverinfo="label+percent",
                textinfo="value",
                textfont_size=14,
                marker=dict(colors=colors, line=dict(color="white", width=2),),
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
        total_files=total_files,
        products_with_cve=products_with_cve,
    )

    # try to load the bigger files just before the generation of report

    # css template names
    css_main = "css/main.css"
    css_bootstrap = "css/bootstrap.css"

    style_main = templates_env.get_template(css_main)
    style_bootstrap = templates_env.get_template(css_bootstrap)

    # js template names
    js_main = "js/main.js"
    js_bootstrap = "js/bootstrap.js"
    js_plotly = "js/plotly.js"
    js_jquery = "js/jquery.js"

    script_main = templates_env.get_template(js_main)
    script_bootstrap = templates_env.get_template(js_bootstrap)
    script_plotly = templates_env.get_template(js_plotly)
    script_jquery = templates_env.get_template(js_jquery)

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

    logger.info(f"HTML Report is stored at location {filename}")
