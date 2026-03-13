"""
Zero Collective bag scraper — Step 1 of pipeline.

Visits the "All Bags" listing, collects every product card,
then visits each product page to pull SIZE + DESCRIPTION details.
Saves results to zero_collective_products.csv.
"""

import csv
import os
from playwright.sync_api import sync_playwright, TimeoutError as PwTimeout

LISTING_URL = (
    "https://zerocollective.ca/collective"
    "?available=no"
    "&selectedBrands=&selectedColours=&selectedMaterials="
    "&selectedMembership=&selectedOccasions=&selectedStyles=&selectedSize="
)
OUTPUT_CSV = "zero_collective_products.csv"

CSV_FIELDS = [
    "name",
    "tier",
    "url",
    "image_url",
    "dimensions",
    "handle_drop",
    "ideal_for",
    "colour",
    "made_of",
    "features",
    "design_notes",
]


# ── helpers ──────────────────────────────────────────────────────────────────


def parse_field(text: str) -> str:
    """Strip the label prefix from a field like 'DIMENSIONS – MEDIUM (9.5"…)'."""
    for sep in ["–", "-"]:
        if sep in text:
            return text.split(sep, 1)[1].strip()
    return text.strip()


def scroll_until_stable(
    page, selector: str, *, pause_ms: int = 2500, max_rounds: int = 60
):
    """Scroll until the number of matching elements stops increasing."""
    prev_count = page.evaluate(f"document.querySelectorAll('{selector}').length")
    print(f"  ... starting with {prev_count} cards")
    stale_rounds = 0
    for _ in range(max_rounds):
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(pause_ms)
        count = page.evaluate(f"document.querySelectorAll('{selector}').length")
        if count == prev_count:
            stale_rounds += 1
            if stale_rounds >= 3:
                break
        else:
            stale_rounds = 0
            print(f"  ... {count} cards loaded so far")
        prev_count = count
    return count


def scrape_listing(page) -> list[dict]:
    """Return de-duplicated product stubs from the listing page."""
    page.goto(LISTING_URL, wait_until="networkidle")
    page.wait_for_selector("div.group-item", timeout=15_000)

    # Infinite-scroll: keep scrolling until no new cards appear
    total = scroll_until_stable(page, "div.group-item")
    print(f"  ... scrolling complete, {total} cards in DOM")

    cards = page.query_selector_all("div.group-item")
    seen_urls: set[str] = set()
    products: list[dict] = []

    for card in cards:
        link_el = card.query_selector('a[href*="/bag/"]')
        if not link_el:
            continue
        url = link_el.get_attribute("href") or ""
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)

        # Product name is the first .Text inside the card
        name_el = card.query_selector("div.bubble-element.Text div")
        name = (name_el.inner_text() if name_el else "").strip()

        # Tier (DELUXE / CLASSIC) is the second .Text
        text_els = card.query_selector_all("div.bubble-element.Text div")
        tier = text_els[1].inner_text().strip() if len(text_els) > 1 else ""

        # First image shown on the card
        img_el = card.query_selector("img")
        image_url = (img_el.get_attribute("src") if img_el else "") or ""

        products.append({
            "name": name,
            "tier": tier,
            "url": url,
            "image_url": image_url,
        })

    print(f"  ... {len(products)} unique bag URLs after dedupe")
    return products


def expand_and_read(page, section_label: str) -> dict[str, str]:
    """Click a dropdown header (e.g. 'SIZE') and return its fields as a dict."""
    fields: dict[str, str] = {}

    # The clickable header contains a <strong> with the section name
    header = page.locator(
        f"div.clickable-element:has(strong:text-is('{section_label}'))"
    ).first

    try:
        header.click(timeout=4000)
        page.wait_for_timeout(600)
    except PwTimeout:
        return fields

    # The sibling container holds the field text elements.
    # Walk up to the parent group, then grab the content container.
    parent = header.locator("xpath=..")
    content_texts = parent.locator("div.bubble-element.Text div").all()

    for el in content_texts:
        raw = el.inner_text().strip()
        if not raw:
            continue
        upper = raw.upper()
        if "DIMENSIONS" in upper:
            fields["dimensions"] = parse_field(raw)
        elif "HANDLE DROP" in upper:
            fields["handle_drop"] = parse_field(raw)
        elif "IDEAL FOR" in upper:
            fields["ideal_for"] = parse_field(raw)
        elif "COLOUR" in upper or "COLOR" in upper:
            fields["colour"] = parse_field(raw)
        elif "MADE OF" in upper:
            fields["made_of"] = parse_field(raw)
        elif "DESIGN NOTES" in upper:
            fields["design_notes"] = parse_field(raw)
        elif "FEATURES" in upper:
            fields["features"] = parse_field(raw)

    return fields


def scrape_detail(page, product: dict) -> dict:
    """Visit a product page and enrich the product dict with detail fields."""
    url = product["url"]
    try:
        page.goto(url, wait_until="networkidle", timeout=20_000)
        page.wait_for_timeout(1000)
    except PwTimeout:
        print(f"  ⏳ Timeout loading {url}, skipping details")
        return product

    size_fields = expand_and_read(page, "SIZE")
    desc_fields = expand_and_read(page, "DESCRIPTION")

    for key in ("dimensions", "handle_drop", "ideal_for"):
        product[key] = size_fields.get(key, "")
    for key in ("colour", "made_of", "features", "design_notes"):
        product[key] = desc_fields.get(key, "")

    return product


# ── main ─────────────────────────────────────────────────────────────────────


def main():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        )
        page = context.new_page()

        # Step 1 — collect product stubs from the listing page
        print("Scraping listing page …")
        products = scrape_listing(page)
        print(f"Found {len(products)} unique products on listing page.\n")

        # Step 2 — write rows as each product finishes so partial progress is saved
        with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            writer.writeheader()
            f.flush()
            os.fsync(f.fileno())

            for i, product in enumerate(products, 1):
                print(f"[{i}/{len(products)}] {product['name']}")
                scrape_detail(page, product)
                writer.writerow({k: product.get(k, "") for k in CSV_FIELDS})
                f.flush()
                os.fsync(f.fileno())

        browser.close()

    print(f"\n✅ Saved {len(products)} products to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
