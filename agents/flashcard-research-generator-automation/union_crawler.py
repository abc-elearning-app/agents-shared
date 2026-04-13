import requests
from bs4 import BeautifulSoup
import time
import os
import re

def crawl_union_test_prep(base_url, output_file):
    all_content = "<html><head><meta charset='UTF-8'></head><body>"
    current_page = 1
    
    while True:
        url = f"{base_url.rstrip('/')}/pages/{current_page}"
        print(f"Crawling: {url}")
        
        try:
            response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
            if response.status_code != 200:
                print(f"Stopped at page {current_page} (Status {response.status_code})")
                break
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Union Test Prep structure: look for main study guide content
            content_section = soup.find('div', class_='study-guide-content') or soup.find('div', class_='page-content') or soup.find('article')
            
            if not content_section:
                print("No content section found. Ending.")
                break
                
            # Clean up the content
            for tag in content_section.find_all(['script', 'style', 'nav', 'header', 'footer']):
                tag.decompose()
                
            all_content += f"<hr><h1>{base_url.split('/')[-1].replace('-', ' ').title()} - Page {current_page}</h1>"
            all_content += str(content_section)
            
            # Check for next page
            # Usually it has a pagination or just check if the content changes
            if current_page > 15: break # Safety limit
            
            current_page += 1
            time.sleep(1.5) 
        except Exception as e:
            print(f"Error: {e}")
            break
            
    all_content += "</body></html>"
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(all_content)
    print(f"Saved {current_page-1} pages to {output_file}")

if __name__ == "__main__":
    # Crawl cho từng môn của Accuplacer
    subjects = [
        "next-generation-advanced-algebra-and-functions",
        "next-generation-arithmetic",
        "next-generation-quantitative-reasoning-algebra-and-statistics",
        "next-generation-reading",
        "next-generation-writing"
    ]
    
    for sub in subjects:
        base = f"https://uniontestprep.com/accuplacer-test/study-guide/{sub}"
        output = f"union_{sub.replace('-', '_')}.html"
        crawl_union_test_prep(base, output)
