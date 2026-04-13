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
    payload = {"query": "Extract all core facts and definitions for ALL ACCUPLACER sections (Math, Reading, Writing).", "app_name": app_name, "limit": 100}
    try:
        res = requests.post(SEARCH_API, json=payload, timeout=60).json()
        return res.get("answer", "")
    except: return ""

def generate_topic_cards(topic_id, topic_name, theory):
    print(f"📡 Generating 50 cards for Topic {topic_id}...")
    prompt = f"""
    THEORY: {theory}
    TASK: Generate exactly 50 high-quality flashcards for "{topic_name}".
    CONSTRAINTS: 100% English, MathJax $formula$, Front 1-8 words, Back 1-2 sentences.
    NUMBERING: Topic="{topic_id}", Subtopic="N/A".
    FORMAT: Return ONLY a JSON list of objects. No filler text.
    """
    try:
        res = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        match = re.search(r'(\[.*\])', res.text, re.DOTALL)
        if match:
            return json.loads(match.group(1))
    except:
        return []
    return []

if __name__ == "__main__":
    app = "accuplacer"
    theory = get_theory(app)
    
    all_250_cards = []
    topics = [
        ("1", "Next Generation Advanced Algebra and Functions"),
        ("2", "Next Generation Arithmetic"),
        ("3", "Next Generation Quantitative Reasoning, Algebra, and Statistics"),
        ("4", "Next Generation Reading"),
        ("5", "Next Generation Writing")
    ]
    
    for tid, tname in topics:
        cards = generate_topic_cards(tid, tname, theory)
        if cards:
            all_250_cards.extend(cards)
            print(f"✅ Created {len(cards)} cards for Topic {tid}")
        time.sleep(2)
        
    if all_250_cards:
        print(f"🚀 Pushing all {len(all_250_cards)} cards to Sheet in order...")
        # Chia làm 2 đợt đẩy để tránh timeout Google Script
        half = len(all_250_cards) // 2
        
        res1 = requests.post(UPLOAD_URL, json={"app_name": app, "flashcards": all_250_cards[:half]}, timeout=60)
        print(f"Batch 1: {res1.text}")
        time.sleep(5)
        res2 = requests.post(UPLOAD_URL, json={"app_name": app, "flashcards": all_250_cards[half:]}, timeout=60)
        print(f"Batch 2: {res2.text}")
        
    print("🏁 DONE! Everything should be in perfect order now.")
