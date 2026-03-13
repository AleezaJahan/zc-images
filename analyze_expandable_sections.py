"""
Analyze the expandable sections (SIZE, DESCRIPTION) on product detail page
"""
from bs4 import BeautifulSoup
import json

print("="*80)
print("ANALYZING EXPANDABLE SECTIONS - PRODUCT DETAIL PAGE")
print("="*80)

# Read the HTML files
with open("product_detail_size_expanded.html", "r", encoding="utf-8") as f:
    size_html = f.read()

with open("product_detail_description_expanded.html", "r", encoding="utf-8") as f:
    desc_html = f.read()

size_soup = BeautifulSoup(size_html, 'html.parser')
desc_soup = BeautifulSoup(desc_html, 'html.parser')

# Analyze SIZE section
print("\n" + "="*80)
print("1. SIZE SECTION STRUCTURE")
print("="*80)

# Find the SIZE clickable trigger
size_triggers = size_soup.find_all('strong', string='SIZE')
if size_triggers:
    size_trigger = size_triggers[0]
    
    # Get the parent clickable element
    parent = size_trigger.find_parent('div', class_=lambda x: x and 'clickable-element' in x)
    if parent:
        print("\nTRIGGER ELEMENT (what you click to expand):")
        print(f"  Tag: <{parent.name}>")
        print(f"  Classes: {' '.join(parent.get('class', []))}")
        print(f"  Text content: {parent.get_text(strip=True)}")
        
        # Find the expanded content
        # Look for siblings or nearby elements that contain size info
        print("\nLooking for expanded content container...")
        
        # Get the parent's parent to see the full structure
        grandparent = parent.find_parent('div')
        if grandparent:
            print(f"\nGrandparent container classes: {' '.join(grandparent.get('class', []))}")
            
            # Look for the content that appears after clicking
            # Usually it's a sibling or child element
            siblings = grandparent.find_next_siblings()
            print(f"\nFound {len(siblings)} siblings after the trigger")
            
            for i, sib in enumerate(siblings[:3]):
                classes = ' '.join(sib.get('class', []))
                text = sib.get_text(strip=True)[:100]
                print(f"\n  Sibling {i+1}:")
                print(f"    Classes: {classes}")
                print(f"    Text: {text}")
        
        # Try to find size-related content
        print("\n" + "-"*80)
        print("SEARCHING FOR SIZE CONTENT...")
        print("-"*80)
        
        # Look for text elements containing size information
        size_keywords = ['Width', 'Height', 'Depth', 'Length', 'cm', 'inches']
        for keyword in size_keywords:
            elements = size_soup.find_all(string=lambda x: x and keyword in str(x))
            if elements:
                print(f"\nFound '{keyword}' in {len(elements)} elements:")
                for elem in elements[:2]:
                    parent_elem = elem.find_parent()
                    if parent_elem:
                        print(f"  Text: {elem.strip()}")
                        print(f"  Parent tag: <{parent_elem.name}>")
                        print(f"  Parent classes: {' '.join(parent_elem.get('class', []))}")

# Analyze DESCRIPTION section
print("\n" + "="*80)
print("2. DESCRIPTION SECTION STRUCTURE")
print("="*80)

desc_triggers = desc_soup.find_all('strong', string='DESCRIPTION')
if desc_triggers:
    desc_trigger = desc_triggers[0]
    
    # Get the parent clickable element
    parent = desc_trigger.find_parent('div', class_=lambda x: x and 'clickable-element' in x)
    if parent:
        print("\nTRIGGER ELEMENT (what you click to expand):")
        print(f"  Tag: <{parent.name}>")
        print(f"  Classes: {' '.join(parent.get('class', []))}")
        print(f"  Text content: {parent.get_text(strip=True)}")
        
        # Find the expanded content
        print("\nLooking for expanded content container...")
        
        # Get the parent's parent to see the full structure
        grandparent = parent.find_parent('div')
        if grandparent:
            print(f"\nGrandparent container classes: {' '.join(grandparent.get('class', []))}")
            
            # Look for the content that appears after clicking
            siblings = grandparent.find_next_siblings()
            print(f"\nFound {len(siblings)} siblings after the trigger")
            
            for i, sib in enumerate(siblings[:3]):
                classes = ' '.join(sib.get('class', []))
                text = sib.get_text(strip=True)[:200]
                print(f"\n  Sibling {i+1}:")
                print(f"    Classes: {classes}")
                print(f"    Text preview: {text}")
        
        # Try to find description-related content
        print("\n" + "-"*80)
        print("SEARCHING FOR DESCRIPTION CONTENT...")
        print("-"*80)
        
        # Look for common description fields
        desc_keywords = ['COLOUR', 'MADE OF', 'FEATURES', 'DESIGN NOTES', 'Material', 'Hardware']
        for keyword in desc_keywords:
            elements = desc_soup.find_all(string=lambda x: x and keyword in str(x))
            if elements:
                print(f"\nFound '{keyword}' in {len(elements)} elements:")
                for elem in elements[:2]:
                    parent_elem = elem.find_parent()
                    if parent_elem:
                        print(f"  Text: {elem.strip()[:100]}")
                        print(f"  Parent tag: <{parent_elem.name}>")
                        print(f"  Parent classes: {' '.join(parent_elem.get('class', []))}")

# Find all Text elements in the page to understand structure
print("\n" + "="*80)
print("3. ALL TEXT ELEMENTS STRUCTURE")
print("="*80)

# Look at the description page for all Text bubble elements
text_elements = desc_soup.find_all('div', class_=lambda x: x and 'bubble-element' in x and 'Text' in x)
print(f"\nFound {len(text_elements)} Text elements on the page")

# Group them by their text content to find patterns
interesting_texts = []
for elem in text_elements:
    text = elem.get_text(strip=True)
    if text and len(text) > 0 and len(text) < 200:
        interesting_texts.append({
            'text': text,
            'classes': ' '.join(elem.get('class', []))
        })

# Print unique interesting texts
print("\nSample text elements (first 30):")
for i, item in enumerate(interesting_texts[:30]):
    print(f"\n{i+1}. Text: {item['text'][:80]}")
    print(f"   Classes: {item['classes'][:100]}")

# Save detailed analysis
print("\n" + "="*80)
print("4. EXTRACTING FULL EXPANDABLE SECTION HTML")
print("="*80)

# Find the SIZE section in detail
size_section = size_soup.find('div', class_=lambda x: x and 'clickable-element' in x, string=lambda x: x and 'SIZE' in str(x))
if not size_section:
    # Try finding by strong tag
    size_strong = size_soup.find('strong', string='SIZE')
    if size_strong:
        size_section = size_strong.find_parent('div', class_=lambda x: x and 'clickable-element' in x)

if size_section:
    # Get the container that holds both trigger and content
    container = size_section.find_parent('div', class_=lambda x: x and 'Group' in x)
    if container:
        print("\nSIZE SECTION FULL HTML:")
        print("-"*80)
        size_html_snippet = container.prettify()[:2000]
        print(size_html_snippet)
        
        with open("size_section_detail.html", "w", encoding="utf-8") as f:
            f.write(container.prettify())
        print("\n✓ Full SIZE section HTML saved to: size_section_detail.html")

# Find the DESCRIPTION section in detail
desc_section = desc_soup.find('div', class_=lambda x: x and 'clickable-element' in x, string=lambda x: x and 'DESCRIPTION' in str(x))
if not desc_section:
    desc_strong = desc_soup.find('strong', string='DESCRIPTION')
    if desc_strong:
        desc_section = desc_strong.find_parent('div', class_=lambda x: x and 'clickable-element' in x)

if desc_section:
    # Get the container that holds both trigger and content
    container = desc_section.find_parent('div', class_=lambda x: x and 'Group' in x)
    if container:
        print("\nDESCRIPTION SECTION FULL HTML:")
        print("-"*80)
        desc_html_snippet = container.prettify()[:2000]
        print(desc_html_snippet)
        
        with open("description_section_detail.html", "w", encoding="utf-8") as f:
            f.write(container.prettify())
        print("\n✓ Full DESCRIPTION section HTML saved to: description_section_detail.html")

print("\n" + "="*80)
print("ANALYSIS COMPLETE")
print("="*80)
print("\nGenerated files:")
print("  - size_section_detail.html")
print("  - description_section_detail.html")
