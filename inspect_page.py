"""
Script to inspect Zero Collective product page structure
"""
import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

def inspect_zero_collective():
    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # Run in background
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    
    # Initialize driver
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        print("Navigating to https://zerocollective.ca/collective...")
        driver.get("https://zerocollective.ca/collective")
        
        # Wait for page to load
        time.sleep(3)
        
        # Scroll down to trigger lazy loading
        print("Scrolling to trigger lazy loading...")
        driver.execute_script("window.scrollTo(0, 800);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, 1600);")
        time.sleep(2)
        
        # Scroll back to top to see the grid
        driver.execute_script("window.scrollTo(0, 400);")
        time.sleep(1)
        
        # Take screenshot
        print("Taking screenshot...")
        driver.save_screenshot("product_grid_screenshot.png")
        print("Screenshot saved as: product_grid_screenshot.png")
        
        # Get page source
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Try to find product cards using common selectors
        print("\n" + "="*80)
        print("ANALYZING PAGE STRUCTURE")
        print("="*80)
        
        # Look for common product card patterns
        possible_selectors = [
            ('div.product-card', 'Product card class'),
            ('div.product-item', 'Product item class'),
            ('div[class*="product"]', 'Div with product in class'),
            ('article', 'Article tags'),
            ('a[href*="/products/"]', 'Links to products'),
            ('div.grid > div', 'Grid children'),
            ('div.collection-item', 'Collection item'),
        ]
        
        product_elements = []
        for selector, description in possible_selectors:
            elements = soup.select(selector)
            if elements:
                print(f"\n✓ Found {len(elements)} elements with: {description} ({selector})")
                if not product_elements:
                    product_elements = elements
        
        # Try to find the main product container
        print("\n" + "-"*80)
        print("SEARCHING FOR PRODUCT GRID CONTAINER")
        print("-"*80)
        
        grid_containers = soup.find_all(['div', 'section', 'ul'], class_=lambda x: x and any(
            term in str(x).lower() for term in ['grid', 'collection', 'product', 'list']
        ))
        
        for container in grid_containers[:5]:  # Show first 5
            classes = container.get('class', [])
            print(f"Container: <{container.name}> class='{' '.join(classes) if classes else 'none'}'")
        
        # Find all links that might be products
        product_links = soup.find_all('a', href=lambda x: x and '/products/' in x)
        print(f"\n✓ Found {len(product_links)} links containing '/products/'")
        
        # Analyze first product card in detail
        if product_links:
            print("\n" + "="*80)
            print("DETAILED ANALYSIS OF FIRST PRODUCT CARD")
            print("="*80)
            
            first_product = product_links[0]
            
            # Get the parent container (likely the product card)
            card = first_product
            for _ in range(3):  # Go up 3 levels to find the card container
                parent = card.parent
                if parent:
                    card = parent
            
            print("\nOUTER CONTAINER:")
            print(f"Tag: <{card.name}>")
            print(f"Classes: {card.get('class', [])}")
            print(f"ID: {card.get('id', 'none')}")
            
            # Extract the full HTML of the first product card
            print("\n" + "-"*80)
            print("FULL HTML OF FIRST PRODUCT CARD:")
            print("-"*80)
            card_html = card.prettify()
            print(card_html[:2000])  # Print first 2000 chars
            if len(card_html) > 2000:
                print(f"\n... (truncated, total length: {len(card_html)} chars)")
            
            # Find product name
            print("\n" + "-"*80)
            print("PRODUCT NAME ELEMENT:")
            print("-"*80)
            possible_name_tags = ['h2', 'h3', 'h4', 'p', 'span', 'div']
            for tag in possible_name_tags:
                name_elem = card.find(tag, class_=lambda x: x and any(
                    term in str(x).lower() for term in ['title', 'name', 'product']
                ))
                if name_elem:
                    print(f"Found in <{tag}> class='{name_elem.get('class', [])}'")
                    print(f"Text: {name_elem.get_text(strip=True)}")
                    break
            
            # Find product URL
            print("\n" + "-"*80)
            print("PRODUCT URL:")
            print("-"*80)
            product_link = card.find('a', href=True)
            if product_link:
                print(f"Tag: <a>")
                print(f"href: {product_link['href']}")
                print(f"Classes: {product_link.get('class', [])}")
            
            # Find product image
            print("\n" + "-"*80)
            print("PRODUCT IMAGE:")
            print("-"*80)
            img = card.find('img')
            if img:
                print(f"Tag: <img>")
                print(f"src: {img.get('src', 'none')}")
                print(f"data-src: {img.get('data-src', 'none')}")
                print(f"srcset: {img.get('srcset', 'none')}")
                print(f"alt: {img.get('alt', 'none')}")
                print(f"Classes: {img.get('class', [])}")
        
        # Check for pagination or load more
        print("\n" + "="*80)
        print("PAGINATION / LOAD MORE CHECK")
        print("="*80)
        
        load_more = soup.find_all(['button', 'a'], text=lambda x: x and any(
            term in str(x).lower() for term in ['load more', 'show more', 'next', 'pagination']
        ))
        
        if load_more:
            print(f"✓ Found {len(load_more)} load more / pagination elements:")
            for elem in load_more:
                print(f"  - <{elem.name}> class='{elem.get('class', [])}' text='{elem.get_text(strip=True)}'")
        else:
            print("✗ No obvious 'load more' or pagination buttons found")
        
        # Check for pagination classes
        pagination_divs = soup.find_all(['div', 'nav'], class_=lambda x: x and 'pagination' in str(x).lower())
        if pagination_divs:
            print(f"✓ Found {len(pagination_divs)} elements with 'pagination' in class")
        
        # Count visible products
        print("\n" + "="*80)
        print("PRODUCT COUNT")
        print("="*80)
        print(f"Total product links found: {len(product_links)}")
        
        # Save detailed report
        report = {
            "url": "https://zerocollective.ca/collective",
            "total_product_links": len(product_links),
            "screenshot": "product_grid_screenshot.png",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        with open("inspection_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        print("\n✓ Inspection complete!")
        print("✓ Screenshot saved: product_grid_screenshot.png")
        print("✓ Report saved: inspection_report.json")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        driver.quit()

if __name__ == "__main__":
    inspect_zero_collective()
