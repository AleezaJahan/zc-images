"""
Final comprehensive analysis of Zero Collective product page
"""
from bs4 import BeautifulSoup
import json

# Read the HTML
with open("page_source_playwright.html", "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

print("="*80)
print("ZERO COLLECTIVE PRODUCT PAGE - COMPLETE ANALYSIS")
print("URL: https://zerocollective.ca/collective")
print("="*80)

# Find all product cards using the exact class structure
product_cards = soup.find_all('div', class_='bubble-element group-item bubble-r-container flex column')

print(f"\n✓ Found {len(product_cards)} product cards")

if not product_cards:
    print("⚠ No product cards found with exact class match")
    # Try partial match
    product_cards = soup.find_all('div', class_=lambda x: x and 'group-item' in x and 'entry-' in x)
    print(f"  Trying partial match: found {len(product_cards)} cards")

# Analyze first product card
if product_cards:
    first_card = product_cards[0]
    
    print("\n" + "="*80)
    print("FIRST PRODUCT CARD - DETAILED STRUCTURE")
    print("="*80)
    
    # Outer container
    print(f"\n1. OUTER CONTAINER (Product Card):")
    print(f"   Tag: <{first_card.name}>")
    classes = first_card.get('class', [])
    print(f"   Classes: {' '.join(classes)}")
    print(f"   CSS Selector: div.group-item")
    
    # Find all nested groups
    groups = first_card.find_all('div', class_=lambda x: x and 'Group' in ' '.join(x) if isinstance(x, list) else False, recursive=False)
    print(f"\n   Contains {len(groups)} direct child Group elements")
    
    # Product link
    link = first_card.find('a', href=True)
    if link:
        print(f"\n2. PRODUCT URL:")
        print(f"   Tag: <a>")
        print(f"   Classes: {' '.join(link.get('class', []))}")
        print(f"   href: {link['href']}")
        print(f"   CSS Selector: a[href*='/bag/']")
    
    # Product image
    img = first_card.find('img')
    if img:
        print(f"\n3. PRODUCT IMAGE:")
        print(f"   Tag: <img>")
        print(f"   src: {img.get('src', 'N/A')[:80]}...")
        print(f"   CSS Selector: img")
    
    # Product name and tier (in Text elements)
    text_elements = first_card.find_all('div', class_=lambda x: x and 'Text' in ' '.join(x) if isinstance(x, list) else False)
    
    if len(text_elements) >= 1:
        name_elem = text_elements[0]
        name_text = name_elem.get_text(strip=True)
        print(f"\n4. PRODUCT NAME:")
        print(f"   Tag: <div>")
        print(f"   Classes: {' '.join(name_elem.get('class', []))}")
        print(f"   Text: {name_text}")
        print(f"   CSS Selector: div.bubble-element.Text (first occurrence)")
    
    if len(text_elements) >= 2:
        tier_elem = text_elements[1]
        tier_text = tier_elem.get_text(strip=True)
        print(f"\n5. PRODUCT TIER/CATEGORY:")
        print(f"   Tag: <div>")
        print(f"   Classes: {' '.join(tier_elem.get('class', []))}")
        print(f"   Text: {tier_text}")
        print(f"   CSS Selector: div.bubble-element.Text (second occurrence)")
    
    # Save first card HTML
    print("\n" + "="*80)
    print("FIRST PRODUCT CARD - FULL HTML (first 2000 chars)")
    print("="*80)
    card_html = first_card.prettify()
    print(card_html[:2000])
    
    with open("first_product_card_final.html", "w", encoding="utf-8") as f:
        f.write(card_html)
    print(f"\n✓ Full card HTML saved to: first_product_card_final.html ({len(card_html)} chars)")

# Extract all products
print("\n" + "="*80)
print("ALL PRODUCTS FOUND")
print("="*80)

products = []
for i, card in enumerate(product_cards, 1):
    # Extract data
    link = card.find('a', href=True)
    img = card.find('img')
    text_elements = card.find_all('div', class_=lambda x: x and 'Text' in ' '.join(x) if isinstance(x, list) else False)
    
    product = {
        'index': i,
        'url': link['href'] if link else None,
        'name': text_elements[0].get_text(strip=True) if len(text_elements) >= 1 else None,
        'tier': text_elements[1].get_text(strip=True) if len(text_elements) >= 2 else None,
        'image_url': img.get('src') if img else None
    }
    products.append(product)
    
    print(f"\n{i}. {product['name']}")
    print(f"   Tier: {product['tier']}")
    print(f"   URL: {product['url']}")

# Pagination check
print("\n" + "="*80)
print("PAGINATION / LOAD MORE")
print("="*80)

# Check for load more buttons or pagination
load_more = soup.find_all(['button', 'a', 'div'], string=lambda x: x and any(
    keyword in str(x).lower() for keyword in ['load more', 'show more', 'next page']
))

if load_more:
    print(f"✓ Found {len(load_more)} potential load more elements")
    for elem in load_more[:3]:
        print(f"  - <{elem.name}> text: {elem.get_text(strip=True)[:50]}")
else:
    print("✗ No 'load more' or pagination found")
    print("  All products load on initial page load")

# Summary
print("\n" + "="*80)
print("SUMMARY & SCRAPING GUIDE")
print("="*80)

print(f"""
PRODUCTS FOUND: {len(products)}

KEY FINDINGS:
- Product cards use class: "bubble-element group-item bubble-r-container flex column entry-N"
- Product URLs use path: /bag/ (not /products/)
- No pagination - all products load initially
- Page uses Bubble.io framework (evident from class names)

RECOMMENDED SELECTORS FOR SCRAPING:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Product Card Container:
   CSS: div.group-item
   or:  div[class*="group-item"][class*="entry-"]
   
2. Product Name:
   CSS: div.bubble-element.Text (first within card)
   XPath: .//div[contains(@class, 'Text')][1]//div
   
3. Product URL:
   CSS: a[href*="/bag/"]
   XPath: .//a[contains(@href, '/bag/')]
   
4. Product Image:
   CSS: img
   XPath: .//img
   Attribute: src
   
5. Product Tier/Category:
   CSS: div.bubble-element.Text (second within card)
   XPath: .//div[contains(@class, 'Text')][2]//div

SCRAPING STRATEGY:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Use Selenium or Playwright (page requires JavaScript)
2. Navigate to: https://zerocollective.ca/collective
3. Wait for page load (wait for div.group-item to appear)
4. Optional: Scroll down to trigger any lazy loading
5. Select all: div.group-item elements
6. For each card, extract:
   - Name: First div.Text element's text
   - URL: a[href*="/bag/"] href attribute
   - Image: img src attribute
   - Tier: Second div.Text element's text

PAGINATION:
- Type: None (all products load at once)
- Total products on first load: {len(products)}

""")

# Save comprehensive report
report = {
    "url": "https://zerocollective.ca/collective",
    "analysis_date": "2026-03-10",
    "total_products": len(products),
    "products": products,
    "selectors": {
        "product_card": {
            "css": "div.group-item",
            "classes": "bubble-element group-item bubble-r-container flex column entry-N"
        },
        "product_name": {
            "css": "div.bubble-element.Text:first-of-type",
            "xpath": ".//div[contains(@class, 'Text')][1]//div"
        },
        "product_url": {
            "css": "a[href*='/bag/']",
            "xpath": ".//a[contains(@href, '/bag/')]",
            "attribute": "href"
        },
        "product_image": {
            "css": "img",
            "xpath": ".//img",
            "attribute": "src"
        },
        "product_tier": {
            "css": "div.bubble-element.Text:nth-of-type(2)",
            "xpath": ".//div[contains(@class, 'Text')][2]//div"
        }
    },
    "pagination": {
        "type": "none",
        "notes": "All products load on initial page load",
        "requires_javascript": True
    },
    "framework": "Bubble.io"
}

with open("final_scraping_report.json", "w") as f:
    json.dump(report, f, indent=2)

print("✓ Complete analysis saved to: final_scraping_report.json")
print("✓ Screenshot available at: product_grid_screenshot.png")
print("✓ First product card HTML: first_product_card_final.html")
