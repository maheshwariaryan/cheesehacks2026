from playwright.sync_api import sync_playwright
try:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        print("Chromium launched successfully")
        browser.close()
except Exception as e:
    print(f"Error: {e}")
