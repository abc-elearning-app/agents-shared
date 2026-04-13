import requests
import json

url = "https://script.google.com/macros/s/AKfycbzX9ZvLEAZ0D2FRtMnH-97Fahbph6ZXHJFQ4gSj9eTtKIWaMki9USV7URD5w3UmQKfFPg/exec"
payload = {"action": "read_tasks"}

try:
    response = requests.post(url, data=json.dumps(payload), headers={'Content-Type': 'application/json'}, allow_redirects=True)
    tasks = response.json()
    # Tìm các task cần xử lý
    for task in tasks:
        if task.get('researchStatus') == "Research" or task.get('generateStatus') == "Generate":
            print(json.dumps(task))
except Exception as e:
    print(f"Error: {e}")
