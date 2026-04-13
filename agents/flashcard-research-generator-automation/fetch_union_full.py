import os
import time
import requests
from google import genai
from google.genai import types

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

subjects = [
    "next-generation-advanced-algebra-and-functions",
    "next-generation-arithmetic",
    "next-generation-quantitative-reasoning-algebra-and-statistics",
    "next-generation-reading",
    "next-generation-writing"
]

output_file = "union_accuplacer_full_theory.txt"

def fetch_page_content(url):
    prompt = f"Extract the full educational content, definitions, and formulas from this specific study guide page: {url}. If the page is empty or doesn't exist, return 'EMPTY_PAGE'."
    try:
        res = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[{"google_search": {}}]
            )
        )
        return res.text
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return "ERROR"

with open(output_file, "w", encoding="utf-8") as f:
    f.write("=== UNION TEST PREP: ACCUPLACER ULTIMATE THEORY (COMPLETE PAGES) ===\n\n")
    
    for sub in subjects:
        print(f"🚀 Starting Deep Crawl for: {sub}")
        for page in range(1, 16): # Quét tối đa 15 trang mỗi môn (an toàn cho Union Test Prep)
            url = f"https://uniontestprep.com/accuplacer-test/study-guide/{sub}/pages/{page}"
            content = fetch_page_content(url)
            
            if "EMPTY_PAGE" in content or len(content) < 200:
                print(f"  🛑 Reached end of content at Page {page}")
                break
                
            f.write(f"\n--- {sub.upper()} - PAGE {page} ---\n")
            f.write(content)
            f.write("\n\n")
            print(f"  ✅ Page {page} fetched successfully.")
            time.sleep(2) # Tránh bị rate limit

print(f"🏁 MISSION COMPLETE! Full theory saved to: {output_file}")
