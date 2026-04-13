import requests
import json
import time
import os
import re
from google import genai

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)
UPLOAD_URL = "https://script.google.com/macros/s/AKfycbzX9ZvLEAZ0D2FRtMnH-97Fahbph6ZXHJFQ4gSj9eTtKIWaMki9USV7URD5w3UmQKfFPg/exec"
SEARCH_API = "http://117.7.0.31:5930/search/chat"

def get_theory(app_name):
    payload = {"query": "Extract all core facts and definitions from this bucket.", "app_name": app_name, "limit": 50}
    try:
        res = requests.post(SEARCH_API, json=payload, timeout=60).json()
        return res.get("answer", "")
    except: return ""

def push_topic(app_name, topic_id, topic_name, theory):
    print(f"🚀 Generating Topic {topic_id}: {topic_name}")
    # Sử dụng ngoặc nhọn kép {{}} để tránh lỗi f-string với JSON
    prompt = f"""
    ROLE: Learning Design Expert.
    THEORY: {theory}
    TASK: Generate 50 unique flashcards for "{topic_name}".
    STRICT CONSTRAINTS: 100% English, MathJax $formula$, Front 1-8 words (no questions), Back 1-2 sentences.
    Topic ID: {topic_id}, Subtopic ID: N/A.
    OUTPUT FORMAT: Return ONLY a valid JSON list like this:
    [
      {{
        "Topic": "{topic_id}",
        "Subtopic": "N/A",
        "Front": "Term",
        "Back": "Explanation"
      }}
    ]
    """
    try:
        res = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        match = re.search(r'(\[.*\])', res.text, re.DOTALL)
        if match:
            cards = json.loads(match.group(1))
            requests.post(UPLOAD_URL, json={"app_name": app_name, "flashcards": cards}, timeout=30)
            print(f"✅ Uploaded {len(cards)} cards for Topic {topic_id}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    app = "accuplacer"
    theory = get_theory(app)
    # Push missing topics
    for tid, tname in [
        ("1", "Next Generation Advanced Algebra and Functions"),
        ("2", "Next Generation Arithmetic"),
        ("3", "Next Generation Quantitative Reasoning, Algebra, and Statistics"),
        ("5", "Next Generation Writing")
    ]:
        push_topic(app, tid, tname, theory)
        time.sleep(3)
