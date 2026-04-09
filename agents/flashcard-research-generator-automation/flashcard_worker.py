import requests
import json
import time
import sys
import subprocess
import os

# --- CẤU HÌNH BẢO MẬT (Lấy từ Project Memory) ---
SHEET_URL = "https://script.google.com/macros/s/AKfycbwM_sk8-VNktBMybaRcoqTnqLTat1XVDtDUklQ-e0ZM-wbVZqFR2P3Ah5LM9gfFRX6P/exec"
INGEST_API = "http://117.7.0.31:5930/ingest-url"
SEARCH_API = "http://117.7.0.31:5930/search/chat"

def log(message):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")
    with open("worker_log.txt", "a") as f:
        f.write(f"[{timestamp}] {message}\n")

def update_sheet_status(app_name, column, status):
    payload = {"action": "update_status", "app_name": app_name, "column": column, "status": status}
    try:
        requests.post(SHEET_URL, data=json.dumps(payload), headers={'Content-Type': 'application/json'}, allow_redirects=True)
        return True
    except:
        return False

def check_link_alive(url):
    try:
        response = requests.head(url, timeout=10, allow_redirects=True)
        return response.status_code == 200
    except:
        return False

def handle_research(task):
    app_name = task['appName']
    log(f"🚀 Starting RESEARCH for {app_name}...")
    update_sheet_status(app_name, "research", "Pending")
    
    # Ở phiên bản Worker này, Agent (tôi) sẽ thực hiện Research thủ công qua chat
    # Hoặc bạn có thể cung cấp các URL trực tiếp trong Topic Structure
    # Để đảm bảo an toàn, Worker sẽ báo Fail nếu không có URL cụ thể để Ingest tự động
    log(f"⚠️ Research requires manual URL discovery by the AI agent in the chat session.")
    update_sheet_status(app_name, "research", "Fail")

def handle_generate(task):
    app_name = task['appName']
    log(f"🚀 Starting GENERATE for {app_name}...")
    update_sheet_status(app_name, "generate", "Pending")
    
    # Logic này sẽ gọi Agent thực thi thông qua tệp tín hiệu hoặc subprocess
    # Vì việc 'Generate' cần trí tuệ của LLM, Worker sẽ ghi lại yêu cầu vào một file 'todo.json'
    # để tôi (Agent) có thể xử lý ngay khi bạn mở terminal hoặc qua webhook.
    
    with open("pending_tasks.json", "a") as f:
        f.write(json.dumps(task) + "\n")
    
    log(f"📝 Task for {app_name} registered. AI Agent will process this immediately.")

def poll_dashboard():
    payload = {"action": "read_tasks"}
    try:
        response = requests.post(SHEET_URL, data=json.dumps(payload), headers={'Content-Type': 'application/json'}, allow_redirects=True)
        tasks = response.json()
        for task in tasks:
            if not task['appName']: continue
            
            # Kiểm tra lệnh Research
            if task['researchStatus'] == "Research":
                handle_research(task)
            
            # Kiểm tra lệnh Generate
            if task['generateStatus'] == "Generate":
                handle_generate(task)
                
    except Exception as e:
        log(f"❌ Error polling dashboard: {e}")

if __name__ == "__main__":
    log("🤖 Flashcard Master Worker started...")
    while True:
        poll_dashboard()
        time.sleep(60) # Quét mỗi phút một lần
