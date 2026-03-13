"""
Analyze the Zero Collective page structure from the saved HTML
"""
from bs4 import BeautifulSoup
import json

# Read the HTML file
with open("page_source_playwright.html", "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

print("="*80)
print("ZERO COLLECTIVE PRODUCT PAGE ANALYSIS")
print("="*80)

# Find all product links (they use /bag/ not /products/)
product_links = soup.find_all('a', href=lambda x: x and '/bag/' in x)
print(f"\n✓ Found {len(product_links)} product links (using /bag/ path)")

# Get unique URLs
unique_urls = list(set([link['href'] for link in product_links if link.get('href')]))
print(f"✓ Unique products: {len(unique_urls)}")

# Find the repeating group container
repeating_group = soup.find('div', class_=lambda x: x and 'RepeatingGroup' in ' '.join(x) if x else False)

group_items = []
if repeating_group:
    print(f"\n✓ Found RepeatingGroup container")
    print(f"  Classes: {' '.join(repeating_group.get('class', []))}")
    
    # Find all group items (product cards)
    group_items = repeating_group.find_all('div', class_=lambda x: x and 'group-item' in ' '.join(x) if x else False)
    print(f"  Contains {len(group_items)} group-item elements")
else:
    print("\n⚠ RepeatingGroup container not found, searching for group-items directly")
    group_items = soup.find_all('div', class_=lambda x: x and 'group-item' in ' '.join(x) if x else False)
    print(f"  Found {len(group_items)} group-item elements")

# Analyze first product card
if group_items:
    first_card = group_items[0]
    
    print("\n" + "="*80)
    print("FIRST PRODUCT CARD STRUCTURE")
    print("="*80)
    
    print(f"\nOuter Container:")
    print(f"  Tag: <{first_card.name}>")
    print(f"  Classes: {' '.join(first_card.get('class', []))}")
    
    # Find product name
    name_elem = first_card.find('div', class_=lambda x: x and 'Text' in ' '.join(x) if x else False)
    if name_elem:
        name_text = name_elem.get_text(strip=True)
        print(f"\nProduct Name:")
        print(f"  Tag: <{name_elem.name}>")
        print(f"  Classes: {' '.join(name_elem.get('class', []))}")
        print(f"  Text: {name_text}")
    
    # Find product URL
    link_elem = first_card.find('a', href=lambda x: x and '/bag/' in x)
    if link_elem:
        print(f"\nProduct URL:")
        print(f"  Tag: <{link_elem.name}>")
        print(f"  Classes: {' '.join(link_elem.get('class', []))}")
        print(f"  href: {link_elem['href']}")
    
    # Find product image
    img_elem = first_card.find('img')
    if img_elem:
        print(f"\nProduct Image:")
        print(f"  Tag: <{img_elem.name}>")
        print(f"  Classes: {' '.join(img_elem.get('class', []))}")
        print(f"  src: {img_elem.get('src', 'N/A')}")
        print(f"  alt: {img_elem.get('alt', 'N/A')}")
    
    # Find category/tier (DELUXE, CLASSIC, etc.)
    all_text_divs = first_card.find_all('div', class_=lambda x: x and 'Text' in ' '.join(x) if x else False)
    if len(all_text_divs) >= 2:
        tier_elem = all_text_divs[1]
        tier_text = tier_elem.get_text(strip=True)
        print(f"\nProduct Tier/Category:")
        print(f"  Tag: <{tier_elem.name}>")
        print(f"  Classes: {' '.join(tier_elem.get('class', []))}")
        print(f"  Text: {tier_text}")
    
    # Print full HTML of first card (formatted)
    print("\n" + "="*80)
    print("FULL HTML OF FIRST PRODUCT CARD")
    print("="*80)
    print(first_card.prettify()[:3000])
    
    # Save to file
    with open("first_product_card_analyzed.html", "w", encoding="utf-8") as f:
        f.write(first_card.prettify())
    print("\n✓ Full card HTML saved to: first_product_card_analyzed.html")

# Check for pagination
print("\n" + "="*80)
print("PAGINATION CHECK")
print("="*80)

# The page uses a RepeatingGroup which likely loads all items at once
# or uses infinite scroll
pagination_keywords = ['load', 'more', 'next', 'prev', 'pagination']
potential_pagination = []

for keyword in pagination_keywords:
    elements = soup.find_all(text=lambda x: x and keyword.lower() in str(x).lower())
    if elements:
        potential_pagination.extend(elements)

if potential_pagination:
    print(f"✓ Found {len(potential_pagination)} elements with pagination keywords")
else:
    print("✗ No pagination elements found")
    print("  The page likely loads all products at once or uses infinite scroll")

# Summary and recommendations
print("\n" + "="*80)
print("SCRAPING RECOMMENDATIONS")
print("="*80)

print(f"""
Total Products Visible: {len(group_items)}
Unique Product URLs: {len(unique_urls)}

RECOMMENDED SELECTORS:
1. Product Card Container:
   - CSS: div.group-item.bubble-r-container
   - Class contains: "group-item", "bubble-r-container", "entry-N"

2. Product Name:
   - CSS: div.bubble-element.Text (first Text element in card)
   - Look for div with class containing "Text" and "bubble-element"

3. Product URL:
   - CSS: a[href*="/bag/"]
   - All product links use the /bag/ path

4. Product Image:
   - CSS: img (within the card)
   - Images are within div.bubble-element.Image

5. Product Tier/Category:
   - CSS: div.bubble-element.Text (second Text element in card)
   - Contains values like "DELUXE", "CLASSIC"

PAGINATION:
- No obvious pagination found
- All products appear to load on initial page load
- Total visible: {len(group_items)} products

SCRAPING STRATEGY:
1. Load the page with JavaScript execution (use Selenium/Playwright)
2. Wait for RepeatingGroup to populate (wait for div.RepeatingGroup)
3. Optionally scroll to trigger any lazy loading
4. Select all div.group-item elements
5. For each card, extract:
   - Product name from first Text div
   - Product URL from a[href*="/bag/"]
   - Product image from img tag
   - Product tier from second Text div
""")

# Save sample URLs
print("\nSample Product URLs:")
for i, url in enumerate(unique_urls[:5], 1):
    print(f"  {i}. {url}")

# Create JSON report
report = {
    "url": "https://zerocollective.ca/collective",
    "analysis_date": "2026-03-10",
    "total_products": len(group_items),
    "unique_urls": len(unique_urls),
    "selectors": {
        "product_card": "div.group-item.bubble-r-container",
        "product_name": "div.bubble-element.Text (first occurrence)",
        "product_url": "a[href*='/bag/']",
        "product_image": "img",
        "product_tier": "div.bubble-element.Text (second occurrence)"
    },
    "pagination": {
        "type": "none_or_infinite_scroll",
        "notes": "All products load on initial page load"
    },
    "sample_urls": unique_urls[:10]
}

with open("scraping_analysis.json", "w") as f:
    json.dump(report, f, indent=2)

print("\n✓ Analysis complete!")
print("✓ Report saved to: scraping_analysis.json")
