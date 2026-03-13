"""
Simple script to inspect Zero Collective product page structure using requests
"""
import requests
from bs4 import BeautifulSoup
import json

def inspect_page():
    url = "https://zerocollective.ca/collective"
    
    print(f"Fetching: {url}")
    print("="*80)
    
    # Add headers to mimic a browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    response = requests.get(url, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Content Length: {len(response.content)} bytes\n")
    
    if response.status_code != 200:
        print(f"Error: Failed to fetch page (status {response.status_code})")
        return
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Save the full HTML for reference
    with open("page_source.html", "w", encoding="utf-8") as f:
        f.write(soup.prettify())
    print("✓ Full HTML saved to: page_source.html\n")
    
    # ANALYSIS
    print("="*80)
    print("SEARCHING FOR PRODUCT CARDS")
    print("="*80)
    
    # Try multiple strategies to find product cards
    strategies = [
        ("Links with /products/", lambda: soup.find_all('a', href=lambda x: x and '/products/' in x)),
        ("Links with /collections/", lambda: soup.find_all('a', href=lambda x: x and '/collections/' in x)),
        ("Article tags", lambda: soup.find_all('article')),
        ("Divs with 'product' in class", lambda: soup.find_all('div', class_=lambda x: x and 'product' in ' '.join(x).lower())),
        ("Divs with 'item' in class", lambda: soup.find_all('div', class_=lambda x: x and 'item' in ' '.join(x).lower())),
        ("Divs with 'card' in class", lambda: soup.find_all('div', class_=lambda x: x and 'card' in ' '.join(x).lower())),
    ]
    
    results = {}
    for name, func in strategies:
        elements = func()
        count = len(elements)
        results[name] = count
        print(f"{name}: {count} found")
    
    # Find product links
    product_links = soup.find_all('a', href=lambda x: x and '/products/' in x)
    
    if not product_links:
        print("\n⚠ No product links found with /products/ in href")
        print("The page might be using JavaScript to load products dynamically.")
        print("\nLet me check for common grid containers...")
        
        # Look for grid containers
        grids = soup.find_all(['div', 'section', 'ul'], class_=lambda x: x and any(
            term in ' '.join(x).lower() for term in ['grid', 'collection', 'products']
        ))
        
        print(f"\nFound {len(grids)} potential grid containers:")
        for i, grid in enumerate(grids[:5], 1):
            classes = ' '.join(grid.get('class', []))
            print(f"{i}. <{grid.name}> class=\"{classes}\"")
            print(f"   Children: {len(list(grid.children))} elements")
        
        return
    
    print(f"\n✓ Found {len(product_links)} product links")
    
    # Get unique product URLs
    unique_products = set()
    for link in product_links:
        href = link.get('href', '')
        if '/products/' in href:
            unique_products.add(href)
    
    print(f"✓ Unique products: {len(unique_products)}")
    
    # Analyze first product card
    print("\n" + "="*80)
    print("DETAILED ANALYSIS OF FIRST PRODUCT CARD")
    print("="*80)
    
    first_link = product_links[0]
    
    # Find the product card container (go up the tree)
    card = first_link
    for level in range(5):  # Try up to 5 levels up
        parent = card.parent
        if parent and parent.name in ['div', 'article', 'li']:
            # Check if this looks like a card container
            classes = parent.get('class', [])
            if any(term in ' '.join(classes).lower() for term in ['product', 'item', 'card', 'grid-item']):
                card = parent
                break
            card = parent
        elif parent:
            card = parent
    
    print(f"\nOUTER CONTAINER:")
    print(f"  Tag: <{card.name}>")
    print(f"  Classes: {card.get('class', [])}")
    print(f"  ID: {card.get('id', 'none')}")
    
    # Full HTML of first card
    print("\n" + "-"*80)
    print("FULL HTML OF FIRST PRODUCT CARD:")
    print("-"*80)
    card_html = card.prettify()
    print(card_html)
    
    # Save first card HTML
    with open("first_product_card.html", "w", encoding="utf-8") as f:
        f.write(card_html)
    print("\n✓ First card HTML saved to: first_product_card.html")
    
    # Find product name
    print("\n" + "-"*80)
    print("PRODUCT NAME ELEMENT:")
    print("-"*80)
    
    name_candidates = []
    for tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'span', 'div', 'a']:
        elements = card.find_all(tag)
        for elem in elements:
            text = elem.get_text(strip=True)
            if text and len(text) > 3 and len(text) < 100:  # Reasonable name length
                classes = ' '.join(elem.get('class', []))
                name_candidates.append({
                    'tag': tag,
                    'text': text,
                    'classes': classes
                })
    
    # Show top candidates
    for i, candidate in enumerate(name_candidates[:5], 1):
        print(f"{i}. <{candidate['tag']}> class=\"{candidate['classes']}\"")
        print(f"   Text: {candidate['text']}")
    
    # Find product URL
    print("\n" + "-"*80)
    print("PRODUCT URL:")
    print("-"*80)
    
    product_link_elem = card.find('a', href=lambda x: x and '/products/' in x)
    if product_link_elem:
        print(f"  Tag: <a>")
        print(f"  href: {product_link_elem.get('href', '')}")
        print(f"  Classes: {product_link_elem.get('class', [])}")
    else:
        print("  ⚠ No product link found in card")
    
    # Find product image
    print("\n" + "-"*80)
    print("PRODUCT IMAGE:")
    print("-"*80)
    
    img = card.find('img')
    if img:
        print(f"  Tag: <img>")
        print(f"  src: {img.get('src', 'none')}")
        print(f"  data-src: {img.get('data-src', 'none')}")
        print(f"  data-srcset: {img.get('data-srcset', 'none')}")
        print(f"  srcset: {img.get('srcset', 'none')}")
        print(f"  alt: {img.get('alt', 'none')}")
        print(f"  Classes: {img.get('class', [])}")
    else:
        print("  ⚠ No image found in card")
    
    # Check for pagination
    print("\n" + "="*80)
    print("PAGINATION / LOAD MORE CHECK")
    print("="*80)
    
    # Look for pagination elements
    pagination_keywords = ['load more', 'show more', 'next', 'pagination', 'page', 'load-more', 'view more']
    
    buttons = soup.find_all(['button', 'a', 'div'], text=lambda x: x and any(
        keyword in str(x).lower() for keyword in pagination_keywords
    ))
    
    if buttons:
        print(f"✓ Found {len(buttons)} potential pagination elements:")
        for btn in buttons[:5]:
            print(f"  - <{btn.name}> class=\"{' '.join(btn.get('class', []))}\"")
            print(f"    Text: {btn.get_text(strip=True)}")
    else:
        print("✗ No obvious pagination or 'load more' buttons found")
    
    # Check for pagination by class
    pagination_by_class = soup.find_all(class_=lambda x: x and 'pagination' in ' '.join(x).lower())
    if pagination_by_class:
        print(f"\n✓ Found {len(pagination_by_class)} elements with 'pagination' in class:")
        for elem in pagination_by_class[:3]:
            print(f"  - <{elem.name}> class=\"{' '.join(elem.get('class', []))}\"")
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total product links found: {len(product_links)}")
    print(f"Unique products: {len(unique_products)}")
    
    # Generate selector recommendations
    print("\n" + "="*80)
    print("RECOMMENDED SELECTORS")
    print("="*80)
    
    card_classes = ' '.join(card.get('class', []))
    print(f"Card container: <{card.name}> with class=\"{card_classes}\"")
    
    if card_classes:
        # Create CSS selector
        selector = f"{card.name}.{'.'.join(card.get('class', []))}"
        print(f"CSS Selector: {selector}")
    
    if product_link_elem:
        print(f"\nProduct URL: a[href*='/products/']")
    
    if img:
        img_classes = ' '.join(img.get('class', []))
        print(f"Product Image: img (classes: {img_classes})")
    
    # Save report
    report = {
        "url": url,
        "status_code": response.status_code,
        "total_product_links": len(product_links),
        "unique_products": len(unique_products),
        "card_container": {
            "tag": card.name,
            "classes": card.get('class', []),
            "id": card.get('id', '')
        },
        "selectors": {
            "card": f"{card.name}.{'.'.join(card.get('class', []))}" if card.get('class') else card.name,
            "product_url": "a[href*='/products/']",
            "product_image": "img"
        }
    }
    
    with open("inspection_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print("\n✓ Report saved to: inspection_report.json")
    print("✓ Full page HTML saved to: page_source.html")
    print("✓ First product card HTML saved to: first_product_card.html")

if __name__ == "__main__":
    inspect_page()
