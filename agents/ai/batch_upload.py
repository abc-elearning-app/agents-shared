import requests
import json
import os
import time

def upload_json(file_path, url):
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found.")
        return False

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"Uploading {file_path} to {url}...")
    
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
    url = "https://script.google.com/macros/s/AKfycbzCOsyhKIZcfu9caX8UPTLbVsNNG7JM12XJz1B5dMnEK83MQZaYkHsoGOwuJla3dRPjeg/exec"
    files = [
        "ccna_t1_s1.json",
        "ccna_t1_s2.json",
        "ccna_t1_s3.json",
        "ccna_t1_s4.json",
        "ccna_t1_s5.json",
        "ccna_t1_s6.json",
        "ccna_t1_s7.json",
        "ccna_t1_s8_9.json",
        "ccna_t1_s10.json",
        "ccna_t1_s11.json",
        "ccna_t1_s12.json",
        "ccna_t1_s13.json"
    ]
    
    for i, file_path in enumerate(files):
        success = upload_json(file_path, url)
        if i < len(files) - 1:
            print("Waiting 2 seconds before next upload...")
            time.sleep(2)

    print("Batch upload complete.")
