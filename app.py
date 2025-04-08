from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright

app = Flask(__name__)

@app.route('/')
def home():
    return "Playwright Server is running!"

@app.route('/scrape', methods=['POST'])
def scrape():
    url = "https://www.names.bcregistry.gov.bc.ca/"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        page.goto(url)

        page_title = page.locator("div.mt-4.col-md-6.col-lg-6.col-12").text_content()

        context.close()
        browser.close()

    return jsonify({"title": page_title})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
