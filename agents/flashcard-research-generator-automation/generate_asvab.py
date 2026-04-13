import os
import re
import json
import time
import requests
from google import genai

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)
SEARCH_API = "http://117.7.0.31:5930/search/chat"
SHEET_URL = "https://script.google.com/macros/s/AKfycbzX9ZvLEAZ0D2FRtMnH-97Fahbph6ZXHJFQ4gSj9eTtKIWaMki9USV7URD5w3UmQKfFPg/exec"

def safe_json_loads(text):
    try:
        cleaned = re.sub(r'```json\s*|```', '', text).strip()
        return json.loads(cleaned)
    except json.JSONDecodeError:
        try:
            fixed = cleaned.replace('\\', '\\\\')
            return json.loads(fixed)
        except:
            return None

def get_asvab_task():
    url = "https://script.google.com/macros/s/AKfycbzX9ZvLEAZ0D2FRtMnH-97Fahbph6ZXHJFQ4gSj9eTtKIWaMki9USV7URD5w3UmQKfFPg/exec"
    payload = {"action": "read_tasks"}
    response = requests.post(url, data=json.dumps(payload), headers={'Content-Type': 'application/json'})
    tasks = response.json()
    for task in tasks:
        if task.get('appName') == 'asvab':
            return task
    return None

def main():
    task = get_asvab_task()
    if not task: return

    app_name = "asvab"
    topic_structure = task['topicStructure']
    lines = [line.strip() for line in topic_structure.split('\n') if line.strip()]
    
    structured_topics = []
    current_topic = None
    topic_seq = 0
    
    for line in lines:
        topic_match = re.match(r'^(\d+)\.\s+(.*)', line)
        subtopic_match = re.match(r'^(\d+\.\d+)\.?\s+(.*)', line)
        
        if topic_match and not subtopic_match:
            topic_seq += 1
            current_topic = {"id": str(topic_seq), "name": topic_match.group(2).strip(), "subtopics": []}
            structured_topics.append(current_topic)
            subtopic_seq = 0
        elif subtopic_match:
            subtopic_seq += 1
            current_topic["subtopics"].append({"id": str(subtopic_seq), "name": subtopic_match.group(2).strip()})
    
    for topic in structured_topics:
        for sub in topic["subtopics"]:
            print(f"\n🚀 Processing Topic {topic['id']}, Subtopic {sub['id']}: {sub['name']}")
            
            # 1. Retrieve Source Material
            search_query = f"Provide all detailed facts, definitions, and formulas for ASVAB {topic['name']} and {sub['name']}."
            search_payload = {
                "query": search_query, 
                "app_name": app_name, 
                "limit": 50,
                "similarity_threshold": 0.2
            }
            
            try:
                search_res = requests.post(SEARCH_API, json=search_payload, timeout=45).json()
                knowledge = search_res.get("answer", "")
                
                if not knowledge or "No relevant data found" in knowledge:
                    print(f"Subtopic search failed, trying Topic search for: {topic['name']}")
                    search_payload["query"] = f"Comprehensive study guide for ASVAB {topic['name']}"
                    search_res = requests.post(SEARCH_API, json=search_payload, timeout=45).json()
                    knowledge = search_res.get("answer", "")

                # 2. Read & Extract
                gen_prompt = f"""
                ROLE: Autonomous Knowledge Extraction Expert.
                SOURCE MATERIAL (Context from PDF):
                {knowledge}
                
                TASK: Generate EXACTLY 30 high-quality flashcards for "{sub['name']}" within Topic "{topic['name']}".
                If the source material above is thin, use your expert knowledge of the ASVAB curriculum (matching the style of the provided PDF) to complete the 30 cards.
                
                STRICT CONSTRAINTS:
                A. Language: English.
                B. Front (Term): 1-8 words. No questions.
                C. MathJax: Formula must be wrapped in $ (No spaces, use \\text{{}} for words).
                D. Back: 1-2 concise sentences (20-40 words). No circular definitions.
                E. KPI: Exactly 30 unique terms.
                F. Numbering: Topic MUST be "{topic['id']}". Subtopic MUST be "{sub['id']}".
                
                OUTPUT FORMAT: Return ONLY a single Valid JSON block matching this structure:
                {{
                  "flashcards": [
                    {{
                      "Topic": "{topic['id']}",
                      "Subtopic": "{sub['id']}",
                      "Front": "Term",
                      "Back": "Explanation"
                    }}
                  ]
                }}
                """
                
                res = client.models.generate_content(model="gemini-2.0-flash", contents=gen_prompt)
                result_json = safe_json_loads(res.text)
                
                if result_json and "flashcards" in result_json:
                    batch = result_json["flashcards"]
                    requests.post(SHEET_URL, json={"app_name": app_name, "flashcards": batch}, timeout=30)
                    print(f"✅ Success: Generated and uploaded {len(batch)} cards for Subtopic {sub['id']}.")
                
                time.sleep(2)
            except Exception as e:
                print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
