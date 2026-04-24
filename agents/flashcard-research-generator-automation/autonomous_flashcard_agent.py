import os
import re
import json
import time
import logging
import hashlib
import requests
import argparse
import asyncio
import random
from concurrent.futures import ThreadPoolExecutor
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

GEMINI_API_KEYS = [k.strip() for k in os.getenv("GEMINI_API_KEY", "").split(",") if k.strip()]
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

def fix_mathjax(text: str) -> str:
    if not text: return ""
    # Chuyển $..$ sang \(..\) nếu có
    text = re.sub(r"\$(.*?)\$", r"\\(\1\\)", text)
    # Xóa khoảng trắng sát thẻ \( và \)
    text = text.replace("\\( ", "\\(").replace(" \\)", "\\)")
    return text

def apply_term_constraints(text: str, is_front: bool = True) -> str:
    if not text: return ""
    
    # 1. Xử lý riêng cho Front (Noun Phrases, xóa meta/questions)
    if is_front:
        text = text.replace("?", "").strip()
        patterns = [
            r"^(What is|What are|Define|Explain|Describe|How to|Why do|Where is|Which of the following is|Which is)\s+",
            r"^(The|A|An)\s+" 
        ]
        for p in patterns:
            text = re.sub(p, "", text, flags=re.IGNORECASE)
    
    # 2. Quy tắc viết hoa STRICT (Front & Back)
    # Bộ từ điển Acronyms phổ biến và các case đặc biệt
    acronym_list = {
        "OSHA", "HIPAA", "PPE", "CDC", "CLSI", "HIV", "HBV", "HCV", "EDTA", "SST", "PST", "CBC", "PT", "PTT", "INR", "GTT", "HCG", "PKU", "ABG", "TDM", "SDS", "MSDS", "RBC", "WBC", "TCP/IP", "IaaS", "PaaS", "SaaS", "RBAC", "VPC", "VNET", "SOHO", "DNS", "DHCP", "FTP", "HTTP", "HTTPS", 
        "FAA", "sUAS", "ATC", "AGL", "MSL", "NOTAM", "METAR", "TAF", "VFR", "IFR", "PIC", "VO", "VLOS", "BVLOS", "CRM", "ICAO", "UA", "CS", "OSI", "LAN", "WAN", "PAN", "WLAN", "SATA", "NVME", "CPU", "GPU", "RAM", "ROM", "BIOS", "UEFI", "POST", "MAC", "IP", "UDP", "TCP", "ICMP", "ARP",
        "NREMT", "EMS", "EMT", "CPR", "AED", "GCS", "AVPU", "ABC", "BSI", "SAMPLE", "OPQRST", "DCAP-BTLS", "MCI", "ICS", "NIMS", "HAZMAT", "NRB", "BVM", "CPAP", "PEEP", "CHF", "COPD", "ACS", "TIA", "CVA", "ICP", "CSF", "ALOC", "LOC"
    }
    # Tạo set lowercase để tra cứu nhanh
    acronym_map = {a.lower(): a for a in acronym_list}
    
    # Bảo vệ các khối MathJax
    math_blocks = re.findall(r"\\\(.*?\\\)", text)
    placeholder = "___MATH_BLOCK___"
    temp_text = re.sub(r"\\\(.*?\\\)", placeholder, text)
    
    words = temp_text.split()
    if not words: return ""
    
    new_words = []
    math_idx = 0
    for i, word in enumerate(words):
        if placeholder in word:
            actual_math = math_blocks[math_idx]
            math_idx += 1
            new_words.append(word.replace(placeholder, actual_math))
            continue
            
        # Tách từ để nhận diện (loại bỏ dấu câu sát từ)
        clean_match = re.search(r"[\w\d\-/]+", word)
        if not clean_match:
            new_words.append(word.lower())
            continue
            
        clean = clean_match.group()
        
        # Heuristic nhận diện Acronym:
        # - Có trong danh sách bảo vệ
        # - AI đã viết hoa toàn bộ và dài >= 2 ký tự (ví dụ: NASA)
        # - Có chứa số (ví dụ: 5G, 4G, IPv6)
        is_acronym = False
        target_version = clean # Mặc định
        
        if clean.lower() in acronym_map:
            is_acronym = True
            target_version = acronym_map[clean.lower()]
        elif clean.isupper() and len(clean) >= 2:
            is_acronym = True
            target_version = clean
        elif any(c.isdigit() for c in clean) and len(clean) >= 2:
            is_acronym = True
            target_version = clean.upper() # Ví dụ: ipv6 -> IPV6 (hoặc giữ nguyên nếu muốn)
            # Fix riêng cho IPv4/v6 nếu cần
            if "ipv" in clean.lower():
                target_version = "IPv" + clean.lower().split("ipv")[-1]
            
        if is_acronym:
            new_words.append(word.replace(clean, target_version))
        elif i == 0:
            # Chữ cái đầu tiên của chuỗi viết hoa, còn lại viết thường
            new_words.append(word[0].upper() + word[1:].lower())
        else:
            new_words.append(word.lower())
            
    return " ".join(new_words)


class ScopeMap(BaseModel):
    included_skills: list[str]
    included_concepts: list[str]

class FlashcardOutput(BaseModel):

    Topic: str
    Subtopic: str
    Front: str
    Back: str
    Reference: str

class ResearchEngine:
    BLOCKED_DOMAINS = [
        "baidu.com", "zhihu.com", "csdn.net", "bilibili.com", "weibo.com", "sogou.com", "360.cn", 
        "douban.com", "toutiao.com", "jianshu.com", "quizlet.com", "coursehero.com", "chegg.com", 
        "brainly.com", "scribd.com", "reddit.com", "facebook.com"
    ]
    SUPPORTED_FORMATS = [".pdf", ".md", ".txt", ".text", ".json", ".docx", ".html", ".htm"]
    
    # Tier 1: Official Publishers & Authorities
    TIER_1_DOMAINS = [
        ".gov", ".mil", ".edu", "comptia.org", "isc2.org", "pmi.org", "aws.amazon.com", "microsoft.com", 
        "cisco.com", "oracle.com", "faa.gov", "nist.gov", "iso.org", "ieee.org", "aicpa.org"
    ]
    # Tier 2: Recognized Exam Prep & Support
    TIER_2_DOMAINS = [
        "professormesser.com", "pilotinstitute.com", "whizlabs.com", "pluralsight.com", "github.com",
        "wiley.com", "kaplan.com", "pearson.com", "sybex.com", "boson.com"
    ]
    
    VENDOR_DOMAIN_MAP = {
        "CompTIA": "comptia.org", "PMI": "pmi.org", "ISC2": "isc2.org", "Cisco": "cisco.com",
        "AWS": "aws.amazon.com", "Microsoft": "microsoft.com", "Google Cloud": "cloud.google.com",
        "Oracle": "oracle.com", "FAA": "faa.gov", "NREMT": "nremt.org",
        "ServSafe": "servsafe.com", "National Restaurant Association": "restaurant.org", "OSHA": "osha.gov",
        "Criteria": "criteriacorp.com"
    }

    def __init__(self, target_exam: str, exam_vendor: str, app_name: str = ""):
        self.identity = self.normalize_exam_identity(target_exam, exam_vendor, app_name)
        self.exam = self.identity["official_name"]
        self.vendor = self.identity["vendor"]
        self.registry = load_url_registry()
        self.tavily = TavilyClient(api_key=TAVILY_API_KEY) if TAVILY_API_KEY else None
        logger.info(f"🧬 Research Engine Init - Identity: {json.dumps(self.identity, indent=2)}")

    def normalize_exam_identity(self, target_exam: str, exam_vendor: str, app_name: str) -> dict:
        # Priority: target_exam > exam_vendor > app_name
        raw_exam = target_exam.strip() if target_exam and target_exam.strip() else app_name.strip()
        vendor = exam_vendor.strip() if exam_vendor and exam_vendor.strip() else ""
        
        # Vendor normalization: Remove Corp, Inc, LLC, Ltd, Company, Group
        vendor_normalized = re.sub(r'(?i)\b(corp|inc|llc|ltd|company|group)\b', '', vendor).strip()
        
        # Extract exam code (e.g. N10-009, SY0-701, AZ-900)
        code_match = re.search(r'\b([A-Z0-9]{2,}-\d{3,}|[A-Z]{1,2}\d{3})\b', raw_exam)
        exam_code = code_match.group(1) if code_match else ""
        
        official_name = raw_exam
        if exam_code and exam_code in official_name:
            official_name = official_name.replace(exam_code, "").strip(" ()-")
            
        aliases = [official_name]
        if "plus" in official_name.lower(): aliases.append(official_name.lower().replace("plus", "+"))
        if "+" in official_name: aliases.append(official_name.replace("+", " Plus"))
        if exam_code: aliases.append(exam_code)
        
        # Extract acronym if present in parentheses or looks like one
        acronym_match = re.search(r'\b([A-Z]{2,6})\b', official_name)
        acronym = acronym_match.group(1) if acronym_match else ""
        
        # Short Acronym Protection (CRITICAL)
        # If acronym length <= 5, we MUST combine it with vendor or full name in searches later.
        
        vendor_domain = ""
        for v_key, domain in self.VENDOR_DOMAIN_MAP.items():
            if v_key.lower() in vendor.lower() or v_key.lower() in raw_exam.lower():
                vendor_domain = domain
                break
                
        return {
            "official_name": official_name,
            "acronym": acronym,
            "vendor": vendor_normalized if vendor_normalized else vendor,
            "exam_code": exam_code,
            "aliases": list(set(aliases)),
            "vendor_domain": vendor_domain
        }

    def search_web(self, query: str = "", app_name: str = "general", pass_num=1) -> list[dict]:
        id = self.identity
        templates = []
        
        if pass_num == 1:
            templates = [
                f'"{id["vendor"]}" "{id["official_name"]}" exam objectives PDF',
                f'"{id["official_name"]}" official exam guide PDF',
                f'"{id["official_name"]}" candidate handbook PDF',
                f'"{id["official_name"]}" exam content outline PDF',
                f'"{id["official_name"]}" blueprint PDF'
            ]
            if id["vendor_domain"]:
                templates.append(f'site:{id["vendor_domain"]} "{id["official_name"]}"')
            if id["exam_code"]:
                templates.append(f'"{id["exam_code"]}" exam objectives PDF')
                templates.append(f'"{id["vendor"]}" "{id["exam_code"]}" PDF')
        else:
            templates = [
                f'"{id["official_name"]}" official study guide',
                f'"{id["official_name"]}" coursebook PDF',
                f'"{id["official_name"]}" domains objectives',
                f'"{id["official_name"]}" syllabus'
            ]
            for alias in id["aliases"]:
                templates.append(f'"{alias}" manual study guide PDF')

        all_results = []
        seen_urls = set()
        
        if self.tavily and pass_num == 1:
            t_query = f'"{id["official_name"]}" {id["exam_code"]} official blueprint manual PDF'
            try:
                res = self.tavily.search(query=t_query, search_depth="basic", max_results=20)
                for r in res.get('results', []):
                    if r['url'] not in seen_urls:
                        all_results.append({"url": r['url'], "title": r.get('title', ''), "snippet": r.get('content', '')})
                        seen_urls.add(r['url'])
            except: pass

        for q in templates[:12]:
            try:
                with DDGS() as ddgs:
                    for r in ddgs.text(q, max_results=5):
                        url = r.get('href')
                        if url and url not in seen_urls:
                            all_results.append({"url": url, "title": r.get('title', ''), "snippet": r.get('body', '')})
                            seen_urls.add(url)
            except: pass
            
            for r in searxng_search(q, max_results=5):
                if r['url'] not in seen_urls:
                    all_results.append(r)
                    seen_urls.add(r['url'])
            
        return all_results

    def gate_8_execution_pipeline(self, result: dict) -> dict:
        url = result.get("url", "").lower()
        title = result.get("title", "").lower()
        snippet = result.get("snippet", "").lower()
        id = self.identity
        
        if any(blocked in url for blocked in self.BLOCKED_DOMAINS): return None
        
        try:
            resp = requests.get(result["url"], headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            if not resp.ok: return None
        except: return None
        
        score = 0.0
        
        if (id["vendor_domain"] and id["vendor_domain"] in url) or any(d in url for d in [".gov", ".edu", ".mil"]):
            score += 0.4
        elif any(d in url for d in self.TIER_1_DOMAINS): score += 0.4
        elif any(d in url for d in self.TIER_2_DOMAINS): score += 0.3
            
        if id["exam_code"] and (id["exam_code"].lower() in url or id["exam_code"].lower() in title):
            score += 0.3
            
        if id["official_name"].lower() in url or id["official_name"].lower() in title:
            score += 0.4
        elif any(a.lower() in url or a.lower() in title for a in id["aliases"]):
            score += 0.2
            
        if url.endswith(".pdf") or any(x in url or x in title for x in ["blueprint", "objective", "handbook", "syllabus", "outline"]):
            score += 0.2
            
        if any(yr in title or yr in snippet for yr in ["2024", "2025", "2026"]):
            score += 0.2
            
        if id["vendor"] and id["vendor"].lower() not in url and id["vendor"].lower() not in title and id["vendor"].lower() not in snippet:
            score -= 0.6
            
        final_score = round(score, 2)
        if final_score < 0.6: return None
        
        return {
            "url": result["url"], 
            "score": final_score, 
            "canonical_id": hashlib.md5(result["url"].encode()).hexdigest(), 
            "format": "pdf" if url.endswith(".pdf") else "html"
        }

class FlashcardAgent:
    def __init__(self):
        # Khởi tạo danh sách clients cho tất cả API keys
        self.clients = [genai.Client(api_key=k) for k in GEMINI_API_KEYS]
        self.current_client_idx = 0
        self.key_cooldowns = [0.0] * len(GEMINI_API_KEYS)
        
        self.executor = ThreadPoolExecutor(max_workers=20)
        # THROTTLING: Chỉ cho phép 1 request duy nhất được thực hiện tại một thời điểm trên toàn hệ thống
        self.semaphore = asyncio.Semaphore(1) 
        self.active_jobs = set()

    async def get_next_available_client(self):
        """Logic luân phiên chuyển Key khi gặp 429 hoặc xoay vòng"""
        start_idx = self.current_client_idx
        while True:
            # Nếu Key hiện tại không trong thời gian cooldown
            if time.time() > self.key_cooldowns[self.current_client_idx]:
                return self.clients[self.current_client_idx]
            
            # Chuyển sang idx tiếp theo
            self.current_client_idx = (self.current_client_idx + 1) % len(self.clients)
            
            # Nếu đã duyệt qua tất cả các Key và đều đang cooldown
            if self.current_client_idx == start_idx:
                min_cooldown = min(self.key_cooldowns)
                wait_time = max(0.1, min_cooldown - time.time())
                logger.warning(f"⏳ All API keys are in cooldown. Waiting {wait_time:.2f}s...")
                await asyncio.sleep(wait_time)

    async def rate_limited_gen(self, prompt, schema):
        """
        Hàm bao bọc để điều tiết luồng API (Throttling) + API Rotation
        """
        async with self.semaphore:
            keys_attempted = 0
            while keys_attempted < len(self.clients):
                client = await self.get_next_available_client()
                try:
                    res = await asyncio.get_event_loop().run_in_executor(
                        self.executor,
                        lambda c=client: c.models.generate_content(
                            model=GEMINI_MODEL,
                            contents=prompt,
                            config=types.GenerateContentConfig(
                                response_mime_type="application/json",
                                response_schema=schema,
                                temperature=0.1
                            )
                        )
                    )
                    # THROTTLING: Nghỉ bắt buộc 30 giây sau mỗi lần gọi thành công
                    await asyncio.sleep(30)
                    return res
                except Exception as e:
                    if "429" in str(e):
                        # QUOTA RECOVERY: Đánh dấu Key này bị hỏng trong 5 phút
                        self.key_cooldowns[self.current_client_idx] = time.time() + 300
                        logger.error(f"🚨 API Key {self.current_client_idx+1} hit 429. Switching key...")
                        # Chuyển idx ngay lập tức để vòng lặp sau dùng key mới
                        self.current_client_idx = (self.current_client_idx + 1) % len(self.clients)
                        keys_attempted += 1
                        continue
                    raise e
            
            # Nếu tất cả Key đều đạt giới hạn
            raise Exception("All API keys reached limit. Quota exhausted.")
    def update_dashboard_status(self, app_name: str, column: str, status: str):
        try:
            payload = {"action": "update_status", "app_name": app_name, "column": column, "status": status}
            resp = requests.post(APP_SCRIPT_URL, data=json.dumps(payload), headers={'Content-Type': 'application/json'}, allow_redirects=True, timeout=30)
            logger.info(f"📊 Dashboard Status Updated ({column}): {status} | Response: {resp.text}")
        except Exception as e:
            logger.error(f"❌ Failed to update dashboard status: {e}")

    def handle_research(self, app_name: str, target_exam: str, exam_vendor: str) -> dict:
        logger.info(f"🚀 [RESEARCH] Start for {app_name} (Exam: {target_exam}, Vendor: {exam_vendor})")
        engine = ResearchEngine(target_exam, exam_vendor, app_name)
        
        sources_ingested = []
        pdf_count = 0
        
        def process_batch(results):
            nonlocal pdf_count
            ingested_count = 0
            for res in results:
                if len(sources_ingested) >= 20: break
                if any(s['url'] == res['url'] for s in sources_ingested): continue
                
                approved = engine.gate_8_execution_pipeline(res)
                if approved:
                    try:
                        if approved['format'] == 'pdf':
                            logger.info(f"📥 Downloading PDF: {res['url']}")
                            pdf_resp = requests.get(res['url'], headers={"User-Agent": "Mozilla/5.0"}, timeout=120)
                            if pdf_resp.ok:
                                clean_filename = f"{hashlib.md5(res['url'].encode()).hexdigest()}.pdf"
                                upload_resp = requests.post(PDF_UPLOAD_API, files={'file': (clean_filename, pdf_resp.content, 'application/pdf')}, data={'app_name': app_name, 'bucket_name': app_name}, timeout=180)
                                if upload_resp.ok:
                                    logger.info(f"✅ PDF Uploaded: {res['url']}")
                                    sources_ingested.append(approved)
                                    pdf_count += 1
                                    ingested_count += 1
                        else:
                            logger.info(f"🔗 Ingesting URL: {res['url']}")
                            ingest_resp = requests.post(INGEST_API, json={"url": res['url'], "app_name": app_name, "bucket_name": app_name, "index_document": True}, timeout=120)
                            if ingest_resp.ok:
                                logger.info(f"✅ URL Ingested: {res['url']}")
                                sources_ingested.append(approved)
                                ingested_count += 1
                    except Exception as e: logger.error(f"⚠️ Error ingesting {res['url']}: {e}")
            return ingested_count

        # Pass 1: Primary Search
        results1 = engine.search_web(app_name=app_name, pass_num=1)
        logger.info(f"🌐 Pass 1: Found {len(results1)} potential URLs")
        process_batch(results1)
        
        # Pass 2: Fallback
        if len(sources_ingested) < 5:
            logger.info(f"⚠️ Only {len(sources_ingested)} sources found. Running second pass...")
            results2 = engine.search_web(app_name=app_name, pass_num=2)
            process_batch(results2)
        
        success_criteria = len(sources_ingested) >= 5
        logger.info(f"🏁 [RESEARCH] Finished for {app_name}. Total: {len(sources_ingested)} (PDFs: {pdf_count})")
        
        return {
            "status": "research_completed", 
            "app_name": app_name, 
            "needs_more": not success_criteria,
            "pdf_count": pdf_count,
            "total_count": len(sources_ingested)
        }

    async def handle_generate(self, app_name: str, target_exam: str, topic_structure: str, dashboard_app_id: str = "") -> dict:
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

        # Parse Structure & Remove Prefixes (e.g. 1.1, 2.)
        lines = [l.strip() for l in topic_structure.splitlines() if l.strip()]
        parsed_items, current_topic_name = [], "General"
        
        raw_structure = []
        for line in lines:
            core_match = re.match(r"^(\d+-\d+):\s+(.*)$", line)
            sub_match = re.match(r"^(\d+)\.(\d+)\.?\s+(.*)$", line)
            top_match = re.match(r"^(\d+)\.?\s+(.*)$", line)
            
            if core_match:
                current_topic_name = re.sub(r"^(\d+\.)+\s+", "", line.strip())
                raw_structure.append({"type": 1, "name": current_topic_name, "parent": None})
            elif sub_match:
                raw_structure.append({"type": 2, "name": re.sub(r"^(\d+\.)+\s+", "", sub_match.group(3).strip()), "parent": current_topic_name})
            elif top_match:
                current_topic_name = re.sub(r"^(\d+\.)+\s+", "", top_match.group(2).strip())
                raw_structure.append({"type": 1, "name": current_topic_name, "parent": None})
        
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
        total_items = len(parsed_items)

        # --- STEP 1: Blueprint Discovery ---
        loop = asyncio.get_event_loop()
        blueprint_context = ""
        try:
            bp_query = f"Find the official exam blueprint, exam objectives, skills outline, domain outline, or table of contents for {target_exam}."
            bp_resp = await loop.run_in_executor(self.executor, lambda: requests.post(
                SEARCH_API, json={"query": bp_query, "app_name": app_name, "limit": 5, "similarity_threshold": 0.3}, timeout=120
            ))
            if bp_resp.ok:
                ans = bp_resp.json().get("answer", "")
                if "couldn't find" not in ans.lower():
                    blueprint_context = ans[:8000]
        except: pass
        
        for idx, item in enumerate(parsed_items):
            progress_msg = f"{idx+1}/{total_items}"
            logger.info(f"🔍 Processing {progress_msg}: {item['name']} (Parent: {item.get('parent_name')})")
            self.update_dashboard_status(app_name, "generate", "Pending")
            
            # --- CRITICAL MAPPING LOGIC (PART 1 DEFAULT) ---
            official_topic_id = "N/A"
            official_subtopic_id = "N/A"
            
            clean_item_name = re.sub(r"\s+", " ", item['name']).lower()
            parent_to_find = item['name'] if item['type'] == 1 else item.get('parent_name', 'General')
            clean_parent = re.sub(r"\s+", " ", parent_to_find).lower()
            
            for ct in cms_topics:
                cms_t_name = re.sub(r"\s+", " ", ct.get("name", "")).lower()
                if clean_parent == cms_t_name or clean_parent in cms_t_name or cms_t_name in clean_parent:
                    official_topic_id = str(ct.get("id"))
                    break
            
            # Subtopic (Part 1 mapping)
            if item['type'] == 2:
                search_part_name = f"{clean_item_name} 1"
                for cp in cms_parts:
                    cms_p_name = re.sub(r"\s+", " ", cp.get("name", "")).lower()
                    if cp.get("type") == 3 and search_part_name == cms_p_name:
                        official_subtopic_id = str(cp.get("id"))
                        break
                if official_subtopic_id == "N/A":
                    for cp in cms_parts:
                        if cp.get("type") == 3 and clean_item_name.lower() in cp.get("name", "").lower() and cp.get("name", "").strip().endswith(" 1"):
                            official_subtopic_id = str(cp.get("id"))
                            break
            else:
                search_part_name = f"{clean_item_name} 1".lower()
                for cp in cms_parts:
                    if cp.get("type") == 3 and search_part_name == cp.get("name", "").lower():
                        official_subtopic_id = str(cp.get("id"))
                        break

            # --- STEP 2: Topic Scope Mapping ---
            scope_skills = []
            if blueprint_context:
                scope_prompt = f"Based on the following blueprint, extract the included skills and concepts specifically for the topic: '{item['name']}'. Blueprint: {blueprint_context[:3000]}"
                try:
                    scope_res = await self.rate_limited_gen(scope_prompt, ScopeMap)
                    scope_map = json.loads(scope_res.text)
                    scope_skills = scope_map.get("included_skills", []) + scope_map.get("included_concepts", [])
                except Exception as e:
                    logger.error(f"Scope mapping error: {e}")
            
            if not scope_skills:
                scope_skills = [item['name']]

            # --- STEP 3: Blueprint-Aligned Retrieval ---
            knowledge_reference = ""
            for skill in scope_skills[:3]:
                s_q = f"{skill} {target_exam} {item['name']}"
                try:
                    r = await loop.run_in_executor(self.executor, lambda sq=s_q: requests.post(SEARCH_API, json={"query": sq, "app_name": app_name, "limit": 3, "similarity_threshold": 0.3}, timeout=60))
                    if r.ok:
                        knowledge_reference += r.json().get("answer", "") + "\n"
                except: pass

            context_text = f"SCOPE:\n{scope_skills}\n\nKNOWLEDGE:\n{knowledge_reference[:10000]}"

            kpi_count = 50 if item.get("type") == 1 else 30
            batch_size = kpi_count
            topic_cards, topic_success = [], True
            max_batches = 3
            current_batch = 0

            while len(topic_cards) < kpi_count and current_batch < max_batches:
                current_batch += 1
                current_goal = min(batch_size, kpi_count - len(topic_cards))
                if current_goal <= 0: break
                
                logger.info(f"📦 Topic/Subtopic Batch {current_batch}: Target {current_goal} cards (Total collected: {len(topic_cards)}/{kpi_count})")
                
                exclusion_instruction = ""
                current_exclusion_set = all_generated_fronts.union({c["Front"].lower() for c in topic_cards})
                
                if current_exclusion_set:
                    previously_generated_terms_list = ", ".join(list(current_exclusion_set)[:200])
                    logger.info(f"🚫 Injecting Exclusion List ({len(current_exclusion_set)} terms)")
                    exclusion_instruction = f"EXCLUSION LIST: Do NOT generate flashcards for these terms or their synonyms: {previously_generated_terms_list}."

                prompt = f"""You are an Expert Learning Designer. Use the MASTER REFERENCE to extract flashcards for: {item['name']}.
MASTER REFERENCE:
{context_text}

{exclusion_instruction}

RULES FOR "FRONT":
- 1 to 8 words. MUST be a specific, testable knowledge entity.
- NO actions or questions. Only capitalize the FIRST letter or acronyms.
- NO fluff/meta terms like "Exam", "Format", "Process".

RULES FOR "BACK":
- Definition + 1 essential characteristic. 1-2 sentences. 20-40 words total.
- NO bullet points or line breaks.
- MathJax REQUIRED: Wrap formulas in \\(..\\) with NO spaces. Use \\text{{}} for words inside formulas.
- Do NOT say "according to the source".

KPI: {current_goal} unique terms.
"""
                
                batch_done = False
                for attempt in range(20): 
                    try:
                        if attempt > 0:
                            delay = (2 ** attempt) + random.uniform(0.5, 2.0)
                            logger.warning(f"🔄 Retry attempt {attempt}. Sleeping {delay:.2f}s...")
                            await asyncio.sleep(delay)
                            
                        res = await self.rate_limited_gen(prompt, list[FlashcardOutput])
                        cards_data = json.loads(res.text)
                        
                        for c in cards_data:
                            c["Front"] = apply_term_constraints(fix_mathjax(normalize_whitespace(c["Front"])), is_front=True)
                            c["Back"] = apply_term_constraints(fix_mathjax(normalize_whitespace(c["Back"])), is_front=False)
                            
                            f_clean = c["Front"].lower()
                            if f_clean not in all_generated_fronts and not any(tc["Front"].lower() == f_clean for tc in topic_cards):
                                if not any(x in f_clean for x in ["exam", "format", "score", "passing", "handbook", "chapter"]):
                                    c["Topic"], c["Subtopic"] = official_topic_id, official_subtopic_id
                                    topic_cards.append(c)
                                    all_generated_fronts.add(f_clean)
                        batch_done = True; break
                    except Exception as e:
                        if "429" in str(e):
                            delay_429 = 120 + random.uniform(5.0, 15.0)
                            logger.error(f"🚨 RATE LIMIT HIT (429). Sleeping {delay_429:.2f}s...")
                            await asyncio.sleep(delay_429)
                        else:
                            logger.error(f"Batch error: {e}")
                            await asyncio.sleep(5)
                if not batch_done: topic_success = False; break
            
            if topic_success:
                for tc in topic_cards:
                    tc["Topic"] = str(official_topic_id)
                    tc["Subtopic"] = str(official_subtopic_id)
                all_flashcards.extend(topic_cards)
            else:
                failed_any = True
                break

        if all_flashcards and not failed_any:
            try:
                logger.info(f"📤 FINAL UPLOAD: Sending {len(all_flashcards)} flashcards to Google Sheets for {app_name}")
                payload = {"action": "upload_flashcards", "app_name": app_name, "flashcards": all_flashcards}
                requests.post(APP_SCRIPT_URL, data=json.dumps(payload), headers={'Content-Type': 'application/json'}, timeout=180)
            except Exception as e:
                logger.error(f"❌ Final Upload failed: {e}")

        return {"status": "completed" if not failed_any else "failed", "flashcards_count": len(all_flashcards)}

    async def run_job(self, app_name, target_exam, exam_vendor, topic_structure, app_id, task_type):
        job_id = f"{app_name}_{task_type}"
        if job_id in self.active_jobs: return
        self.active_jobs.add(job_id)
        logger.info(f"🆕 Job Started: {job_id}")
        loop = asyncio.get_event_loop()
        try:
            if task_type == "research":
                await loop.run_in_executor(self.executor, self.update_dashboard_status, app_name, "research", "Pending")
                res = await loop.run_in_executor(self.executor, self.handle_research, app_name, target_exam, exam_vendor)
                await loop.run_in_executor(self.executor, self.update_dashboard_status, app_name, "research", "Done" if not res["needs_more"] else "Fail")
            elif task_type == "generate":
                await loop.run_in_executor(self.executor, self.update_dashboard_status, app_name, "generate", "Pending")
                res = await self.handle_generate(app_name, target_exam, topic_structure, dashboard_app_id=app_id)
                await loop.run_in_executor(self.executor, self.update_dashboard_status, app_name, "generate", "Done" if res["flashcards_count"] > 0 else "Fail")
        except Exception as e:
            logger.error(f"❌ Job {job_id} failed: {e}")
        finally:
            self.active_jobs.remove(job_id)
            logger.info(f"🔚 Job Finished: {job_id}")

    async def run_loop(self, mode="all"):
        global logger
        logger = setup_logger(mode)
        logger.info(f"🧠 Worker {mode.upper()} Started (Parallel Mode)")
        loop = asyncio.get_event_loop()
        while True:
            try:
                resp = await loop.run_in_executor(self.executor, lambda: requests.post(APP_SCRIPT_URL, data=json.dumps({"action": "read_tasks"}), headers={'Content-Type': 'application/json'}, timeout=60))
                tasks = resp.json().get("tasks", []) if resp.ok else []
                for t in tasks:
                    app = str(t.get("appName", "")).strip()
                    app_id = str(t.get("appId", "") or t.get("databaseId", "")).strip()
                    res_status, gen_status = str(t.get("researchStatus", "")).lower(), str(t.get("generateStatus", "")).lower()
                    
                    target_exam = t.get("targetExam", "")
                    exam_vendor = t.get("examVendor", "")
                    topic_structure = t.get("topicStructure", "")

                    if (mode in ["all", "research"]) and (res_status in ["research", "pending"]):
                        asyncio.create_task(self.run_job(app, target_exam, exam_vendor, topic_structure, app_id, "research"))
                    
                    if (mode in ["all", "generate"]) and (gen_status in ["generate", "pending"]):
                        asyncio.create_task(self.run_job(app, target_exam, exam_vendor, topic_structure, app_id, "generate"))
            except Exception as e: logger.error(f"Loop error: {e}")
            await asyncio.sleep(20)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["all", "research", "generate"], default="all")
    args = parser.parse_args()
    agent = FlashcardAgent()
    asyncio.run(agent.run_loop(mode=args.mode))
