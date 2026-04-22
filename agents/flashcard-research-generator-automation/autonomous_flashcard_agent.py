import os
import re
import json
import time
import logging
import hashlib
import requests
import argparse
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
PDF_UPLOAD_API = os.getenv("PDF_UPLOAD_API", "http://117.7.0.31:5930/upload").strip()
SEARCH_API = os.getenv("SEARCH_API", "http://117.7.0.31:5930/search/chat").strip()
SEARXNG_URL = os.getenv("SEARXNG_URL", "http://searxng:8080/search").strip()
URL_REGISTRY_FILE = "url_registry.json"

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash").strip()
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "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").strip()

# Logger Setup (Separated for Parallel Mode)
def setup_logger(mode="all"):
    l = logging.getLogger(f"flashcard_agent_{mode}")
    l.setLevel(logging.INFO)
    if not l.handlers:
        log_filename = f"agent_stdout_{mode}.log"
        fh = logging.FileHandler(log_filename, encoding="utf-8")
        sh = logging.StreamHandler()
        fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
        fh.setFormatter(fmt); sh.setFormatter(fmt)
        l.addHandler(fh); l.addHandler(sh)
    return l

logger = setup_logger("init")
APIFY_API_KEY = os.getenv("APIFY_API_KEY", "").strip()

# =========================================================
# 2. HELPERS
# =========================================================
def load_url_registry() -> dict:
    if os.path.exists(URL_REGISTRY_FILE):
        try:
            with open(URL_REGISTRY_FILE, "r", encoding="utf-8") as f: return json.load(f)
        except: pass
    return {}

def save_url_registry(registry: dict):
    try:
        with open(URL_REGISTRY_FILE, "w", encoding="utf-8") as f: json.dump(registry, f, indent=2)
    except: pass

def normalize_url(url: str) -> str:
    try:
        parsed = urlparse(url)
        netloc = parsed.netloc.lower()
        query_params = []
        if parsed.query:
            for p in parsed.query.split("&"):
                if "=" in p:
                    k, v = p.split("=", 1)
                    if not k.lower().startswith(("utm_", "fbclid", "gclid", "ref")): query_params.append(f"{k}={v}")
        normalized = f"{parsed.scheme}://{netloc}{parsed.path}"
        if query_params: normalized += f"?{'&'.join(query_params)}"
        return normalized
    except: return url.split("#")[0].strip()

def searxng_search(query: str, max_results: int = 10) -> list[dict]:
    try:
        fixed_searxng = SEARXNG_URL.replace("searxng", "localhost")
        resp = requests.get(fixed_searxng, params={"q": query, "format": "json"}, timeout=15)
        if resp.ok:
            results = resp.json().get("results", [])
            return [{"url": r["url"], "title": r.get("title", ""), "snippet": r.get("content", "")} for r in results[:max_results]]
    except: pass
    return []

def crawl_with_apify(url: str) -> str:
    if not APIFY_API_KEY: return ""
    endpoint = "https://api.apify.com/v2/acts/apify~website-content-crawler/run-sync-get-dataset-items"
    payload = {"startUrls": [{"url": url}], "maxCrawlPages": 1, "crawlerType": "cheerio", "htmlTransformer": "readableText"}
    try:
        resp = requests.post(f"{endpoint}?token={APIFY_API_KEY}", json=payload, timeout=180)
        if resp.ok:
            items = resp.json()
            if items and isinstance(items, list): return items[0].get("text", "")
    except: pass
    return ""

def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()

def fix_sentence_case(text: str) -> str:
    acronyms = {"OSHA", "HIPAA", "PPE", "CDC", "CLSI", "HIV", "HBV", "HCV", "EDTA", "SST", "PST", "CBC", "PT", "PTT", "INR", "GTT", "HCG", "PKU", "ABG", "TDM", "SDS", "MSDS", "RBC", "WBC", "WBS", "TCP/IP", "IaaS", "PaaS", "SaaS", "RBAC", "VPC", "VNet"}
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    if not text: return ""
    words = text.split()
    new_words = []
    for word in words:
        clean = re.sub(r'[^\w]', '', word).upper()
        if clean in acronyms or (word.isupper() and len(clean) <= 5): new_words.append(word.upper())
        else: new_words.append(word.lower())
    result = " ".join(new_words)
    if result: result = result[0].upper() + result[1:]
    return result

class FlashcardOutput(BaseModel):
    Topic: str
    Subtopic: str
    Front: str
    Back: str

class ResearchEngine:
    BLOCKED_DOMAINS = ["baidu.com", "zhihu.com", "csdn.net", "bilibili.com", "weibo.com", "sogou.com", "360.cn", "douban.com", "toutiao.com", "jianshu.com"]
    SUPPORTED_FORMATS = [".pdf", ".md", ".txt", ".text", ".json", ".docx", ".html", ".htm"]
    def __init__(self, exam: str, vendor: str):
        self.exam, self.vendor = exam, vendor or ""
        self.registry = load_url_registry()
        self.tavily = TavilyClient(api_key=TAVILY_API_KEY) if TAVILY_API_KEY else None

    def search_web(self, query: str, max_results=30) -> list[str]:
        variations = [f"{query} official textbook filetype:pdf", f'"{self.exam}" "study guide" technical details filetype:pdf', f'"{self.exam}" "coursebook" filetype:pdf', f'site:edu "{self.exam}" textbook filetype:pdf']
        all_urls = set()
        for q in variations:
            if self.tavily:
                try:
                    res = self.tavily.search(query=q, search_depth="advanced", max_results=max_results)
                    for r in res.get('results', []): all_urls.add(r['url'])
                except: pass
            for r in searxng_search(q, max_results=max_results): all_urls.add(r['url'])
        return list(all_urls)

    def gate_8_execution_pipeline(self, url: str) -> dict:
        try:
            resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
            if not resp.ok: return None
        except: return None
        u = url.lower()
        score = 0.7
        if any(x in u for x in [".gov", ".edu", "comptia.org", "isc2.org", "pmi.org"]): score = 0.9
        if u.endswith(".pdf"): score += 0.1
        if score < 0.5: return None
        return {"url": url, "score": score, "canonical_id": hashlib.md5(url.encode()).hexdigest(), "format": "pdf" if u.endswith(".pdf") else "html"}

class FlashcardAgent:
    def __init__(self):
        self.client = genai.Client(api_key=GEMINI_API_KEY)

    def handle_research(self, app_name: str, target_exam: str, exam_vendor: str) -> dict:
        logger.info(f"🚀 [RESEARCH] Start for {app_name}")
        engine = ResearchEngine(target_exam, exam_vendor)
        raw_urls = engine.search_web(target_exam)
        sources_ingested = []
        for url in raw_urls:
            if len(sources_ingested) >= 20: break
            approved = engine.gate_8_execution_pipeline(url)
            if approved:
                try:
                    if approved['format'] == 'pdf':
                        pdf_resp = requests.get(url, timeout=60)
                        if pdf_resp.ok:
                            requests.post(PDF_UPLOAD_API, files={'file': pdf_resp.content}, data={'app_name': app_name}, timeout=120)
                            sources_ingested.append(approved)
                    else:
                        requests.post(INGEST_API, json={"url": url, "app_name": app_name, "bucket_name": app_name, "index_document": True}, timeout=120)
                        sources_ingested.append(approved)
                except: pass
        return {"status": "research_completed", "app_name": app_name, "needs_more": len(sources_ingested) < 5}

    def handle_generate(self, app_name: str, target_exam: str, topic_structure: str, dashboard_app_id: str = "") -> dict:
        logger.info(f"⚡ [GENERATE] Start for {app_name}")
        cms_topics, cms_parts = [], []
        db_id = dashboard_app_id.strip()
        if db_id:
            try:
                cms_url = f"https://cms-api.abc-elearning.org/api/topic/get-topics-by-database-id?databaseId={db_id}&isAdmin=true"
                resp = requests.get(cms_url, timeout=45)
                if resp.ok:
                    for item in resp.json():
                        if item.get("type") == 1: cms_topics.append(item)
                        elif item.get("type") >= 3: cms_parts.append(item)
            except: pass

        # Parse Structure Core 1/2 Strict Order
        lines = [l.strip() for l in topic_structure.splitlines() if l.strip()]
        parsed_items, current_topic_name = [], "General"
        
        raw_structure = []
        for line in lines:
            core_match = re.match(r"^(\d+-\d+):\s+(.*)$", line)
            sub_match = re.match(r"^(\d+)\.(\d+)\.?\s+(.*)$", line)
            top_match = re.match(r"^(\d+)\.?\s+(.*)$", line)
            
            if core_match:
                current_topic_name = line.strip()
                raw_structure.append({"type": 1, "name": current_topic_name, "parent": None})
            elif sub_match:
                raw_structure.append({"type": 2, "name": sub_match.group(3).strip(), "parent": current_topic_name})
            elif top_match:
                current_topic_name = top_match.group(2).strip()
                raw_structure.append({"type": 1, "name": current_topic_name, "parent": None})
        
        # Lọc lấy Leaf Nodes: Nếu Topic có Subtopic đi kèm thì chỉ lấy Subtopic. Nếu không có thì lấy chính Topic.
        for i in range(len(raw_structure)):
            curr = raw_structure[i]
            if curr["type"] == 1:
                has_child = False
                if i + 1 < len(raw_structure) and raw_structure[i+1]["type"] == 2:
                    has_child = True
                if not has_child:
                    parsed_items.append({"type": 1, "name": curr["name"], "parent_name": "General"})
            else:
                parsed_items.append({"type": 2, "name": curr["name"], "parent_name": curr["parent"]})
        
        all_flashcards, all_generated_fronts = [], set()
        failed_any = False
        
        for item in parsed_items:
            logger.info(f"🔍 Processing: {item['name']} (Parent: {item.get('parent_name')})")
            official_topic_id = "N/A"
            clean_name = re.sub(r"^(\d+\.)+\s+", "", item['name'].lower().strip())
            for ct in cms_topics:
                if clean_name in ct.get("name", "").lower(): official_topic_id = str(ct.get("id")); break
            
            # High-Quality Multi-Search Retrieval
            context_text = ""
            search_queries = [f"Technical definitions for {item['name']} in {target_exam}", f"Key procedures and troubleshooting for {item['name']} {target_exam}", f"Industry standards and components of {item['name']}"]
            for q in search_queries:
                try:
                    resp = requests.post(SEARCH_API, json={"query": q, "app_name": app_name, "limit": 30}, timeout=120)
                    if resp.ok: context_text += resp.json().get("answer", "") + "\n\n"
                except: pass

            kpi_count = 30
            batch_size = 25
            num_batches = (kpi_count + batch_size - 1) // batch_size
            topic_cards, topic_success = [], True

            for b_idx in range(num_batches):
                current_goal = min(batch_size, kpi_count - len(topic_cards))
                if current_goal <= 0: break
                
                # STRICT ANTI-DUPLICATION (Topic/App Wide)
                avoid_instruction = ""
                if all_generated_fronts:
                    recent = list(all_generated_fronts)[-150:]
                    avoid_instruction = f"\nSTRICT ANTI-DUPLICATION: You have already generated these cards for this app. DO NOT repeat them:\n{', '.join(recent)}\n"

                prompt = f"Expert Learning Designer. Exam: {target_exam}. Item: {item['name']}\nSource: {context_text[:35000]}\n{avoid_instruction}\nRULES:\n1. English only.\n2. Front: 1-8 words, Capitalize first letter only. No questions.\n3. Back: 1-2 sentences.\n4. MathJax: wrap formulas in \\\\(..\\\\). Use \\\\text{{..}} for words. \nKPI: {current_goal} unique terms."
                
                batch_done = False
                for attempt in range(20): # Persistent 20 Retries
                    try:
                        if attempt > 0: time.sleep(min(30 * attempt, 300))
                        res = self.client.models.generate_content(model=GEMINI_MODEL, contents=prompt, config=types.GenerateContentConfig(response_mime_type="application/json", response_schema=list[FlashcardOutput], temperature=0.1))
                        cards_data = json.loads(res.text)
                        for c in cards_data:
                            f_clean = fix_sentence_case(normalize_whitespace(c["Front"]))
                            if f_clean.lower() not in all_generated_fronts:
                                c["Topic"], c["Subtopic"], c["Front"] = official_topic_id, "0", f_clean
                                topic_cards.append(c); all_generated_fronts.add(f_clean.lower())
                        batch_done = True; break
                    except Exception as e: logger.error(f"Batch error: {e}")
                if not batch_done: topic_success = False; break
            
            if topic_success:
                all_flashcards.extend(topic_cards)
                try: requests.post(APP_SCRIPT_URL, data=json.dumps({"action": "upload_flashcards", "app_name": app_name, "flashcards": topic_cards}), headers={'Content-Type': 'application/json'}, timeout=120)
                except: pass
            else: failed_any = True; break

        return {"status": "completed" if not failed_any else "failed", "flashcards_count": len(all_flashcards)}

    def run_loop(self, mode="all"):
        global logger
        logger = setup_logger(mode)
        logger.info(f"🧠 Worker {mode.upper()} Started")
        while True:
            try:
                resp = requests.post(APP_SCRIPT_URL, data=json.dumps({"action": "read_tasks"}), headers={'Content-Type': 'application/json'}, timeout=60)
                tasks = resp.json().get("tasks", []) if resp.ok else []
                for t in tasks:
                    app = str(t.get("appName", "")).strip()
                    app_id = str(t.get("appId", "") or t.get("databaseId", "")).strip()
                    res_status, gen_status = str(t.get("researchStatus", "")).lower(), str(t.get("generateStatus", "")).lower()
                    if (mode in ["all", "research"]) and (res_status in ["research", "pending"]):
                        requests.post(APP_SCRIPT_URL, data=json.dumps({"action":"update_status", "app_name":app, "column":"research", "status":"Pending"}), headers={'Content-Type': 'application/json'})
                        res = self.handle_research(app, t.get("targetExam", ""), t.get("examVendor", ""))
                        requests.post(APP_SCRIPT_URL, data=json.dumps({"action":"update_status", "app_name":app, "column":"research", "status":"Done" if not res["needs_more"] else "Fail"}), headers={'Content-Type': 'application/json'})
                    if (mode in ["all", "generate"]) and (gen_status in ["generate", "pending"]):
                        requests.post(APP_SCRIPT_URL, data=json.dumps({"action":"update_status", "app_name":app, "column":"generate", "status":"Pending"}), headers={'Content-Type': 'application/json'})
                        res = self.handle_generate(app, t.get("targetExam", ""), t.get("topicStructure", ""), dashboard_app_id=app_id)
                        requests.post(APP_SCRIPT_URL, data=json.dumps({"action":"update_status", "app_name":app, "column":"generate", "status":"Done" if res["flashcards_count"] > 0 else "Fail"}), headers={'Content-Type': 'application/json'})
            except Exception as e: logger.error(f"Loop error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["all", "research", "generate"], default="all")
    args = parser.parse_args()
    FlashcardAgent().run_loop(mode=args.mode)
