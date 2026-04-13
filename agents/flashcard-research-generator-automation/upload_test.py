import requests
import json
import os

def upload_json(file_path, url):
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found.")
        return

    with open(file_path, 'r') as f:
        data = json.load(f)

    print(f"Uploading {file_path} to {url}...")
    
    try:
        # Google Apps Script requires following redirects. 
        # requests.post follows redirects by default, but it might change POST to GET on 302.
        # For GAS, this is usually fine as the response content is on the redirected page.
        response = requests.post(
            url, 
            data=json.dumps(data),
            headers={'Content-Type': 'application/json'},
            allow_redirects=True
        )
        
        print(f"Status Code: {response.status_code}")
        print("Response Text:")
        print(response.text)
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    url = "https://script.google.com/macros/s/AKfycbzX9ZvLEAZ0D2FRtMnH-97Fahbph6ZXHJFQ4gSj9eTtKIWaMki9USV7URD5w3UmQKfFPg/exec"
    file_path = "ccna_t1_s1.json"
    upload_json(file_path, url)
