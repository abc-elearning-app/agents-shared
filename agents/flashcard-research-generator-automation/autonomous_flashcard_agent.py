import os
import re
import json
import time
import logging
import hashlib
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from pydantic import BaseModel
from duckduckgo_search import DDGS
from tavily import TavilyClient
from google import genai
from google.genai import types
from typing import Any, List, Dict, Tuple, Optional

# =========================================================
# 1. CONFIG & ENV SETUP
# =========================================================
def load_dotenv_simple(env_path: str = ".env") -> None:
    if not os.path.exists(env_path): return
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            raw = line.strip()
            if not raw or raw.startswith("#") or "=" not in raw: continue
            k, v = raw.split("=", 1)
            os.environ[k.strip()] = v.strip()

load_dotenv_simple()

APP_SCRIPT_URL = os.getenv("APP_SCRIPT_URL", "").strip()
INGEST_API = os.getenv("INGEST_API", "http://117.7.0.31:5930/ingest-url").strip()
SEARCH_API = os.getenv("SEARCH_API", "http://117.7.0.31:5930/search/chat").strip()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash").strip()

# Tavily API Key provided by user
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "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").strip()

# Logger Setup
logger = logging.getLogger("flashcard_agent")
logger.setLevel(logging.INFO)
if not logger.handlers:
    fh = logging.FileHandler("agent_stdout.log", encoding="utf-8")
    sh = logging.StreamHandler()
    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    fh.setFormatter(fmt); sh.setFormatter(fmt)
    logger.addHandler(fh); logger.addHandler(sh)

# =========================================================
# 2. HELPERS
# =========================================================
def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()

def fix_sentence_case(text: str) -> str:
    text = normalize_whitespace(text)
    if not text: return ""
    
    words = text.split()
    new_words = []
    for i, word in enumerate(words):
        # Acronym check: all caps and has at least one letter
        has_letter = any(c.isalpha() for c in word)
        clean_word = re.sub(r'[^\w]', '', word)
        
        if word.isupper() and len(clean_word) >= 2 and has_letter:
            # It's an acronym (e.g., "WBS", "TCP/IP"), keep it
            new_words.append(word)
        elif any(c.isupper() for c in word[1:]) and len(word) > 1:
            # Likely a proper noun or mixed-case acronym (e.g., "iPhone", "McDonal"), keep it
            new_words.append(word)
        else:
            # General concept word, lowercase it
            new_words.append(word.lower())
            
    result = " ".join(new_words)
    if result:
        # Capitalize the first letter of the term
        result = result[0].upper() + result[1:]
    return result

def parse_json_maybe(text: str) -> Any:
    try: return json.loads(text)
    except:
        match = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
        if match:
            try: return json.loads(match.group(1))
            except: return None
    return None

# =========================================================
# 3. SCHEMA & LOGIC PHASE 2
# =========================================================
class FlashcardOutput(BaseModel):
    Topic: str     # ID số của Topic (Mã loại 1)
    Subtopic: str  # ID số của Subtopic (Mã loại 2)
    Front: str
    Back: str


# =========================================================
# 4. RESEARCH ENGINE (TAVILY & 8 GATES)
# =========================================================
class ResearchEngine:
    BLOCKED_DOMAINS = [
        "baidu.com", "zhihu.com", "csdn.net", "bilibili.com", "weibo.com", 
        "sogou.com", "360.cn", "douban.com", "toutiao.com", "jianshu.com"
    ]
    SUPPORTED_FORMATS = [".pdf", ".md", ".txt", ".text", ".json", ".docx", ".html", ".htm"]
    
    def __init__(self, exam: str, vendor: str):
        self.exam = exam
        self.vendor = vendor if vendor else "" 
        self.ingested_registry = {} 
        self.tavily = TavilyClient(api_key=TAVILY_API_KEY) if TAVILY_API_KEY else None

    def search_web(self, query: str, max_results=30) -> list[str]:
        urls = []
        if self.tavily:
            try:
                logger.info(f"Searching Tavily for: {query}")
                tavily_res = self.tavily.search(query=query, search_depth="advanced", max_results=max_results)
                urls = [res['url'] for res in tavily_res.get('results', [])]
                if urls: return urls
            except Exception as e:
                logger.error(f"Tavily search error: {e}")

        try:
            logger.info(f"Searching DuckDuckGo for: {query}")
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
                urls = [res['href'] for res in results]
        except Exception as e:
            logger.error(f"DDG search error: {e}")
        return urls

    def gate_1_validate_and_ping(self, url: str) -> tuple[bool, Any]:
        domain = urlparse(url).netloc.lower()
        if any(b in domain for b in self.BLOCKED_DOMAINS):
            return False, "Blocked Domain"
        if not url.startswith(("http://", "https://")):
            return False, "Invalid Protocol"
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code >= 400: 
                return False, f"HTTP Error {resp.status_code}"
            return True, resp
        except Exception:
            return False, "Connection Failed"

    def gate_2_score_tier(self, url: str) -> float:
        url_lower = url.lower()
        score = 0.7 
        vendor_lower = self.vendor.lower()
        
        tier1_domains = [".gov", ".mil", ".edu", "comptia.org", "isc2.org", "pmi.org", "aws.amazon.com"]
        if vendor_lower: tier1_domains.append(vendor_lower)
        
        if any(ext in url_lower for ext in tier1_domains if ext):
            score = 0.9 
        elif any(ext in url_lower for ext in ["whizlabs.com", "pluralsight.com", "github.com", "pilotinstitute.com"]):
            score = 0.8 
            
        if url_lower.endswith(".pdf"): score += 0.1
        if any(kw in url_lower for kw in ["guide", "cheat", "blueprint", "objectives", "syllabus"]): score += 0.05
        if any(kw in url_lower for kw in ["flashcard", "reddit", "forum"]): score -= 0.2
        return min(1.0, max(0.0, score))

    def gate_3_freshness(self, text_content: str) -> bool:
        version_match = re.search(r'\d{3,}', self.exam)
        if version_match:
            current_version = version_match.group(0)
            try:
                old_versions = [str(int(current_version) - 100), str(int(current_version) - 200)]
                for old_v in old_versions:
                    if old_v in text_content and current_version not in text_content:
                        return False
            except: pass
        return True

    def gate_4_quality(self, resp_object, url: str) -> tuple[bool, str]:
        if url.lower().endswith(".pdf") or "application/pdf" in resp_object.headers.get("Content-Type", ""):
            return True, "PDF_DOCUMENT"
        soup = BeautifulSoup(resp_object.text, 'html.parser')
        text_content = soup.get_text(separator=' ', strip=True)
        if len(text_content) < 500: return False, "" 
        return True, text_content

    def gate_5_deduplication(self, url: str, score: float) -> tuple[bool, str]:
        canonical_id = hashlib.md5(url.encode()).hexdigest()
        if canonical_id in self.ingested_registry:
            existing_score = self.ingested_registry[canonical_id]
            if existing_score >= 0.9 and score < 0.9:
                return False, "Duplicate of Tier 1 Source"
            elif score > existing_score:
                self.ingested_registry[canonical_id] = score
                return True, canonical_id
            return False, "Already Ingested"
        self.ingested_registry[canonical_id] = score
        return True, canonical_id

    def gate_6_format_support(self, url: str) -> tuple[bool, str]:
        url_lower = url.lower()
        ext = ".html"
        for f in self.SUPPORTED_FORMATS:
            if url_lower.endswith(f):
                ext = f
                break
        return True, ext

    def gate_7_kpi(self, current_count: int) -> bool:
        return current_count >= 20

    def gate_8_execution_pipeline(self, url: str) -> dict:
        is_live, resp = self.gate_1_validate_and_ping(url)
        if not is_live: return None
        score = self.gate_2_score_tier(url)
        if score < 0.5: return None
        is_quality, content = self.gate_4_quality(resp, url)
        if not is_quality: return None
        if content != "PDF_DOCUMENT":
            is_fresh = self.gate_3_freshness(content)
            if not is_fresh: return None
        is_unique, canonical_id = self.gate_5_deduplication(url, score)
        if not is_unique: return None
        is_supported, ext = self.gate_6_format_support(url)
        return {
            "url": url,
            "canonical_id": canonical_id,
            "tier": 1 if score >= 0.9 else 2 if score >= 0.8 else 3,
            "score": score,
            "format": ext.replace(".", "")
        }


# =========================================================
# 5. FLASHCARD AGENT CỐT LÕI
# =========================================================
class FlashcardAgent:
    def __init__(self):
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        self.INGEST_API = INGEST_API
        self.tavily = TavilyClient(api_key=TAVILY_API_KEY) if TAVILY_API_KEY else None

    # --- PHASE 1: RESEARCH & INGESTION ---
    def handle_research(self, app_name: str, target_exam: str, exam_vendor: str) -> dict:
        logger.info(f"🚀 [PHASE 1] Khởi chạy RESEARCH cho App: {app_name}")
        
        engine = ResearchEngine(target_exam, exam_vendor)
        queries = [f"{target_exam} official guide pdf", f"{target_exam} exam objectives", f"{target_exam} study guide"]
        
        raw_urls = set()
        for q in queries:
            raw_urls.update(engine.search_web(q))

        sources_ingested = []
        for url in list(raw_urls):
            if engine.gate_7_kpi(len(sources_ingested)): break

            approved_source = engine.gate_8_execution_pipeline(url)
            if approved_source:
                logger.info(f"📥 Approved: {url} (Score: {approved_source['score']})")
                try:
                    ingest_resp = requests.post(self.INGEST_API, json={
                        "url": url,
                        "app_name": app_name,
                        "bucket_name": app_name,
                        "index_document": True
                    }, timeout=120)
                    
                    if ingest_resp.ok:
                        sources_ingested.append(approved_source)
                        logger.info(f"✅ Ingested successfully: {url}")
                except Exception as e:
                    logger.error(f"Ingest API error: {e}")

        return {
            "status": "research_completed",
            "app_name": app_name,
            "needs_more": len(sources_ingested) < 3,
            "sources_ingested": sources_ingested
        }

    # --- PHASE 2: GENERATE ---
    def handle_generate(self, app_name: str, target_exam: str, topic_structure: str) -> dict:
        logger.info(f"⚡ [PHASE 2] Khởi chạy GENERATE cho App: {app_name}...")
        
        # 1. Fetch Official CMS Mapping
        cms_topics = []
        cms_subtopics = []
        try:
            # Map App to DatabaseID
            db_mapping = {
                "phlebotomy": "4633794564849664",
                "teas": "5154331313569792"
            }
            db_id = ""
            for k, v in db_mapping.items():
                if k in app_name.lower():
                    db_id = v
                    break
            
            if db_id:
                logger.info(f"Connecting to CMS for databaseId: {db_id}")
                cms_resp = requests.get(f"https://cms-api.abc-elearning.org/api/topic/get-topics-by-database-id?databaseId={db_id}&isAdmin=true", timeout=30)
                if cms_resp.ok:
                    all_cms_data = cms_resp.json()
                    for item in all_cms_data:
                        # type 1 = topic, 2 = subtopic
                        if item.get("type") == 1: cms_topics.append(item)
                        elif item.get("type") == 2: cms_subtopics.append(item)
                    logger.info(f"Fetched {len(cms_topics)} Topics and {len(cms_subtopics)} Subtopics from CMS.")
        except Exception as e:
            logger.error(f"CMS API error: {e}")

        # 2. Parse Dashboard Structure
        topics = []
        for l in topic_structure.splitlines():
            m = re.match(r"^(\d+)\.?\s+(.*)$", l.strip())
            if m: topics.append({"id": m.group(1), "name": m.group(2)})

        all_flashcards = []
        for t in topics:
            logger.info(f"🔍 Processing Dashboard Topic: {t['name']}...")
            
            # Mapping CMS IDs
            official_topic_id = str(t['id'])
            official_subtopic_id = "N/A"
            clean_dash_name = t['name'].lower().strip()
            
            # Check Subtopics first
            found = False
            for st in cms_subtopics:
                st_name = st.get("name", "").lower().strip()
                if clean_dash_name == st_name or clean_dash_name in st_name or st_name in clean_dash_name:
                    official_subtopic_id = str(st.get("id"))
                    official_topic_id = str(st.get("parentId"))
                    found = True
                    logger.info(f"   Mapped dashboard '{t['name']}' to CMS Subtopic ID: {official_subtopic_id}")
                    break
            
            if not found:
                for tp in cms_topics:
                    tp_name = tp.get("name", "").lower().strip()
                    if clean_dash_name == tp_name or clean_dash_name in tp_name or tp_name in clean_dash_name:
                        official_topic_id = str(tp.get("id"))
                        official_subtopic_id = "N/A"
                        found = True
                        logger.info(f"   Mapped dashboard '{t['name']}' to CMS Topic ID: {official_topic_id}")
                        break
            
            # Retrieval Logic
            context_text = ""
            try:
                search_resp = requests.post(SEARCH_API, json={
                    "query": f"Granular technical definitions, formulas, and concepts for {t['name']} in {target_exam}",
                    "app_name": app_name, "limit": 30, "similarity_threshold": 0.1
                }, timeout=60)
                if search_resp.ok:
                    search_data = search_resp.json()
                    context_text = search_data.get("answer", "") or search_data.get("response", "") or str(search_data)
            except Exception as e:
                logger.error(f"Search API error: {e}")

            if len(context_text) < 3000 and self.tavily:
                logger.info(f"   Context low. Supplemental Tavily search for '{t['name']}'...")
                try:
                    tav_res = self.tavily.search(query=f"{target_exam} {t['name']} technical guide", search_depth="advanced", max_results=5)
                    for tr in tav_res.get('results', []):
                        context_text += f"\nSource {tr['url']}: {tr['content']}"
                except: pass

            # KPI Determination: 30 for subtopics, 50 for topics
            kpi_count = 30 if official_subtopic_id != "N/A" else 50
            logger.info(f"   KPI target: {kpi_count} flashcards for '{t['name']}'")

            prompt = f"""
            You are an Autonomous Knowledge Extraction Expert and Learning Designer. 
            Target Exam: {target_exam}
            Current Topic: {t['name']} (ID: {official_topic_id}, Subtopic ID: {official_subtopic_id})
            
            REFERENCE DATA: 
            {context_text[:45000]}
            
            MANDATORY STANDARDS:
            A. Language: ALL output MUST be written entirely in English.
            B. Term (Front): 
               - Priority: Single words, short phrases, idioms, or core concepts.
               - MUST make complete sense on its own (Context-Independent).
               - Strictly use UPPERCASE for Acronyms (e.g., "WBS", "TCP/IP") and Proper Nouns. 
               - Use Lowercase for general concepts, but still CAPITALIZE the first letter of the term.
               - Length: Strictly 1 to 8 words. 
               - PROHIBITED: No question formats (e.g., NO "What is X?").
            C. MathJax Formatting (MANDATORY):
               - Formulas MUST be wrapped in \(..\) signs with NO spaces between signs and content. 
               - Use \\text{{}} for words inside formulas. Example: \\(\\text{{Speed}} = \\frac{{\\text{{Distance}}}}{{\\text{{Time}}}}\\)
            D. Explanation (Back):
               - Provide a direct definition PLUS one essential piece of related knowledge (primary use case, characteristic, or significance).
               - Anti-Circular: STRICTLY PROHIBITED to use the Front term itself (or its direct root words) in the explanation.
               - Self-Contained: Do not reference source material (NO "According to...", "Figure X").
               - Length: Strictly 1-2 concise sentences (approx. 20-40 words). 
               - Output as a SINGLE continuous block; NO bullet points, NO line breaks.
            
            KPI: Extract exactly {kpi_count} unique technical flashcards for this specific item. Ignore all administrative or exam logistics information.
            """

            try:
                response = self.client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=list[FlashcardOutput],
                        temperature=0.1 
                    )
                )
                
                cards_data = json.loads(response.text)
                for card in cards_data:
                    card["Topic"] = str(official_topic_id)
                    card["Subtopic"] = str(official_subtopic_id)
                    card["Front"] = normalize_whitespace(card["Front"])
                    card["Back"] = normalize_whitespace(card["Back"])
                    
                all_flashcards.extend(cards_data)
                logger.info(f"✅ Extracted {len(cards_data)} cards for {t['name']} (Target: {kpi_count})")
            except Exception as e:
                logger.error(f"Generation error Topic {t['name']}: {e}")

        if all_flashcards:
            try:
                # Final deduplication
                seen = set()
                final_cards = []
                for c in all_flashcards:
                    if c['Front'].lower() not in seen:
                        seen.add(c['Front'].lower())
                        final_cards.append(c)
                
                requests.post(APP_SCRIPT_URL, data=json.dumps({
                    "action": "upload_flashcards",
                    "app_name": app_name,
                    "flashcards": final_cards
                }), headers={'Content-Type': 'application/json'}, allow_redirects=True, timeout=120)
                logger.info(f"🚀 Uploaded {len(final_cards)} flashcards successfully.")
            except Exception as e:
                logger.error(f"Upload error: {e}")

        return {"status": "completed", "app_name": app_name, "flashcards": all_flashcards}

    # --- MAIN LOOP ---
    def run_loop(self):
        logger.info("=====================================================")
        logger.info("🧠 Flashcard Agent V10 (Strict Fixed) Started")
        logger.info("=====================================================")
        
        while True:
            try:
                logger.info(f"Connecting to dashboard: {APP_SCRIPT_URL}")
                resp = requests.post(APP_SCRIPT_URL, data=json.dumps({"action": "read_tasks"}), headers={'Content-Type': 'application/json'}, allow_redirects=True, timeout=60)
                logger.info(f"Dashboard response status: {resp.status_code}")
                tasks = resp.json().get("tasks", []) if resp.ok else []
                logger.info(f"Checking {len(tasks)} tasks from dashboard...")
                
                for row in tasks:
                    app = str(row.get("appName", "")).strip()
                    if not app: continue
                    
                    target_exam = row.get("targetExam", "")
                    exam_vendor = row.get("examVendor", "")
                    topic_structure = row.get("topicStructure", "")
                    
                    research_status = str(row.get("researchStatus", "")).strip().lower()
                    generate_status = str(row.get("generateStatus", "")).strip().lower()
                    
                    logger.info(f"Task: {app} | Research: {research_status} | Generate: {generate_status}")
                    
                    if research_status == "research":
                        logger.info(f"🚀 Triggering RESEARCH for {app}...")
                        requests.post(APP_SCRIPT_URL, data=json.dumps({"action":"update_status", "app_name":app, "column":"research", "status":"Pending"}), headers={'Content-Type': 'application/json'}, allow_redirects=True)
                        res = self.handle_research(app, target_exam, exam_vendor)
                        final_status = "Done" if not res["needs_more"] else "Fail"
                        requests.post(APP_SCRIPT_URL, data=json.dumps({"action":"update_status", "app_name":app, "column":"research", "status":final_status}), headers={'Content-Type': 'application/json'}, allow_redirects=True)
                    
                    if generate_status == "generate":
                        logger.info(f"⚡ Triggering GENERATE for {app}...")
                        requests.post(APP_SCRIPT_URL, data=json.dumps({"action":"update_status", "app_name":app, "column":"generate", "status":"Pending"}), headers={'Content-Type': 'application/json'}, allow_redirects=True)
                        res = self.handle_generate(app, target_exam, topic_structure)
                        final_status = "Done" if len(res.get("flashcards", [])) > 0 else "Fail"
                        requests.post(APP_SCRIPT_URL, data=json.dumps({"action":"update_status", "app_name":app, "column":"generate", "status":final_status}), headers={'Content-Type': 'application/json'}, allow_redirects=True)

            except Exception as e:
                logger.error(f"Loop error: {e}")
            
            time.sleep(120) 

if __name__ == "__main__":
    FlashcardAgent().run_loop()
