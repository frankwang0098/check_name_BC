from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright
import re

app = Flask(__name__)

@app.route('/')
def home():
    return "Playwright Server is running!"

@app.route('/scrape', methods=['POST'])
def scrape():
    url = "https://www.names.bcregistry.gov.bc.ca/"
    data = request.json or {}
    input_name = data.get("name", "JAMES' BURGER")
    input_designation = data.get("designation", "CORP.")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        #browser = p.chromium.launch(executable_path="/usr/bin/chromium", args=["--disable-gpu", "--no-sandbox", "--headless"])
        page = browser.new_page()
        page.goto(url)

        page.get_by_role("button", name="Action").click()
        page.get_by_role("menuitem", name="For businesses that do not").locator("div").first.click()
        page.get_by_text("Start a new BC-based business").click()
        page.get_by_role("button", name="Select type of business in B.").click()
        page.get_by_text("Limited Company").click()
        page.get_by_role("textbox", name="Enter a name to request").click()
        page.get_by_role("textbox", name="Enter a name to request").fill(input_name)
        page.get_by_role("button", name="Select a Designation").click()
        page.get_by_text(input_designation).click()
        page.get_by_role("button", name="Check this Name").click()

        # wait until selector contains " Attention Required " or " Ready for Review ".
        selector_review_ready = "div#name-check-verdict.row.white.mt-7.pa-2.no-gutters.align-center"
        page.wait_for_function(
            """selector => {
                const el = document.querySelector(selector);
                if (!el) return false;
                const text = el.innerText.trim();
                return text.includes("Attention Required") || text.includes("Ready for Review");
            }""",
            arg=selector_review_ready
        )
        name_review_status = page.locator(selector_review_ready).text_content()

        finalResult = {"Status": name_review_status}

        if "Attention Required" in name_review_status:
            #Name Structure Check
            if page.get_by_role("tab", name=re.compile(r"Name Structure Check OK")).count() == 0:
                selector_name_structure = "div.row.conflict-row.py-5.px-4.border-top.no-gutters"
                name_structure_problem = page.locator(selector_name_structure).text_content()
                # Remove the "Read More" text from the extracted content.
                name_structure_problem_cleaned = name_structure_problem.replace("Read More", "").strip()
                finalResult["Name Structure"] = name_structure_problem_cleaned

            #Similar Name Check
            if page.get_by_role("tab", name=re.compile(r"Similar Name Check OK")).count() == 0:
                page.get_by_role("tab", name=re.compile(r"Similar Name Check \d+")).first.click()
                page.get_by_role("row", name="Similar names are currently").locator("i").nth(1).click()
                selector_similar_names = "div.row.px-15.no-gutters"
                similar_names = page.locator(selector_similar_names).text_content()
                finalResult["Similar Names"] = similar_names

        browser.close()

    return jsonify(finalResult)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
