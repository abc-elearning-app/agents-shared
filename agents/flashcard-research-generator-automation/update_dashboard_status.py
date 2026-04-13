import requests
import json
import sys

def update_status(app_name, column, status):
    url = "https://script.google.com/macros/s/AKfycbzX9ZvLEAZ0D2FRtMnH-97Fahbph6ZXHJFQ4gSj9eTtKIWaMki9USV7URD5w3UmQKfFPg/exec"
    
    # Payload để cập nhật Dashboard
    payload = {
        "action": "update_status",
        "app_name": app_name,
        "column": column, # 'research' hoặc 'generate'
        "status": status  # 'Pending', 'Done', 'Fail', 'None'
    }
    
    print(f"Updating Dashboard: {app_name} | {column} -> {status}...")
    
    try:
        response = requests.post(
            url, 
            data=json.dumps(payload),
            headers={'Content-Type': 'application/json'},
            allow_redirects=True
        )
        print(f"Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python3 update_dashboard_status.py <app_name> <column> <status>")
    else:
        update_status(sys.argv[1], sys.argv[2], sys.argv[3])
