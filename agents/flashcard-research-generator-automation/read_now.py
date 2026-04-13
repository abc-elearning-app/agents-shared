import requests
import json

url = "https://script.google.com/macros/s/AKfycbzX9ZvLEAZ0D2FRtMnH-97Fahbph6ZXHJFQ4gSj9eTtKIWaMki9USV7URD5w3UmQKfFPg/exec"
payload = {"action": "read_tasks"}

try:
    response = requests.post(url, data=json.dumps(payload), headers={'Content-Type': 'application/json'}, allow_redirects=True)
    tasks = response.json()
    # Chỉ in ra các task đang cần xử lý (Research/Generate)
    active_tasks = [t for t in tasks if t.get('researchStatus') in ['Research', 'Pending'] or t.get('generateStatus') in ['Generate', 'Pending']]
    print(json.dumps(active_tasks, indent=2))
except Exception as e:
    print(f"Error: {e}")
