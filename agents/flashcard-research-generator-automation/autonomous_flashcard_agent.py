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

class FlashcardOutput(BaseModel):
    Topic: str
    Subtopic: str
    Front: str
    Back: str

class ResearchEngine:
    BLOCKED_DOMAINS = ["baidu.com", "zhihu.com", "csdn.net", "bilibili.com", "weibo.com", "sogou.com", "360.cn", "douban.com", "toutiao.com", "jianshu.com"]
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

    def __init__(self, exam: str, vendor: str):
        self.exam, self.vendor = exam, vendor or ""
        self.registry = load_url_registry()
        self.tavily = TavilyClient(api_key=TAVILY_API_KEY) if TAVILY_API_KEY else None

    def search_web(self, query: str, max_results=30) -> list[str]:
        # NGUYÊN TẮC 4: RECENCY CHECK - Luôn tìm version mới nhất (mặc định 2026 cho năm hiện tại của hệ thống)
        current_year = "2026"
        
        # NGUYÊN TẮC 2: CẤU TRÚC QUERY TIÊU CHUẨN
        variations = [
            # Tầng 1: Official site query
            f'"{self.exam}" site:{self.vendor.lower() if self.vendor else ""}' if self.vendor else f'"{self.exam}" official blueprint',
            # Tầng 1 & 6: PDF Mining from authorities
            f'"{self.exam}" filetype:pdf {self.vendor}',
            f'"{query}" site:.gov OR site:.edu filetype:pdf',
            # Tầng 3: Recognized Exam Prep
            f'"{self.exam}" study guide {current_year}',
            f'"{query}" explanation "official"',
            # Tầng 4: Standards
            f'"{query}" technical standards documentation',
            # Verbatim phrase check (if query is specific)
            f'"{query}"'
        ]
        
        all_urls = set()
        
        # TAVILY - GỌI 1 LẦN DUY NHẤT ĐỂ TIẾT KIỆM TOKEN
        if self.tavily:
            # Câu lệnh tổng hợp tìm Blueprint và Manual (Dạng PDF - Gold Standard)
            tavily_query = f'"{self.exam}" official blueprint manual study guide filetype:pdf'
            try:
                res = self.tavily.search(query=tavily_query, search_depth="advanced", max_results=20)
                for r in res.get('results', []): all_urls.add(r['url'])
            except: pass

        for q in variations:
            # DuckDuckGo (Hỗ trợ tìm kiếm miễn phí)
            try:
                with DDGS() as ddgs:
                    for r in ddgs.text(q, max_results=10): all_urls.add(r['href'])
            except: pass

            # SearXNG (Hỗ trợ tìm kiếm miễn phí)
            for r in searxng_search(q, max_results=max_results): all_urls.add(r['url'])
            
        # NGUYÊN TẮC 1: LỌC QUA GATE 1 (Accessibility & Blocked Domains)
        valid_urls = []
        for url in all_urls:
            if any(blocked in url.lower() for blocked in self.BLOCKED_DOMAINS): continue
            valid_urls.append(url)
            
        return valid_urls

    def gate_8_execution_pipeline(self, url: str) -> dict:
        """
        NGUYÊN TẮC 1: PYRAMID NGUỒN (TIER CLASSIFICATION)
        """
        try:
            # GATE 1: Pre-upload accessibility check
            resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
            if not resp.ok: return None
        except: return None
        
        u = url.lower()
        score = 0.7 # Tier 3 default
        
        # TIER 1: Official Score 0.9
        if any(domain in u for domain in self.TIER_1_DOMAINS):
            score = 0.9
        # TIER 2: Recognized Prep Score 0.8
        elif any(domain in u for domain in self.TIER_2_DOMAINS):
            score = 0.8
            
        # Score Adjustments
        if u.endswith(".pdf"): score += 0.1 # NGUYÊN TẮC 6: PDF Mining - Gold Standard
        if any(x in u for x in ["blueprint", "objective", "syllabus"]): score += 0.05
        
        # Gate 3: Freshness & Gate 4: Quality (Cơ bản qua score)
        if score < 0.7: return None
        
        return {
            "url": url, 
            "score": round(score, 2), 
            "canonical_id": hashlib.md5(url.encode()).hexdigest(), 
            "format": "pdf" if u.endswith(".pdf") else "html"
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
        engine = ResearchEngine(target_exam, exam_vendor)
        raw_urls = engine.search_web(target_exam)
        logger.info(f"🌐 Found {len(raw_urls)} raw URLs, starting ingestion pipeline...")
        
        sources_ingested = []
        pdf_count = 0
        
        for url in raw_urls:
            if len(sources_ingested) >= 20: break
            approved = engine.gate_8_execution_pipeline(url)
            if approved:
                try:
                    if approved['format'] == 'pdf':
                        logger.info(f"📥 Attempting to upload PDF: {url}")
                        pdf_resp = requests.get(url, timeout=60)
                        if pdf_resp.ok:
                            upload_resp = requests.post(PDF_UPLOAD_API, files={'file': pdf_resp.content}, data={'app_name': app_name}, timeout=120)
                            if upload_resp.ok:
                                logger.info(f"✅ PDF Uploaded successfully: {url}")
                                sources_ingested.append(approved)
                                pdf_count += 1
                            else:
                                logger.warning(f"❌ PDF Upload failed (Status {upload_resp.status_code}): {url}")
                    else:
                        logger.info(f"🔗 Attempting to ingest URL: {url}")
                        ingest_resp = requests.post(INGEST_API, json={"url": url, "app_name": app_name, "bucket_name": app_name, "index_document": True}, timeout=120)
                        if ingest_resp.ok:
                            logger.info(f"✅ URL Ingested successfully: {url}")
                            sources_ingested.append(approved)
                        else:
                            logger.warning(f"❌ URL Ingest failed (Status {ingest_resp.status_code}): {url}")
                except Exception as e:
                    logger.error(f"⚠️ Error during ingestion of {url}: {e}")
        
        # Logic báo Done chặt chẽ hơn: Cần ít nhất 5 nguồn, trong đó khuyến khích có PDF
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
        total_items = len(parsed_items)
        
        for idx, item in enumerate(parsed_items):
            progress_msg = f"{idx+1}/{total_items}"
            logger.info(f"🔍 Processing {progress_msg}: {item['name']} (Parent: {item.get('parent_name')})")
            self.update_dashboard_status(app_name, "generate", "Pending")
            
            # --- CRITICAL MAPPING LOGIC (PART 1 DEFAULT) ---
            official_topic_id = "N/A"
            official_subtopic_id = "N/A" # This will hold the PART ID (Type 3)
            
            clean_item_name = re.sub(r"^(\d+\.)+\s+", "", item['name'].strip())
            
            # 1. Luôn tìm Topic ID (Type 1)
            parent_to_find = item['name'] if item['type'] == 1 else item.get('parent_name', 'General')
            clean_parent = re.sub(r"^(\d+\.)+\s+", "", parent_to_find.strip()).lower()
            
            for ct in cms_topics:
                if clean_parent in ct.get("name", "").lower() or ct.get("name", "").lower() in clean_parent:
                    official_topic_id = str(ct.get("id"))
                    break
            
            # 2. Nếu là Subtopic, tìm Part 1 (Type 3) của nó
            # Pattern: [Subtopic Name] + " 1"
            if item['type'] == 2:
                search_part_name = f"{clean_item_name} 1".lower()
                logger.info(f"🕵️ Searching for Part 1: '{search_part_name}' (type=3)")
                for cp in cms_parts:
                    if cp.get("type") == 3 and search_part_name == cp.get("name", "").lower():
                        official_subtopic_id = str(cp.get("id"))
                        logger.info(f"✅ Found Part 1 ID: {official_subtopic_id}")
                        break
                
                # Fallback: Nếu không khớp chính xác, tìm Part 1 có chứa tên Subtopic
                if official_subtopic_id == "N/A":
                    for cp in cms_parts:
                        if cp.get("type") == 3 and clean_item_name.lower() in cp.get("name", "").lower() and cp.get("name", "").strip().endswith(" 1"):
                            official_subtopic_id = str(cp.get("id"))
                            logger.info(f"✅ Fuzzy Matched Part 1: '{cp.get('name')}' (ID: {official_subtopic_id})")
                            break
            else:
                # Nếu Topic là leaf node, kiểm tra xem có Part 1 của Topic đó không
                search_part_name = f"{clean_item_name} 1".lower()
                for cp in cms_parts:
                    if cp.get("type") == 3 and search_part_name == cp.get("name", "").lower():
                        official_subtopic_id = str(cp.get("id"))
                        break

            if official_topic_id == "N/A":
                logger.error(f"❌ Could not find CMS Topic ID for: '{clean_parent}'")
            # -----------------------------------------------

            # Step 1: Automated Technical Retrieval & Context Optimization
            loop = asyncio.get_event_loop()
            context_text = ""
            search_query = f"Provide core definitions, frameworks, formulas, and key concepts specifically for {item['name']} - {item.get('parent_name', 'General')}."
            
            try:
                # API Execution & Strict Payload Limits (limit: 3, similarity_threshold: 0.4)
                resp = await loop.run_in_executor(self.executor, lambda: requests.post(
                    SEARCH_API, 
                    json={"query": search_query, "app_name": app_name, "limit": 3, "similarity_threshold": 0.4}, 
                    timeout=120
                ))
                if resp.ok: 
                    ans = resp.json().get("answer", "")
                    if "couldn't find any relevant documents" not in ans.lower():
                        # Master Reference Truncation: Strictly first 15,000 characters
                        context_text = ans[:15000]
            except: pass

            # Đặt KPI theo loại Node (Type 1: Topic -> 50, Type 2: Subtopic -> 30)
            kpi_count = 50 if item.get("type") == 1 else 30
            batch_size = kpi_count # Ép AI gen đủ luôn trong 1 lần để giảm request
            topic_cards, topic_success = [], True
            max_batches = 3 # Giảm số batch tối đa vì chúng ta đã yêu cầu đủ từ đầu
            current_batch = 0

            while len(topic_cards) < kpi_count and current_batch < max_batches:
                current_batch += 1
                current_goal = min(batch_size, kpi_count - len(topic_cards))
                if current_goal <= 0: break
                
                logger.info(f"📦 Topic/Subtopic Batch {current_batch}: Target {current_goal} cards (Total collected: {len(topic_cards)}/{kpi_count})")
                
                # Session-Based Deduplication (Exclusion List) for the current job
                exclusion_instruction = ""
                # Gộp cả topic_cards (trong topic này) và all_generated_fronts (toàn bộ app)
                current_exclusion_set = all_generated_fronts.union({c["Front"].lower() for c in topic_cards})
                
                if current_exclusion_set:
                    previously_generated_terms_list = ", ".join(list(current_exclusion_set))
                    logger.info(f"🚫 Injecting Exclusion List ({len(current_exclusion_set)} terms)")
                    exclusion_instruction = f"""
                    EXCLUSION LIST: You have already generated flashcards for the following terms: {previously_generated_terms_list}. 
                    CRITICAL RULE: You are STRICTLY FORBIDDEN from generating flashcards for these exact terms again. Furthermore, you MUST NOT generate ANY terms that are semantic duplicates, synonyms, or paraphrased versions of the terms in the exclusion list. Every newly generated term MUST introduce a completely unique and distinct educational concept.
                    """

                # Master Reference Synthesis per Topic/Subtopic
                prompt = f"""
                You are an Expert Learning Designer. Use the provided MASTER REFERENCE to extract flashcards for: {item['name']}
                
                MASTER REFERENCE (Source of Truth):
                {context_text}

                {exclusion_instruction}

                UNIVERSAL STANDARDS FOR "FRONT" TERM EXTRACTION:
                - RULE 1: THE ENTITY & TESTABILITY TEST (MOST IMPORTANT). 
                  The extracted term MUST be a specific, testable Knowledge Entity. It must be a specific Law, Protocol, Theorem, Technical Component, Medical Condition, or Academic Vocabulary (e.g., "Dram Shop Law", "TCP/IP Protocol", "Work Breakdown Structure", "Pythagorean Theorem").
                - RULE 2: THE UNIVERSAL "FLUFF & META" KILL LIST (ABSOLUTE BAN). 
                  IMMEDIATELY REJECT any term containing words like: 
                  * Meta/Exam: "Exam", "Format", "Chapter", "Course", "Handbook", "Passing Score".
                  * Vague Skills: "Skills", "Abilities", "Reasoning", "Strategies", "Thinking", "Aptitude".
                  * Empty Categories: "Introduction", "Overview", "Basics", "Concepts", "The Process".
                - RULE 3: SPECIFICITY & CONTEXT-INDEPENDENCE. 
                  The term MUST make complete sense on its own if picked up from the floor. Do not extract generic nouns. (e.g., "Azure Blob Storage" instead of "Storage").
                - RULE 4: NO ACTIONS OR QUESTIONS. 
                  DO NOT use conversational questions or instructional verbs. 
                  * Convert "How to mitigate risk" to "Risk Mitigation Techniques".
                  * Convert "What is a Variable" to "Algebraic Variable".
                - RULE 5: FORMATTING CONSTRAINT.
                  * Capitalization: Only capitalize the first letter of the entire term and any acronyms (e.g., "Engineering controls", "OSHA standards").
                  * Length: Strictly 1 to 8 words.

                STRICT RULES FOR "BACK":
                - Definition + 1 essential characteristic.
                - 1-2 concise sentences. No bullet points.
                - MathJax: Wrap in \\\\(..\\\\) with NO spaces. Use \\\\text{{}} for words.

                KPI: {current_goal} unique terms.
                Topic ID: {official_topic_id}, Subtopic: {official_subtopic_id}.
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
                            # Kiểm tra trùng lặp trong cả app và trong chính batch vừa gen
                            if f_clean not in all_generated_fronts and not any(tc["Front"].lower() == f_clean for tc in topic_cards):
                                if not any(x in f_clean for x in ["exam", "format", "score", "passing", "handbook", "chapter"]):
                                    c["Topic"], c["Subtopic"] = official_topic_id, official_subtopic_id
                                    topic_cards.append(c)
                                    # Cập nhật all_generated_fronts ngay lập tức để batch sau biết
                                    all_generated_fronts.add(f_clean)
                        batch_done = True; break
                    except Exception as e:
                        if "429" in str(e):
                            # ĐIỀU TIẾT LUỒNG: Nghỉ ít nhất 2 phút nếu bị rate limit
                            delay_429 = 120 + random.uniform(5.0, 15.0)
                            logger.error(f"🚨 RATE LIMIT HIT (429). Throttling active: Sleeping {delay_429:.2f}s for quota recovery...")
                            await asyncio.sleep(delay_429)
                        else:
                            logger.error(f"Batch error: {e}")
                            await asyncio.sleep(5)
                if not batch_done: topic_success = False; break
            
            if topic_success:
                all_flashcards.extend(topic_cards)
                try: requests.post(APP_SCRIPT_URL, data=json.dumps({"action": "upload_flashcards", "app_name": app_name, "flashcards": topic_cards}), headers={'Content-Type': 'application/json'}, timeout=120)
                except: pass
            else: failed_any = True; break

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
