import os
from playwright.sync_api import sync_playwright

URL = "https://viac.ch/produkte/hypothek/"


def main() -> None:
    print("Launching Playwright Debug…")
    os.makedirs("debug", exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print("Opening VIAC page…")
        page.goto(URL, timeout=60000)
        page.wait_for_timeout(5000)

        print("Saving debug dumps...")

        text = page.inner_text("body")
        html = page.content()

        with open("debug/debug_page.txt", "w", encoding="utf-8") as f:
            f.write(text)

        with open("debug/debug_html.html", "w", encoding="utf-8") as f:
            f.write(html)

        print("Preview (first 1000 chars):")
        print(text[:1000])

        browser.close()


if __name__ == "__main__":
    main()
