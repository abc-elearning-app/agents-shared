import requests
import json
import os
import sys

def upload_json(file_path):
    # URL mới nhất của bạn
    url = "https://script.google.com/macros/s/AKfycbzX9ZvLEAZ0D2FRtMnH-97Fahbph6ZXHJFQ4gSj9eTtKIWaMki9USV7URD5w3UmQKfFPg/exec"
    
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found.")
        return False

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"Uploading {file_path} to Dashboard...")
    
    try:
        response = requests.post(
            url, 
            data=json.dumps(data),
            headers={'Content-Type': 'application/json'},
            allow_redirects=True
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        return response.status_code == 200
        
    except Exception as e:
        print(f"An error occurred: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        upload_json(sys.argv[1])
    else:
        print("Usage: python3 batch_upload.py <file_path>")
