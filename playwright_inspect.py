"""
Script to inspect Zero Collective product page using Playwright
"""
import asyncio
import json
from playwright.async_api import async_playwright

async def inspect_page():
    async with async_playwright() as p:
        # Launch browser
        print("Launching browser...")
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={'width': 1920, 'height': 1080})
        
        # Navigate to the page
        url = "https://zerocollective.ca/collective"
        print(f"Navigating to {url}...")
        await page.goto(url, wait_until='networkidle', timeout=60000)
        
        # Wait a bit for any lazy loading
        print("Waiting for page to fully load...")
        await asyncio.sleep(3)
        
        # Scroll down to trigger lazy loading
        print("Scrolling to trigger lazy loading...")
        await page.evaluate("window.scrollTo(0, 800)")
        await asyncio.sleep(2)
        await page.evaluate("window.scrollTo(0, 1600)")
        await asyncio.sleep(2)
        await page.evaluate("window.scrollTo(0, 2400)")
        await asyncio.sleep(2)
        
        # Scroll back up to see the product grid
        await page.evaluate("window.scrollTo(0, 400)")
        await asyncio.sleep(1)
        
        # Take screenshot
        print("Taking screenshot...")
        await page.screenshot(path='product_grid_screenshot.png', full_page=False)
        print("✓ Screenshot saved: product_grid_screenshot.png")
        
        # Get page content
        content = await page.content()
        
        # Save HTML
        with open("page_source_playwright.html", "w", encoding="utf-8") as f:
            f.write(content)
        print("✓ HTML saved: page_source_playwright.html")
        
        # Find product cards using JavaScript
        print("\n" + "="*80)
        print("ANALYZING PAGE STRUCTURE")
        print("="*80)
        
        # Try to find product links
        product_links = await page.query_selector_all('a[href*="/products/"]')
        print(f"\n✓ Found {len(product_links)} product links")
        
        if not product_links:
            print("⚠ No product links found. Checking for other patterns...")
            
            # Try other patterns
            all_links = await page.query_selector_all('a')
            print(f"Total links on page: {len(all_links)}")
            
            # Check for grid containers
            grids = await page.query_selector_all('[class*="grid"], [class*="collection"], [class*="product"]')
            print(f"Elements with grid/collection/product in class: {len(grids)}")
            
            await browser.close()
            return
        
        # Get unique product URLs
        product_urls = []
        for link in product_links:
            href = await link.get_attribute('href')
            if href and href not in product_urls:
                product_urls.append(href)
        
        print(f"✓ Unique products: {len(product_urls)}")
        
        # Analyze first product card
        print("\n" + "="*80)
        print("DETAILED ANALYSIS OF FIRST PRODUCT CARD")
        print("="*80)
        
        first_link = product_links[0]
        
        # Get the outer HTML of the first product card
        # Try to find the card container by going up the DOM
        card_element = await page.evaluate('''(element) => {
            let current = element;
            for (let i = 0; i < 5; i++) {
                if (!current.parentElement) break;
                current = current.parentElement;
                const classes = current.className || '';
                if (classes.includes('product') || classes.includes('item') || classes.includes('card') || classes.includes('grid-item')) {
                    return {
                        tag: current.tagName.toLowerCase(),
                        classes: current.className,
                        id: current.id,
                        html: current.outerHTML
                    };
                }
            }
            return {
                tag: current.tagName.toLowerCase(),
                classes: current.className,
                id: current.id,
                html: current.outerHTML
            };
        }''', first_link)
        
        print(f"\nOUTER CONTAINER:")
        print(f"  Tag: <{card_element['tag']}>")
        print(f"  Classes: {card_element['classes']}")
        print(f"  ID: {card_element['id']}")
        
        # Save first card HTML
        with open("first_product_card.html", "w", encoding="utf-8") as f:
            f.write(card_element['html'])
        print("\n✓ First card HTML saved: first_product_card.html")
        
        # Print the HTML (truncated)
        print("\n" + "-"*80)
        print("FULL HTML OF FIRST PRODUCT CARD (truncated):")
        print("-"*80)
        html_preview = card_element['html'][:2000]
        print(html_preview)
        if len(card_element['html']) > 2000:
            print(f"\n... (truncated, total length: {len(card_element['html'])} chars)")
        
        # Extract details from first card
        card_details = await page.evaluate('''(element) => {
            // Find card container
            let card = element;
            for (let i = 0; i < 5; i++) {
                if (!card.parentElement) break;
                card = card.parentElement;
                const classes = card.className || '';
                if (classes.includes('product') || classes.includes('item') || classes.includes('card')) {
                    break;
                }
            }
            
            // Find product name
            const nameSelectors = ['h2', 'h3', 'h4', '.product-title', '.product-name', '[class*="title"]', '[class*="name"]'];
            let productName = null;
            let nameElement = null;
            for (const selector of nameSelectors) {
                const elem = card.querySelector(selector);
                if (elem && elem.textContent.trim()) {
                    productName = elem.textContent.trim();
                    nameElement = {
                        tag: elem.tagName.toLowerCase(),
                        classes: elem.className,
                        text: elem.textContent.trim()
                    };
                    break;
                }
            }
            
            // Find product URL
            const linkElem = card.querySelector('a[href*="/products/"]');
            const productUrl = linkElem ? linkElem.href : null;
            const linkClasses = linkElem ? linkElem.className : '';
            
            // Find product image
            const imgElem = card.querySelector('img');
            const imageInfo = imgElem ? {
                src: imgElem.src,
                dataSrc: imgElem.getAttribute('data-src'),
                srcset: imgElem.srcset,
                alt: imgElem.alt,
                classes: imgElem.className
            } : null;
            
            return {
                name: nameElement,
                url: { href: productUrl, classes: linkClasses },
                image: imageInfo,
                cardClasses: card.className,
                cardTag: card.tagName.toLowerCase()
            };
        }''', first_link)
        
        print("\n" + "-"*80)
        print("PRODUCT NAME ELEMENT:")
        print("-"*80)
        if card_details['name']:
            print(f"  Tag: <{card_details['name']['tag']}>")
            print(f"  Classes: {card_details['name']['classes']}")
            print(f"  Text: {card_details['name']['text']}")
        else:
            print("  ⚠ Could not find product name")
        
        print("\n" + "-"*80)
        print("PRODUCT URL:")
        print("-"*80)
        if card_details['url']['href']:
            print(f"  Tag: <a>")
            print(f"  href: {card_details['url']['href']}")
            print(f"  Classes: {card_details['url']['classes']}")
        else:
            print("  ⚠ Could not find product URL")
        
        print("\n" + "-"*80)
        print("PRODUCT IMAGE:")
        print("-"*80)
        if card_details['image']:
            print(f"  Tag: <img>")
            print(f"  src: {card_details['image']['src']}")
            print(f"  data-src: {card_details['image']['dataSrc']}")
            print(f"  srcset: {card_details['image']['srcset']}")
            print(f"  alt: {card_details['image']['alt']}")
            print(f"  Classes: {card_details['image']['classes']}")
        else:
            print("  ⚠ Could not find product image")
        
        # Check for pagination
        print("\n" + "="*80)
        print("PAGINATION / LOAD MORE CHECK")
        print("="*80)
        
        pagination_info = await page.evaluate('''() => {
            const keywords = ['load more', 'show more', 'next', 'pagination', 'view more'];
            const buttons = Array.from(document.querySelectorAll('button, a, div'));
            const matches = buttons.filter(btn => {
                const text = btn.textContent.toLowerCase();
                return keywords.some(keyword => text.includes(keyword));
            });
            
            const paginationElements = Array.from(document.querySelectorAll('[class*="pagination"]'));
            
            return {
                loadMoreButtons: matches.map(btn => ({
                    tag: btn.tagName.toLowerCase(),
                    classes: btn.className,
                    text: btn.textContent.trim().substring(0, 50)
                })),
                paginationElements: paginationElements.map(elem => ({
                    tag: elem.tagName.toLowerCase(),
                    classes: elem.className
                }))
            };
        }''')
        
        if pagination_info['loadMoreButtons']:
            print(f"✓ Found {len(pagination_info['loadMoreButtons'])} load more / pagination buttons:")
            for btn in pagination_info['loadMoreButtons'][:5]:
                print(f"  - <{btn['tag']}> class=\"{btn['classes']}\"")
                print(f"    Text: {btn['text']}")
        else:
            print("✗ No obvious 'load more' or pagination buttons found")
        
        if pagination_info['paginationElements']:
            print(f"\n✓ Found {len(pagination_info['paginationElements'])} elements with 'pagination' in class:")
            for elem in pagination_info['paginationElements'][:3]:
                print(f"  - <{elem['tag']}> class=\"{elem['classes']}\"")
        
        # Summary
        print("\n" + "="*80)
        print("SUMMARY & RECOMMENDED SELECTORS")
        print("="*80)
        print(f"Total product links found: {len(product_links)}")
        print(f"Unique products: {len(product_urls)}")
        
        print(f"\nCard container: <{card_details['cardTag']}> class=\"{card_details['cardClasses']}\"")
        
        # Generate CSS selectors
        card_classes = card_details['cardClasses'].split()
        if card_classes:
            card_selector = f"{card_details['cardTag']}.{'.'.join(card_classes)}"
            print(f"CSS Selector for card: {card_selector}")
        
        print(f"\nProduct URL selector: a[href*='/products/']")
        
        if card_details['name']:
            name_classes = card_details['name']['classes'].split() if card_details['name']['classes'] else []
            if name_classes:
                name_selector = f"{card_details['name']['tag']}.{'.'.join(name_classes)}"
                print(f"Product name selector: {name_selector}")
            else:
                print(f"Product name selector: {card_details['name']['tag']}")
        
        if card_details['image']:
            print(f"Product image selector: img")
        
        # Save report
        report = {
            "url": url,
            "total_product_links": len(product_links),
            "unique_products": len(product_urls),
            "product_urls": product_urls[:10],  # First 10 URLs
            "card_container": {
                "tag": card_details['cardTag'],
                "classes": card_details['cardClasses']
            },
            "selectors": {
                "card": f"{card_details['cardTag']}.{'.'.join(card_classes)}" if card_classes else card_details['cardTag'],
                "product_url": "a[href*='/products/']",
                "product_name": f"{card_details['name']['tag']}.{'.'.join(card_details['name']['classes'].split())}" if card_details['name'] and card_details['name']['classes'] else (card_details['name']['tag'] if card_details['name'] else None),
                "product_image": "img"
            },
            "pagination": {
                "has_load_more": len(pagination_info['loadMoreButtons']) > 0,
                "has_pagination": len(pagination_info['paginationElements']) > 0
            }
        }
        
        with open("inspection_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        print("\n✓ Report saved: inspection_report.json")
        print("✓ Screenshot saved: product_grid_screenshot.png")
        print("✓ Full HTML saved: page_source_playwright.html")
        print("✓ First card HTML saved: first_product_card.html")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(inspect_page())
