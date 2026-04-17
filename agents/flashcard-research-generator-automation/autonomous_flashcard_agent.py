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

APP_SCRIPT_URL = os.getenv("APP_SCRIPT_URL", "https://script.google.com/macros/s/AKfycbxrVC5t3Ak35q2cQLUAsFern7aOwLXChbpsADbXW4vNPNnyhHGr6cF1vuh_FYol7CiwGw/exec").strip()
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

# Apify API Setup
APIFY_API_KEY = os.getenv("APIFY_API_KEY", "").strip()

# =========================================================
# 2. HELPERS
# =========================================================
def crawl_with_apify(url: str) -> str:
    """Sử dụng Apify Website Content Crawler để lấy nội dung sạch."""
    if not APIFY_API_KEY:
        return ""
    
    logger.info(f"🕸️ Deep crawling with Apify: {url}")
    endpoint = "https://api.apify.com/v2/acts/apify~website-content-crawler/run-sync-get-dataset-items"
    payload = {
        "startUrls": [{"url": url}],
        "maxCrawlPages": 1,
        "crawlerType": "cheerio", # Nhanh và hiệu quả cho text
        "htmlTransformer": "readableText" # Chỉ lấy nội dung chính readable
    }
    try:
        resp = requests.post(f"{endpoint}?token={APIFY_API_KEY}", json=payload, timeout=180)
        if resp.ok:
            items = resp.json()
            if items and isinstance(items, list):
                # Gộp text từ các page (ở đây chỉ lấy 1 page)
                return items[0].get("text", "")
    except Exception as e:
        logger.error(f"Apify error: {e}")
    return ""

def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()

def fix_sentence_case(text: str) -> str:
    # Known technical acronyms to keep UPPERCASE
    acronyms = {
        "OSHA", "HIPAA", "PPE", "CDC", "CLSI", "HIV", "HBV", "HCV", 
        "EDTA", "SST", "PST", "CBC", "PT", "PTT", "INR", "GTT", 
        "HCG", "PKU", "ABG", "TDM", "SDS", "MSDS", "RBC", "WBC",
        "WBS", "TCP/IP", "IaaS", "PaaS", "SaaS", "RBAC", "VPC", "VNet"
    }
    
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    if not text: return ""
    
    words = text.split()
    new_words = []
    for word in words:
        # Strip non-alphanumeric for checking but keep original for building
        clean = re.sub(r'[^\w]', '', word).upper()
        if clean in acronyms or (word.isupper() and len(clean) <= 5):
            new_words.append(word.upper())
        else:
            new_words.append(word.lower())
            
    result = " ".join(new_words)
    if result:
        # Capitalize only the first letter of the entire term
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
        # Refine query to exclude marketing/brochure content
        refined_query = f"{query} -brochure -registration -benefits -fee -apply"
        urls = []
        if self.tavily:
            try:
                logger.info(f"Searching Tavily for: {refined_query}")
                tavily_res = self.tavily.search(query=refined_query, search_depth="advanced", max_results=max_results)
                urls = [res['url'] for res in tavily_res.get('results', [])]
                if urls: return urls
            except Exception as e:
                logger.error(f"Tavily search error: {e}")

        try:
            logger.info(f"Searching DuckDuckGo for: {refined_query}")
            with DDGS() as ddgs:
                results = list(ddgs.text(refined_query, max_results=max_results))
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
        
        # Sử dụng Apify để crawl nội dung HTML chất lượng cao
        text_content = crawl_with_apify(url)
        
        # Fallback về BeautifulSoup nếu Apify thất bại
        if not text_content:
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

    def gate_4_1_educational_focus(self, text: str) -> bool:
        """Check if content is actually educational or technical."""
        kill_list = [
            "how to register", "exam fee", "scheduling", "testing center", 
            "passing score", "certification benefits", "why get certified", 
            "registration", "brochure", "flyer", "brochures"
        ]
        text_lower = text.lower()
        hits = sum(1 for word in kill_list if word in text_lower)
        if hits >= 3: return False
        
        # Must contain technical/educational keywords
        technical_keywords = ["diagnosis", "repair", "component", "system", "theory", "operation", "procedure", "definition"]
        t_hits = sum(1 for word in technical_keywords if word in text_lower)
        return t_hits >= 1

    def gate_8_execution_pipeline(self, url: str) -> dict:
        is_live, resp = self.gate_1_validate_and_ping(url)
        if not is_live: return None
        score = self.gate_2_score_tier(url)
        
        # Aggressive penalty for metadata/marketing keywords in URL
        if any(bad in url.lower() for bad in ["brochure", "flyer", "about", "benefit", "registration"]):
            score -= 0.5
            
        if score < 0.5: return None
        is_quality, content = self.gate_4_quality(resp, url)
        if not is_quality: return None
        if content != "PDF_DOCUMENT":
            if not self.gate_4_1_educational_focus(content):
                logger.warning(f"   🚫 Rejected (Meta/Marketing content): {url}")
                return None
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
    def handle_generate(self, app_name: str, target_exam: str, topic_structure: str, dashboard_app_id: str = "") -> dict:
        logger.info(f"⚡ [PHASE 2] Khởi chạy GENERATE cho App: {app_name}...")
        
        # 1. CMS ID Retrieval Pipeline (MANDATORY)
        cms_topics = []
        cms_subtopics = []
        cms_parts = []
        try:
            # Use App ID from dashboard if available, otherwise fallback to mapping
            db_id = dashboard_app_id.strip()
            
            if not db_id:
                db_mapping = {
                    "phlebotomy": "4633794564849664",
                    "teas": "5154331313569792",
                    "az900": "6465901784203264"
                }
                for k, v in db_mapping.items():
                    if k in app_name.lower():
                        db_id = v
                        break
            
            if db_id:
                logger.info(f"Using CMS DatabaseID: {db_id} for mapping.")
                cms_resp = requests.get(f"https://cms-api.abc-elearning.org/api/topic/get-topics-by-database-id?databaseId={db_id}&isAdmin=true", timeout=45)
                if cms_resp.ok:
                    all_cms_data = cms_resp.json()
                    for item in all_cms_data:
                        # type 1 = topic, type 2 = subtopic, type 3 = part
                        t = item.get("type")
                        if t == 1: cms_topics.append(item)
                        elif t == 2: cms_subtopics.append(item)
                        elif t == 3: cms_parts.append(item)
                    logger.info(f"Fetched {len(cms_topics)} Topics, {len(cms_subtopics)} Subtopics, and {len(cms_parts)} Parts from CMS.")
        except Exception as e:
            logger.error(f"CMS API Integration Error: {e}")

        # 2. Parse Dashboard Structure (Handle Leaf Node Policy)
        lines = [l.strip() for l in topic_structure.splitlines() if l.strip()]
        topic_map = {} # topic_num -> {"name": str, "subtopics": [{"name": str}]}
        
        for line in lines:
            sub_match = re.match(r"^(\d+)\.(\d+)\.?\s+(.*)$", line)
            top_match = re.match(r"^(\d+)\.?\s+(.*)$", line)
            
            if sub_match:
                t_num, s_name = sub_match.group(1), sub_match.group(3).strip()
                if t_num not in topic_map: topic_map[t_num] = {"name": "", "subtopics": []}
                topic_map[t_num]["subtopics"].append({"name": s_name})
            elif top_match:
                t_num, t_name = top_match.group(1), top_match.group(2).strip()
                if t_num not in topic_map: topic_map[t_num] = {"name": t_name, "subtopics": []}
                else: topic_map[t_num]["name"] = t_name

        parsed_items = []
        for t_num in sorted(topic_map.keys(), key=int):
            t_data = topic_map[t_num]
            if t_data["subtopics"]:
                # If subtopics exist, ONLY generate for subtopics (Leaf Nodes)
                for st in t_data["subtopics"]:
                    parsed_items.append({"type": 2, "name": st["name"]})
            elif t_data["name"]:
                # If no subtopics, the Topic is the Leaf Node
                parsed_items.append({"type": 1, "name": t_data["name"]})

        all_flashcards = []
        for item in parsed_items:
            logger.info(f"🔍 Mapping Dashboard Item: {item['name']} (Type: {item['type']})")
            
            # 3. Exact ID Matching (MANDATORY Pipeline)
            official_topic_id = "N/A"
            official_subtopic_id = "N/A"
            target_name = item['name'].lower().strip()
            
            if item['type'] == 1: # FIND TOPIC ID (type=1)
                for ct in cms_topics:
                    if target_name == ct.get("name", "").lower().strip():
                        official_topic_id = str(ct.get("id"))
                        break
            else: # FIND SUBTOPIC -> PART 1 (type=3)
                part_target_name = f"{target_name} 1"
                for cp in cms_parts:
                    if part_target_name == cp.get("name", "").lower().strip():
                        official_subtopic_id = str(cp.get("id"))
                        # Find parent topic via subtopic parent
                        for cs in cms_subtopics:
                            if cs.get("id") == cp.get("parentId"):
                                official_topic_id = str(cs.get("parentId"))
                                break
                        break
            
            if official_topic_id == "N/A" and official_subtopic_id == "N/A":
                logger.warning(f"   ⚠️ Could not map CMS ID for '{item['name']}'. Ensure naming consistency.")
                continue

            # 4. Retrieval Logic via SEARCH_API
            context_text = ""
            try:
                search_resp = requests.post(SEARCH_API, json={
                    "query": f"Granular technical definitions, formulas, and concepts for {item['name']} in {target_exam}",
                    "app_name": app_name, "limit": 50, "similarity_threshold": 0.1
                }, timeout=120)
                if search_resp.ok:
                    search_data = search_resp.json()
                    context_text = search_data.get("answer", "") or search_data.get("response", "") or str(search_data)
            except Exception as e:
                logger.error(f"Search API error: {e}")

            if len(context_text) < 3000 and self.tavily:
                logger.info(f"   Context low. Supplemental Tavily search for '{item['name']}'...")
                try:
                    tav_res = self.tavily.search(query=f"{target_exam} {item['name']} technical guide", search_depth="advanced", max_results=5)
                    for tr in tav_res.get('results', []):
                        context_text += f"\nSource {tr['url']}: {tr['content']}"
                except: pass

            # KPI Determination: 30 for subtopics, 50 for topics
            kpi_count = 30 if item['type'] == 2 else 50
            logger.info(f"   KPI target: {kpi_count} flashcards for '{item['name']}'")

            prompt = f"""
            You are an expert Learning Designer. Target Exam: {target_exam} | Current Item: {item['name']}
            REFERENCE DATA (Bucket Knowledge): 
            {context_text[:45000]}
            
            MANDATORY STANDARDS (FLASHCARD GENERATION RULES)

            A. GENERAL REQUIREMENTS:
            - Language: ALL output MUST be written entirely in English.

            B. "FRONT" TERM CRITERIA:
            1. Deep Topic Alignment: Extract ONLY critical technical knowledge, domain concepts, formulas, or laws that STRICTLY belong to the current topic/subtopic ("{item['name']}").
            2. Anti-Meta Kill List (STRICT): ABSOLUTELY PROHIBITED to extract terms about the exam itself. REJECT any terms related to logistics, formats, scoring, administrative materials (e.g., "Handbook", "Passing Score", "Chapter 1").
            3. Context-Independent: The term MUST make complete sense on its own. Do not extract generic words like "The Process", "Costs", or "Requirements". Append domain context if needed (e.g., change "Costs" to "Civil Liability Costs").
            4. No Questions or Actions: DO NOT use conversational questions or instructional verbs. (e.g., NO "What is X?"). Convert phrases like "How to check ID" into "ID Checking Process".
            5. Capitalization (STRICT): Only capitalize the first letter of the entire term and any acronyms (e.g., "Engineering controls", "OSHA standards"). All other words MUST be lowercase. Incorrect: "Engineering CONTROLS".
            6. Length: Strictly 1 to 8 words.

            C. "BACK" EXPLANATION CRITERIA:
            1. Core Content: Provide a direct definition PLUS one essential, testable related characteristic.
            2. Anti-Circular (STRICT): STRICTLY PROHIBITED to use the Front term (or its root words) in the explanation. Use synonyms or pronouns to explain the concept.
            3. Self-Contained: Do not reference source documents or diagrams (NO "According to...", "In this chapter...", "Figure X").
            4. Strict Formatting: Output as a SINGLE continuous block of text. NO bullet points, NO line breaks.
            5. Length: Strictly 1-2 concise sentences (approx. 20-40 words).

            D. MATH & FORMULA FORMATTING (MANDATORY):
            - Formulas and units MUST be wrapped in MathJax format. 
            - Because the output is JSON, you MUST double-escape backslashes: use \\\\(..\\\\) instead of \\(..\\). 
            - Example: Use \\\\text{{word}} for text inside formulas.
            
            KPI: Extract exactly {kpi_count} unique technical flashcards for this specific item.
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
                    # Apply strict sentence case fixing
                    card["Front"] = fix_sentence_case(normalize_whitespace(card["Front"]))
                    card["Back"] = normalize_whitespace(card["Back"])
                    
                all_flashcards.extend(cards_data)
                logger.info(f"✅ Extracted {len(cards_data)} cards for {item['name']} (Target: {kpi_count})")
            except Exception as e:
                logger.error(f"Generation error Topic {item['name']}: {e}")

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
                    app_id = str(row.get("appId", "") or row.get("databaseId", "")).strip()
                    if not app: continue
                    
                    target_exam = row.get("targetExam", "")
                    exam_vendor = row.get("examVendor", "")
                    topic_structure = row.get("topicStructure", "")
                    
                    research_status = str(row.get("researchStatus", "")).strip().lower()
                    generate_status = str(row.get("generateStatus", "")).strip().lower()
                    
                    logger.info(f"Task: {app} (ID: {app_id}) | Research: {research_status} | Generate: {generate_status}")
                    
                    if research_status == "research":
                        logger.info(f"🚀 Triggering RESEARCH for {app}...")
                        requests.post(APP_SCRIPT_URL, data=json.dumps({"action":"update_status", "app_name":app, "column":"research", "status":"Pending"}), headers={'Content-Type': 'application/json'}, allow_redirects=True)
                        res = self.handle_research(app, target_exam, exam_vendor)
                        final_status = "Done" if not res["needs_more"] else "Fail"
                        requests.post(APP_SCRIPT_URL, data=json.dumps({"action":"update_status", "app_name":app, "column":"research", "status":final_status}), headers={'Content-Type': 'application/json'}, allow_redirects=True)
                    
                    if generate_status == "generate":
                        logger.info(f"⚡ Triggering GENERATE for {app}...")
                        requests.post(APP_SCRIPT_URL, data=json.dumps({"action":"update_status", "app_name":app, "column":"generate", "status":"Pending"}), headers={'Content-Type': 'application/json'}, allow_redirects=True)
                        res = self.handle_generate(app, target_exam, topic_structure, dashboard_app_id=app_id)
                        final_status = "Done" if len(res.get("flashcards", [])) > 0 else "Fail"
                        requests.post(APP_SCRIPT_URL, data=json.dumps({"action":"update_status", "app_name":app, "column":"generate", "status":final_status}), headers={'Content-Type': 'application/json'}, allow_redirects=True)

            except Exception as e:
                logger.error(f"Loop error: {e}")
            
            time.sleep(120) 

if __name__ == "__main__":
    FlashcardAgent().run_loop()
