import csv
import os
import re
from datetime import datetime
from playwright.sync_api import sync_playwright

URL = "https://viac.ch/produkte/hypothek/"

# --- REGEX PATTERNS ---
# VIAC offers exactly 3 products (all rates in German, decimal may be . or ,)

# Geldmarkt-Hypothek (SARON-based): matches "Geldmarkt" then nearest percentage
REGEX_SARON = re.compile(
    r"Geldmarkt.{0,500}?(\d+[.,]\d+)\s*%",
    re.DOTALL | re.IGNORECASE,
)

# 5-year fixed: "5" near "Jahr/jährig" then nearest percentage
REGEX_FIXED_5 = re.compile(
    r"(?:5[- ]?j[äa]hrige?|5\s+Jahre?|Fest.{0,60}?\b5\b.{0,60}?[Jj]ahr).{0,300}?(\d+[.,]\d+)\s*%",
    re.DOTALL | re.IGNORECASE,
)

# 10-year fixed: "10" near "Jahr/jährig" then nearest percentage
REGEX_FIXED_10 = re.compile(
    r"(?:10[- ]?j[äa]hrige?|10\s+Jahre?|Fest.{0,60}?\b10\b.{0,60}?[Jj]ahr).{0,300}?(\d+[.,]\d+)\s*%",
    re.DOTALL | re.IGNORECASE,
)


def normalize_rate(raw: str) -> str:
    return raw.replace(",", ".")


def scrape_page_text() -> str:
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(URL, timeout=60000)
        page.wait_for_timeout(5000)
        text = page.inner_text("body")
        browser.close()
        return text


def extract_rates(text: str) -> list[dict]:
    results = []
    timestamp = datetime.utcnow().isoformat()

    m = REGEX_SARON.search(text)
    if m:
        results.append({
            "date": timestamp,
            "product": "SARON",
            "term": "SARON",
            "interestRate": normalize_rate(m.group(1)),
        })
    else:
        print("WARNING: SARON rate not found")

    m5 = REGEX_FIXED_5.search(text)
    if m5:
        results.append({
            "date": timestamp,
            "product": "Fixed",
            "term": "5 years",
            "interestRate": normalize_rate(m5.group(1)),
        })
    else:
        print("WARNING: 5-year fixed rate not found")

    m10 = REGEX_FIXED_10.search(text)
    if m10:
        results.append({
            "date": timestamp,
            "product": "Fixed",
            "term": "10 years",
            "interestRate": normalize_rate(m10.group(1)),
        })
    else:
        print("WARNING: 10-year fixed rate not found")

    return results


def write_csv(rows: list[dict]) -> None:
    os.makedirs("data", exist_ok=True)
    csv_path = "data/rates.csv"
    exists = os.path.exists(csv_path)

    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["date", "product", "term", "interestRate"])
        if not exists:
            w.writeheader()
        w.writerows(rows)


def main() -> None:
    print("Fetching VIAC mortgage page…")
    text = scrape_page_text()

    print("Extracting rates…")
    rows = extract_rates(text)

    for r in rows:
        print("✔", r)

    if not rows:
        print("ERROR: No rates extracted — check debug_scraper.py output to tune regexes.")
        raise SystemExit(1)

    write_csv(rows)
    print(f"Done. Extracted {len(rows)} rows.")


if __name__ == "__main__":
    main()
