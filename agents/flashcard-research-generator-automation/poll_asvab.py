import requests
import json

url = "https://script.google.com/macros/s/AKfycbzX9ZvLEAZ0D2FRtMnH-97Fahbph6ZXHJFQ4gSj9eTtKIWaMki9USV7URD5w3UmQKfFPg/exec"
payload = {"action": "read_tasks"}

try:
    response = requests.post(url, data=json.dumps(payload), headers={'Content-Type': 'application/json'}, allow_redirects=True)
    tasks = response.json()
    asvab_task = next((t for t in tasks if t.get('appName') == 'asvab'), None)
    if asvab_task:
        print(json.dumps(asvab_task))
    else:
        print("NOT_FOUND")
except Exception as e:
    print(f"Error: {e}")
