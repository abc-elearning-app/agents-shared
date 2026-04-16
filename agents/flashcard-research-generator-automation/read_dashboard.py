import requests
import json

url = "https://script.google.com/macros/s/AKfycbxrVC5t3Ak35q2cQLUAsFern7aOwLXChbpsADbXW4vNPNnyhHGr6cF1vuh_FYol7CiwGw/exec"
payload = {"action": "read_tasks"}

try:
    response = requests.post(url, data=json.dumps(payload), headers={'Content-Type': 'application/json'}, allow_redirects=True)
    data = response.json()
    if data.get("ok"):
        for task in data.get("tasks", []):
            app = task.get("appName")
            app_id = task.get("appId") or task.get("databaseId") or "N/A"
            status_r = task.get("researchStatus")
            status_g = task.get("generateStatus")
            print(f"App: {app} | ID: {app_id} | Research: {status_r} | Generate: {status_g}")
    else:
        print(response.text)
except Exception as e:
    print(f"Error: {e}")
