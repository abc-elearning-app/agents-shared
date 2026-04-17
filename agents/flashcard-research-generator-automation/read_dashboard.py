import requests
import json

url = "https://script.google.com/macros/s/AKfycbxrVC5t3Ak35q2cQLUAsFern7aOwLXChbpsADbXW4vNPNnyhHGr6cF1vuh_FYol7CiwGw/exec"
payload = {"action": "read_tasks"}

try:
    response = requests.post(url, data=json.dumps(payload), headers={'Content-Type': 'application/json'}, allow_redirects=True)
    print(f"URL used: {url}")
    print(f"Raw Response: {response.text}")
    data = response.json()
    tasks = data.get("tasks", []) if isinstance(data, dict) else data
    if tasks:
        for task in tasks:
            if isinstance(task, dict):
                app = task.get("appName")
                app_id = task.get("appId") or task.get("databaseId") or "N/A"
                status_r = task.get("researchStatus")
                status_g = task.get("generateStatus")
                print(f"App: {app} | ID: {app_id} | Research: {status_r} | Generate: {status_g}")
    else:
        print("No tasks found or empty list.")
except Exception as e:
    print(f"Error: {e}")
