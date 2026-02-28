# NOTE: WeasyPrint requires system dependencies:
# macOS: brew install pango
# Linux: apt-get install libpango-1.0-0 libgdk-pixbuf2.0-0

from jinja2 import Environment, FileSystemLoader
import json
import os
from datetime import datetime

template_env = Environment(
    loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), "..", "templates"))
)

class ReportGenerator:

    def generate(self, report_type: str, deal: dict, analyses: dict,
                 narrative: dict) -> str:
        """
        1. Select template
        2. Build context
        3. Render HTML
        4. Convert to PDF via WeasyPrint (if available) or fallback to HTML.
        5. Return file path
        """
        template_map = {
            "iar": "iar_report.html",
            "dcf": "dcf_report.html",
            "red_flag": "red_flag_report.html",
            "qoe": "qoe_report.html",
            "nwc": "nwc_report.html",
            "executive_summary": "executive_summary.html",
        }

        template = template_env.get_template(template_map[report_type])

        # Provide fallback empty dicts for all analyses
        context = {
            "deal": deal,
            "generated_date": datetime.utcnow().strftime("%B %d, %Y"),
            "narrative": narrative or {},
            "qoe": analyses.get("qoe", {}),
            "working_capital": analyses.get("working_capital", {}),
            "ratios": analyses.get("ratios", {}),
            "dcf": analyses.get("dcf", {}),
            "red_flags": analyses.get("red_flags", []),
            "anomalies": analyses.get("anomalies", []),
            "ai_insights": analyses.get("ai_insights", {}),
        }

        html_content = template.render(**context)

        output_dir = os.path.abspath(f"./reports/{deal.get('id', 0)}")
        os.makedirs(output_dir, exist_ok=True)

        try:
            from playwright.sync_api import sync_playwright
            filepath = os.path.join(output_dir, f"{report_type}_report.pdf")
            
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                # Use load instead of networkidle to be faster and less prone to timeout if no external assets
                page.set_content(html_content, wait_until="load")
                page.pdf(
                    path=filepath,
                    format="A4",
                    print_background=True,
                    margin={"top": "2.54cm", "right": "2.54cm", "bottom": "2.54cm", "left": "2.54cm"}
                )
                browser.close()
                
            return filepath
        except Exception as e:
            print(f"Playwright failed: {e}")
            import traceback
            traceback.print_exc()
            filepath = os.path.join(output_dir, f"{report_type}_report.html")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(html_content)
            return filepath

