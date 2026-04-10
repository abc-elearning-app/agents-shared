import os
import re
import json
import time
import requests
from google import genai

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)
SEARCH_API = "http://117.7.0.31:5930/search/chat"
SHEET_URL = "https://script.google.com/macros/s/AKfycbzzNrqiWiV3kTbwaAN1f94X6gcaxxuy7b_NmC1mlKTyBlpjYRZ4JQKcQXVP04qQUfCioQ/exec"

def safe_json_loads(text):
    try:
        cleaned = re.sub(r'```json\s*|```', '', text).strip()
        return json.loads(cleaned)
    except:
        return None

def process_target(app_name, topic_id, sub_id, topic_name, sub_name, kpi=30):
    print(f"\n🎯 Targeted Processing: Topic {topic_id}, Subtopic {sub_id} ({sub_name}) - Target: {kpi} cards")
    
    # 1. Broad Search
    search_query = f"Provide all detailed facts, synonyms, context questions, and definitions for ASVAB {topic_name}: {sub_name}. Use the Word Knowledge Study Guide specifically."
    search_payload = {
        "query": search_query, 
        "app_name": app_name, 
        "limit": 50,
        "similarity_threshold": 0.2
    }
    
    try:
        search_res = requests.post(SEARCH_API, json=search_payload, timeout=45).json()
        knowledge = search_res.get("answer", "")
        
        # 2. Generate with higher KPI for Topic 9
        gen_prompt = f"""
        ROLE: Autonomous Knowledge Extraction Expert.
        SOURCE MATERIAL:
        {knowledge}
        
        TASK: Generate EXACTLY {kpi} high-quality flashcards for "{sub_name}" within Topic "{topic_name}".
        Focus on vocabulary, synonyms, and context clues as per the ASVAB Word Knowledge curriculum.
        
        STRICT CONSTRAINTS:
        A. Language: English.
        B. Front: 1-8 words. No questions.
        C. MathJax: $formula$.
        D. Back: 1-2 concise sentences. No circular definitions.
        E. KPI: Exactly {kpi} unique terms.
        F. Numbering: Topic MUST be "{topic_id}". Subtopic MUST be "{sub_id}".
        
        OUTPUT FORMAT: JSON ONLY.
        """
        
        res = client.models.generate_content(model="gemini-2.0-flash", contents=gen_prompt)
        result_json = safe_json_loads(res.text)
        
        if result_json and "flashcards" in result_json:
            batch = result_json["flashcards"]
            requests.post(SHEET_URL, json={"app_name": app_name, "flashcards": batch}, timeout=30)
            print(f"✅ Success: Uploaded {len(batch)} cards to '{app_name}' sheet.")
            return True
    except Exception as e:
        print(f"❌ Error: {e}")
    return False

if __name__ == "__main__":
    app = "asvab"
    # Fix Topic 1 Subtopic 4
    process_target(app, "1", "4", "Arithmetic Reasoning", "Math Operations", kpi=30)
    
    # Regenerate Topic 9 with MAX cards (50 per subtopic as requested "nhất có thể")
    process_target(app, "9", "1", "Word Knowledge", "Contextualised Questions", kpi=50)
    process_target(app, "9", "2", "Word Knowledge", "Synonym-based Questions", kpi=50)
