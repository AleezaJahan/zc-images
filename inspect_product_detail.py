"""
Inspect Zero Collective product detail page
Focus on expandable sections like SIZE and DESCRIPTION
"""
from playwright.sync_api import sync_playwright
import json
import time

def inspect_product_detail():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        # Navigate to a product detail page
        product_url = "https://zerocollective.ca/bag/dior-rattan-oblique-medium-lady-dior-bag"
        print(f"Navigating to: {product_url}")
        page.goto(product_url, wait_until='networkidle')
        
        # Wait for page to load
        time.sleep(3)
        
        # Take screenshot of initial state
        page.screenshot(path="product_detail_initial.png", full_page=True)
        print("✓ Screenshot saved: product_detail_initial.png")
        
        # Look for expandable sections
        print("\n" + "="*80)
        print("SEARCHING FOR EXPANDABLE SECTIONS")
        print("="*80)
        
        # Find all clickable elements that might be dropdowns
        # Common patterns: buttons, divs with click handlers, elements with "collapse", "expand", etc.
        
        # Try to find SIZE section
        print("\n1. Looking for SIZE section...")
        size_elements = page.locator('text=/SIZE/i').all()
        print(f"   Found {len(size_elements)} elements containing 'SIZE'")
        
        for i, elem in enumerate(size_elements[:3]):
            try:
                outer_html = elem.evaluate('el => el.outerHTML')
                print(f"\n   SIZE element {i+1}:")
                print(f"   {outer_html[:200]}")
            except:
                pass
        
        # Try to find DESCRIPTION section
        print("\n2. Looking for DESCRIPTION section...")
        desc_elements = page.locator('text=/DESCRIPTION/i').all()
        print(f"   Found {len(desc_elements)} elements containing 'DESCRIPTION'")
        
        for i, elem in enumerate(desc_elements[:3]):
            try:
                outer_html = elem.evaluate('el => el.outerHTML')
                print(f"\n   DESCRIPTION element {i+1}:")
                print(f"   {outer_html[:200]}")
            except:
                pass
        
        # Click on SIZE section if found
        print("\n" + "="*80)
        print("CLICKING SIZE SECTION")
        print("="*80)
        
        try:
            # Try different selectors for SIZE
            size_clicked = False
            
            # Try 1: Look for clickable element with SIZE text
            try:
                size_button = page.locator('text=/^SIZE$/i').first
                if size_button.is_visible():
                    print("Found SIZE button, clicking...")
                    size_button.click()
                    time.sleep(2)
                    page.screenshot(path="product_detail_size_expanded.png", full_page=True)
                    print("✓ Screenshot saved: product_detail_size_expanded.png")
                    size_clicked = True
            except Exception as e:
                print(f"   Method 1 failed: {e}")
            
            # Try 2: Look for parent div/button containing SIZE
            if not size_clicked:
                try:
                    size_section = page.locator('[class*="clickable"]:has-text("SIZE")').first
                    if size_section.is_visible():
                        print("Found SIZE section (method 2), clicking...")
                        size_section.click()
                        time.sleep(2)
                        page.screenshot(path="product_detail_size_expanded.png", full_page=True)
                        print("✓ Screenshot saved: product_detail_size_expanded.png")
                        size_clicked = True
                except Exception as e:
                    print(f"   Method 2 failed: {e}")
            
            if size_clicked:
                # Get the HTML of the expanded content
                print("\nExtracting SIZE section HTML...")
                size_html = page.content()
                
                # Save a snippet of the page source
                with open("product_detail_size_expanded.html", "w", encoding="utf-8") as f:
                    f.write(size_html)
                print("✓ Full HTML saved: product_detail_size_expanded.html")
        
        except Exception as e:
            print(f"✗ Could not click SIZE section: {e}")
        
        # Click on DESCRIPTION section
        print("\n" + "="*80)
        print("CLICKING DESCRIPTION SECTION")
        print("="*80)
        
        try:
            desc_clicked = False
            
            # Try 1: Look for clickable element with DESCRIPTION text
            try:
                desc_button = page.locator('text=/^DESCRIPTION$/i').first
                if desc_button.is_visible():
                    print("Found DESCRIPTION button, clicking...")
                    desc_button.click()
                    time.sleep(2)
                    page.screenshot(path="product_detail_description_expanded.png", full_page=True)
                    print("✓ Screenshot saved: product_detail_description_expanded.png")
                    desc_clicked = True
            except Exception as e:
                print(f"   Method 1 failed: {e}")
            
            # Try 2: Look for parent div/button containing DESCRIPTION
            if not desc_clicked:
                try:
                    desc_section = page.locator('[class*="clickable"]:has-text("DESCRIPTION")').first
                    if desc_section.is_visible():
                        print("Found DESCRIPTION section (method 2), clicking...")
                        desc_section.click()
                        time.sleep(2)
                        page.screenshot(path="product_detail_description_expanded.png", full_page=True)
                        print("✓ Screenshot saved: product_detail_description_expanded.png")
                        desc_clicked = True
                except Exception as e:
                    print(f"   Method 2 failed: {e}")
            
            if desc_clicked:
                # Get the HTML of the expanded content
                print("\nExtracting DESCRIPTION section HTML...")
                desc_html = page.content()
                
                # Save a snippet of the page source
                with open("product_detail_description_expanded.html", "w", encoding="utf-8") as f:
                    f.write(desc_html)
                print("✓ Full HTML saved: product_detail_description_expanded.html")
        
        except Exception as e:
            print(f"✗ Could not click DESCRIPTION section: {e}")
        
        # Get full page HTML
        print("\n" + "="*80)
        print("SAVING FULL PAGE SOURCE")
        print("="*80)
        
        full_html = page.content()
        with open("product_detail_full.html", "w", encoding="utf-8") as f:
            f.write(full_html)
        print("✓ Full page HTML saved: product_detail_full.html")
        
        # Analyze the structure
        print("\n" + "="*80)
        print("ANALYZING PAGE STRUCTURE")
        print("="*80)
        
        # Look for all clickable groups (potential expandable sections)
        clickable_groups = page.locator('[class*="clickable"][class*="Group"]').all()
        print(f"\nFound {len(clickable_groups)} clickable groups")
        
        for i, group in enumerate(clickable_groups[:10]):
            try:
                text = group.inner_text()[:50]
                classes = group.get_attribute('class')
                print(f"\n{i+1}. Clickable group:")
                print(f"   Text: {text}")
                print(f"   Classes: {classes[:100]}")
            except:
                pass
        
        # Keep browser open for manual inspection
        print("\n" + "="*80)
        print("Browser will stay open for 30 seconds for manual inspection...")
        print("="*80)
        time.sleep(30)
        
        browser.close()

if __name__ == "__main__":
    inspect_product_detail()
