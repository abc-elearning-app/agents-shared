import os
import re
import json
import time
import hashlib
import logging
from typing import Any, Dict, List, Optional

import requests
from google import genai

# =========================================================
# SIMPLE .ENV LOADER
# =========================================================
def load_dotenv_simple(env_path: str = ".env") -> None:
    if not os.path.exists(env_path):
        return
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            raw = line.strip()
            if not raw or raw.startswith("#") or "=" not in raw:
                continue
            key, val = raw.split("=", 1)
            os.environ[key.strip()] = val.strip()

load_dotenv_simple()

# =========================================================
# CONFIG
# =========================================================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

WEB_APP_URL = "https://script.google.com/macros/s/AKfycbzX9ZvLEAZ0D2FRtMnH-97Fahbph6ZXHJFQ4gSj9eTtKIWaMki9USV7URD5w3UmQKfFPg/exec"
DASHBOARD_URL = WEB_APP_URL
UPLOAD_URL = WEB_APP_URL

INGEST_API = "http://117.7.0.31:5930/ingest-url"
SEARCH_API = "http://117.7.0.31:5930/search/chat"

POLL_INTERVAL_SECONDS = 60
HTTP_TIMEOUT_SHORT = 15
HTTP_TIMEOUT_MEDIUM = 45
HTTP_TIMEOUT_LONG = 120

BLOCKED_DOMAINS = {"baidu.com", "zhihu.com", "csdn.net", "bilibili.com", "weibo.com"}

client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler("worker_log.txt", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

# =========================================================
# HELPERS
# =========================================================
def normalize_app_name(app_name: str) -> str:
    return str(app_name or "").strip()

def normalize_whitespace(text: str) -> str:
    text = str(text or "").replace("\x00", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def truncate_text(text: str, max_chars: int) -> str:
    text = str(text or "")
    return text if len(text) <= max_chars else text[:max_chars]

def md5_hash(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()

def safe_json_loads(text: str) -> Optional[Any]:
    if not text: return None
    try: return json.loads(text)
    except:
        match = re.search(r"(\[.*\]|\{.*\})", text, re.DOTALL)
        if match:
            try: return json.loads(match.group(1))
            except: pass
    return None

def safe_request(method: str, url: str, json_payload: Optional[dict] = None, timeout: int = 30) -> Dict[str, Any]:
    try:
        if method.upper() == "GET": resp = requests.get(url, timeout=timeout)
        else: resp = requests.post(url, json=json_payload, timeout=timeout)
        resp.raise_for_status()
        content_type = resp.headers.get("Content-Type", "")
        if "application/json" in content_type:
            return {"ok": True, "data": resp.json()}
        return {"ok": True, "data": resp.text}
    except Exception as e:
        logging.error(f"HTTP {method} {url} failed: {e}")
        return {"ok": False, "error": str(e)}

# =========================================================
# APPS SCRIPT HELPERS
# =========================================================
def read_tasks_from_dashboard() -> List[dict]:
    res = safe_request("POST", DASHBOARD_URL, {"action": "read_tasks"})
    return res.get("data", {}).get("tasks", []) if res["ok"] else []

def update_sheet_status(app_name: str, column: str, status: str):
    safe_request("POST", DASHBOARD_URL, {"action": "update_status", "app_name": app_name, "column": column, "status": status})

def clear_sheet_command(app_name: str, column: str):
    safe_request("POST", DASHBOARD_URL, {"action": "clear_command", "app_name": app_name, "column": column})

def upload_flashcards_to_sheet(app_name: str, all_cards: List[dict]) -> Dict[str, Any]:
    return safe_request("POST", UPLOAD_URL, {"action": "upload_flashcards", "app_name": app_name, "sheet_name": app_name, "flashcards": all_cards}, timeout=HTTP_TIMEOUT_LONG)

# =========================================================
# INGEST + SEARCH HELPERS
# =========================================================
def ingest_url(url: str, app_name: str) -> Dict[str, Any]:
    payload = {"url": url, "app_name": app_name, "bucket_name": app_name, "index_document": True}
    return safe_request("POST", INGEST_API, payload, timeout=HTTP_TIMEOUT_LONG)

def search_chat(query: str, app_name: str, limit: int = 8, similarity_threshold: float = 0.2) -> str:
    payload = {"query": query, "app_name": app_name, "limit": limit, "similarity_threshold": similarity_threshold}
    result = safe_request("POST", SEARCH_API, json_payload=payload, timeout=HTTP_TIMEOUT_LONG)
    if not result["ok"]: return ""
    data = result.get("data", {})
    if isinstance(data, dict):
        for k in ["answer", "response", "result", "text", "content"]:
            if isinstance(data.get(k), str): return normalize_whitespace(data[k])
    return normalize_whitespace(data) if isinstance(data, str) else ""

# =========================================================
# SEARCH CANDIDATES (PHASE 1)
# =========================================================
def search_candidate_urls_from_web(target_exam: str, exam_vendor: str) -> List[str]:
    if not client: return []
    prompt = f"Search for direct PDF study guides and training materials for: {target_exam} ({exam_vendor}). Return ONLY direct PDF URLs."
    try:
        res = client.models.generate_content(model="gemini-2.0-flash", contents=prompt, config={"tools": [{"google_search": {}}]})
        urls = re.findall(r'https?://[^\s<>"]+?\.pdf(?:[?\w=&%-]+)?', res.text, re.IGNORECASE)
        return list(set(urls))
    except: return []

def phase_1_research(task: dict):
    app_name = normalize_app_name(task.get("appName"))
    target_exam = task.get("targetExam")
    exam_vendor = task.get("examVendor")
    logging.info(f"STARTING RESEARCH for {app_name}...")
    update_sheet_status(app_name, "research", "Pending")
    urls = search_candidate_urls_from_web(target_exam, exam_vendor)
    success_count = 0
    for url in urls:
        if ingest_url(url, app_name)["ok"]:
            success_count += 1
            logging.info(f"SUCCESSfully ingested: {url}")
        if success_count >= 15: break
    update_sheet_status(app_name, "research", "Done" if success_count > 0 else "Fail")
    clear_sheet_command(app_name, "research")

# =========================================================
# FLASHCARD GENERATION (PHASE 2)
# =========================================================
def parse_topic_structure(topic_structure: str) -> List[Dict[str, Any]]:
    lines = [line.strip() for line in str(topic_structure or "").splitlines() if line.strip()]
    topics = []
    current_topic = None
    for line in lines:
        if re.match(r"^\d+\.\s+", line):
            current_topic = {"id": re.search(r"^\d+", line).group(), "name": re.sub(r"^\d+\.\s*", "", line).strip(), "subtopics": []}
            topics.append(current_topic)
        elif re.match(r"^\d+\.\d+\.?\s+", line) and current_topic:
            current_topic["subtopics"].append({"id": re.search(r"^\d+\.\d+", line).group().split(".")[-1], "name": re.sub(r"^\d+\.\d+\.?\s*", "", line).strip()})
    return topics

def generate_flashcards_for_target(master_reference: str, topic_id: str, subtopic_id: str, target_name: str, target_count: int) -> List[dict]:
    if not client: return []
    prompt = f"Generate {target_count} flashcards for {target_name} (Topic {topic_id}, Subtopic {subtopic_id}).\n\nMASTER REFERENCE:\n{truncate_text(master_reference, 100000)}"
    try:
        res = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        return safe_json_loads(res.text) or []
    except: return []

def phase_2_generate(task: dict):
    app_name = normalize_app_name(task.get("appName"))
    topic_structure = task.get("topicStructure")
    update_sheet_status(app_name, "generate", "Pending")
    topics = parse_topic_structure(topic_structure)
    all_cards = []
    for topic in topics:
        for sub in topic["subtopics"]:
            ref = search_chat(f"Core concepts for {sub['name']} in {topic['name']}", app_name)
            cards = generate_flashcards_for_target(ref, topic["id"], sub["id"], sub["name"], 30)
            if isinstance(cards, list): all_cards.extend(cards)
    if all_cards:
        upload_flashcards_to_sheet(app_name, all_cards)
        update_sheet_status(app_name, "generate", "Done")
    else:
        update_sheet_status(app_name, "generate", "Fail")
    clear_sheet_command(app_name, "generate")

def main_loop():
    logging.info("Agent started.")
    while True:
        try:
            for task in read_tasks_from_dashboard():
                if task.get("researchStatus") == "Research": phase_1_research(task)
                if task.get("generateStatus") == "Generate": phase_2_generate(task)
        except Exception as e: logging.error(f"Loop error: {e}")
        time.sleep(POLL_INTERVAL_SECONDS)

if __name__ == "__main__":
    main_loop()
