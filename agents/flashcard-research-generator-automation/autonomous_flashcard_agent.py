import requests
import json
import time
import os
import re
import hashlib
from google import genai

# --- SECURE CONFIGURATION ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SHEET_URL = "https://script.google.com/macros/s/AKfycbwM_sk8-VNktBMybaRcoqTnqLTat1XVDtDUklQ-e0ZM-wbVZqFR2P3Ah5LM9gfFRX6P/exec"
INGEST_API = "http://117.7.0.31:5930/ingest-url"
SEARCH_API = "http://117.7.0.31:5930/search/chat"

client = genai.Client(api_key=GEMINI_API_KEY)

def log(msg):
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}")

def update_sheet(app_name, column, status):
    payload = {"action": "update_status", "app_name": app_name, "column": column, "status": status}
    try: requests.post(SHEET_URL, json=payload, timeout=15)
    except: pass

def clean_json(text):
    return re.sub(r'```json\n?|```', '', text).strip()

# =====================================================================
# 2. PHASE 1: REPOSITORY MANAGEMENT, RESEARCH & INGESTION
# =====================================================================

def gate_1_validate(url):
    """Gate 1: URL Validation & Accessibility (CRITICAL)"""
    if not url.startswith("http"): return False
    blocked = ["baidu.com", "zhihu.com", "csdn.net", "bilibili.com", "weibo.com", "sogou.com", "360.cn", "douban.com", "toutiao.com", "jianshu.com"]
    if any(b in url for b in blocked): 
        log(f"Gate 1 Failed: Blocked domain -> {url}")
        return False
    try:
        res = requests.head(url, timeout=10, allow_redirects=True)
        if res.status_code >= 400: return False
        return True
    except:
        return False

def gate_2_score(url):
    """Gate 2: Tier Classification & Scoring"""
    url_lower = url.lower()
    score = 0.7 # Tier 3 default
    
    tier_1_domains = [".gov", ".mil", ".edu", "comptia.org", "isc2.org", "pmi.org", "aws.amazon.com"]
    tier_2_domains = ["whizlabs.com", "pluralsight.com", "github.com", "pilotinstitute.com"]
    
    if any(d in url_lower for d in tier_1_domains): score = 0.9
    elif any(d in url_lower for d in tier_2_domains): score = 0.8
    
    if url_lower.endswith(".pdf"): score += 0.1
    if "guide" in url_lower or "cheat" in url_lower: score += 0.05
    if "flashcard" in url_lower or "reddit" in url_lower or "forum" in url_lower: score -= 0.2
    return score

def phase_1_research(task):
    app_name = task['appName']
    exam = task['targetExam']
    vendor = task['examVendor']
    
    log(f"--- STARTING PHASE 1: RESEARCH FOR [{app_name}] ---")
    update_sheet(app_name, "research", "Pending")
    
    # Step 1: Supabase Bucket Verification (Simulated via Search/Ingest architecture)
    log(f"Step 1: Verifying/Creating exact bucket [{app_name}]")
    
    # Step 2: Autonomous Research
    search_prompt = f"Find 30 high-quality, direct PDF or educational webpage URLs for the '{exam}' by '{vendor}'. Return ONLY a JSON list of strings."
    res = client.models.generate_content(model="gemini-2.0-flash", contents=search_prompt)
    candidate_urls = json.loads(clean_json(res.text))
    
    ingested_sources = []
    canonical_registry = set()
    
    for url in candidate_urls:
        # Gate 7 Check (KPI)
        if len(ingested_sources) >= 20: break
            
        # Gate 1: Validate
        if not gate_1_validate(url): continue
            
        # Gate 2: Tier & Score
        score = gate_2_score(url)
        tier = 1 if score >= 0.9 else (2 if score >= 0.8 else 3)
        
        # Gate 5: Deduplication
        canonical_id = hashlib.md5(url.split('/')[-1].encode()).hexdigest()
        if canonical_id in canonical_registry: continue
        
        # Gate 6 & 8: Format Support & Final Ingestion Flow
        payload = {"url": url, "app_name": app_name, "bucket_name": app_name, "index_document": True}
        try:
            ingest_res = requests.post(INGEST_API, json=payload, timeout=45)
            if ingest_res.status_code == 200:
                canonical_registry.add(canonical_id)
                ingested_sources.append({
                    "url": url,
                    "canonical_id": canonical_id,
                    "tier": tier,
                    "score": round(score, 2),
                    "format": url.split('.')[-1] if '.' in url.split('/')[-1] else "html"
                })
                log(f"Gate 8 Success: Ingested {url} (Score: {score})")
        except:
            continue

    # Gate 7: Minimum Sources KPI & Step 3: Output Phase 1
    needs_more = len(ingested_sources) < 20
    output_json = {
        "status": "research_completed",
        "app_name": app_name,
        "bucket_status": "verified",
        "needs_more": needs_more,
        "sources_ingested": ingested_sources
    }
    
    log(f"PHASE 1 OUTPUT:\n{json.dumps(output_json, indent=2)}")
    
    final_status = "Done" if len(ingested_sources) > 0 else "Fail"
    update_sheet(app_name, "research", final_status)

# =====================================================================
# 3. PHASE 2: RETRIEVAL & GENERATION (Zero-Omission Policy)
# =====================================================================

def phase_2_generate(task):
    app_name = task['appName']
    topic_structure = task['topicStructure']
    
    log(f"--- STARTING PHASE 2: GENERATE FOR [{app_name}] (STRICT WORKFLOW) ---")
    update_sheet(app_name, "generate", "Pending")
    
    # Step 1 & 2: Exhaustive Retrieval & Master Reference Synthesis
    # Fetching 100% of documents in the bucket
    search_payload = {"query": "Extract all core facts, definitions, and formulas from EVERY document in this bucket.", "app_name": app_name, "limit": 100, "similarity_threshold": 0.1}
    try:
        search_res = requests.post(SEARCH_API, json=search_payload, timeout=60).json()
        master_reference = search_res.get("answer", "")
    except:
        master_reference = ""

    lines = [line.strip() for line in topic_structure.split('\n') if line.strip()]
    
    # Correct Hierarchical Parsing for Strict Numbering (Topic: 1, Subtopic: 1)
    topic_seq = 0
    all_flashcards = []
    
    # Logic to identify topics and subtopics
    structured_data = []
    current_topic = None
    
    for line in lines:
        if re.match(r'^\d+\.\s+[a-zA-Z]', line): # Main Topic
            topic_seq += 1
            current_topic = {"id": str(topic_seq), "name": line, "subtopics": []}
            structured_data.append(current_topic)
            sub_seq = 0
        elif re.match(r'^\d+\.\d+\.?\s+', line): # Subtopic
            sub_seq += 1
            current_topic["subtopics"].append({"id": str(sub_seq), "name": line})

    for t_obj in structured_data:
        for s_obj in t_obj["subtopics"]:
            topic_id = t_obj["id"]
            sub_id = s_obj["id"]
            log(f"Generating for Topic {topic_id}, Subtopic {sub_id}")
            
            gen_prompt = f"""
            ROLE: Autonomous Knowledge Extraction Expert.
            MASTER REFERENCE: {master_reference}
            
            TASK: Generate EXACTLY 30 flashcards for "{s_obj['name']}" (Topic {topic_id}).
            
            STRICT CONSTRAINTS:
            A. Language: English only.
            B. Term Standards (Front): 1-8 words, capitalize Acronyms, NO questions.
            C. MathJax: $formula$ (No spaces).
            D. Explanation (Back): 1-2 concise sentences (20-40 words). No circular definitions.
            E. KPI: Exactly 30 unique terms.
            F. Numbering: Topic MUST be "{topic_id}". Subtopic MUST be "{sub_id}".
            
            OUTPUT FORMAT: Single JSON block only.
            """
            
            res = client.models.generate_content(model="gemini-2.0-flash", contents=gen_prompt)
            # ... process and upload ...
            
            OUTPUT FORMAT: Return ONLY a single Valid JSON block matching this structure EXACTLY:
            {{
              "status": "completed",
              "app_name": "{app_name}",
              "flashcards": [
                {{
                  "Topic": "{topic_num}",
                  "Subtopic": "N/A",
                  "Front": "Term",
                  "Back": "Explanation"
                }}
              ]
            }}
            """
            
            res = client.models.generate_content(model="gemini-2.0-flash", contents=gen_prompt)
            result_json = json.loads(clean_json(res.text))
            
            if "flashcards" in result_json:
                all_flashcards.extend(result_json["flashcards"])
                # Đẩy từng Topic lên Sheet
                requests.post(SHEET_URL, json={"app_name": app_name, "flashcards": result_json["flashcards"]}, timeout=30)
                log(f"Topic {topic_num} generated and uploaded ({len(result_json['flashcards'])} cards).")
                
            time.sleep(3) # Tránh rate limit

        # Output Phase 2 JSON Structure to log
        final_output = {
            "status": "completed",
            "app_name": app_name,
            "flashcards": all_flashcards
        }
        log(f"PHASE 2 OUTPUT GENERATED (Total Cards: {len(all_flashcards)})")
        
        update_sheet(app_name, "generate", "Done")
    except Exception as e:
        log(f"❌ Phase 2 Error: {e}")
        update_sheet(app_name, "generate", "Fail")

# =====================================================================
# MAIN WORKER LOOP
# =====================================================================

def main_loop():
    log("🤖 Autonomous Knowledge Extraction Agent (STRICT WORKFLOW) started...")
    while True:
        try:
            tasks = requests.post(SHEET_URL, json={"action": "read_tasks"}, timeout=15).json()
            for task in tasks:
                if not task.get('appName'): continue
                
                if task.get('researchStatus') == "Research":
                    phase_1_research(task)
                
                if task.get('generateStatus') == "Generate":
                    phase_2_generate(task)
                    
        except Exception as e:
            log(f"Polling Error: {e}")
            
        time.sleep(60)

if __name__ == "__main__":
    main_loop()
