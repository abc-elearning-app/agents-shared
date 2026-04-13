import os
import time
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

output_file = "union_accuplacer_theory.txt"

with open(output_file, "w", encoding="utf-8") as f:
    f.write("=== UNION TEST PREP: ACCUPLACER COMPREHENSIVE THEORY ===\n\n")
    
    for sub in subjects:
        print(f"Fetching theory for: {sub}")
        # Fetching first 2 pages for each to get deep theory without hitting context limits or bot detection too hard
        for page in range(1, 3):
            url = f"https://uniontestprep.com/accuplacer-test/study-guide/{sub}/pages/{page}"
            prompt = f"Extract all educational content, definitions, and formulas from this study guide page: {url}. Provide it in a structured text format."
            
            try:
                res = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        tools=[{"google_search": {}}]
                    )
                )
                f.write(f"\n--- {sub.replace('-', ' ').upper()} - PAGE {page} ---\n")
                f.write(res.text)
                f.write("\n\n")
                print(f"  Successfully fetched Page {page}")
                time.sleep(2)
            except Exception as e:
                print(f"  Failed Page {page}: {e}")

print(f"Completed! File saved: {output_file}")
