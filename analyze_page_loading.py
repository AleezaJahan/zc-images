#!/usr/bin/env python3
"""
Script to analyze page loading behavior for Zero Collective products page.
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import time
import os

def main():
    url = "https://zerocollective.ca/collective?available=no&selectedBrands=&selectedColours=&selectedMaterials=&selectedMembership=&selectedOccasions=&selectedStyles=&selectedSize="
    
    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    
    print("Starting browser...")
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        print(f"\nNavigating to: {url}")
        driver.get(url)
        
        # Wait for page to load - wait for product cards
        print("\nWaiting for product cards to load...")
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.group-item"))
        )
        time.sleep(3)  # Additional wait for any dynamic content
        
        # Take initial screenshot
        screenshot_dir = "/Users/aleezajahan/zc-scrape/screenshots"
        os.makedirs(screenshot_dir, exist_ok=True)
        initial_screenshot = os.path.join(screenshot_dir, "initial_page.png")
        driver.save_screenshot(initial_screenshot)
        print(f"✓ Initial screenshot saved: {initial_screenshot}")
        
        # Count initial products
        products = driver.find_elements(By.CSS_SELECTOR, "div.group-item")
        initial_count = len(products)
        print(f"\n✓ Initial product count: {initial_count}")
        
        # Check for pagination or load more button
        load_more_button = None
        pagination = None
        
        try:
            # Common selectors for load more buttons
            load_more_selectors = [
                "button:contains('Load More')",
                "button:contains('Show More')",
                ".load-more",
                "#load-more",
                "button[class*='load']",
                "a:contains('Load More')"
            ]
            
            # Check for pagination
            pagination_selectors = [".pagination", "nav[aria-label='pagination']", ".page-numbers"]
            for selector in pagination_selectors:
                try:
                    pagination = driver.find_elements(By.CSS_SELECTOR, selector)
                    if pagination:
                        print(f"✓ Found pagination element: {selector}")
                        break
                except:
                    pass
            
        except Exception as e:
            print(f"Note: Error checking for buttons: {e}")
        
        # Scroll and count
        print("\nStarting scroll test...")
        scroll_iterations = 0
        previous_count = initial_count
        no_change_count = 0
        max_no_change = 3  # Stop after 3 scrolls with no new products
        
        while no_change_count < max_no_change:
            scroll_iterations += 1
            
            # Get current scroll position
            current_height = driver.execute_script("return document.body.scrollHeight")
            
            # Scroll down
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            print(f"\nScroll iteration {scroll_iterations}...")
            
            # Wait for potential lazy loading
            time.sleep(3)
            
            # Count products again
            products = driver.find_elements(By.CSS_SELECTOR, "div.group-item")
            current_count = len(products)
            
            print(f"  Product count: {current_count}")
            
            if current_count > previous_count:
                print(f"  ✓ New products loaded: +{current_count - previous_count}")
                previous_count = current_count
                no_change_count = 0
            else:
                no_change_count += 1
                print(f"  No new products (attempt {no_change_count}/{max_no_change})")
            
            # Check if we've reached the bottom
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == current_height and current_count == previous_count:
                print("  Reached bottom of page")
        
        # Take final screenshot
        final_screenshot = os.path.join(screenshot_dir, "final_page.png")
        driver.save_screenshot(final_screenshot)
        print(f"\n✓ Final screenshot saved: {final_screenshot}")
        
        # Final count
        final_products = driver.find_elements(By.CSS_SELECTOR, "div.group-item")
        final_count = len(final_products)
        
        # Determine loading mechanism
        loading_mechanism = "Unknown"
        if final_count > initial_count:
            loading_mechanism = "Infinite scroll (lazy loading)"
        elif pagination:
            loading_mechanism = "Pagination"
        elif load_more_button:
            loading_mechanism = "Load More button"
        else:
            loading_mechanism = "All products loaded initially (no lazy loading)"
        
        # Print summary
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        print(f"Initial product count: {initial_count}")
        print(f"Final product count: {final_count}")
        print(f"New products loaded: {final_count - initial_count}")
        print(f"Loading mechanism: {loading_mechanism}")
        print(f"Scroll iterations needed: {scroll_iterations}")
        print(f"Pagination detected: {'Yes' if pagination else 'No'}")
        print(f"Load More button detected: {'Yes' if load_more_button else 'No'}")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        print("\nClosing browser...")
        driver.quit()

if __name__ == "__main__":
    main()
