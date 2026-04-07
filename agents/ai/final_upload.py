import requests
import time
import os
import json

url = "https://script.google.com/macros/s/AKfycbzCOsyhKIZcfu9caX8UPTLbVsNNG7JM12XJz1B5dMnEK83MQZaYkHsoGOwuJla3dRPjeg/exec"

topics = {
    1: range(1, 14),
    2: range(1, 10),
    3: range(1, 6),
    4: range(1, 10),
    5: range(1, 11),
    6: range(1, 8)
}

success_count = 0
fail_count = 0

for t, subtopics in topics.items():
    for s in subtopics:
        filename = f"ccna_t{t}_s{s}.json"
        if os.path.exists(filename):
            print(f"Uploading {filename}...", end=" ")
            try:
                with open(filename, "r") as f:
                    data = json.load(f)
                
                # Ensure structure
                data["appName"] = "ccna"
                
                response = requests.post(url, json=data)
                if response.status_code == 200 and '"result":"success"' in response.text:
                    print("SUCCESS")
                    success_count += 1
                else:
                    print(f"FAILED (Status: {response.status_code}, Resp: {response.text[:50]})")
                    fail_count += 1
            except Exception as e:
                print(f"ERROR: {str(e)}")
                fail_count += 1
            time.sleep(1.5)
        else:
            print(f"SKIP: {filename} not found")

print(f"\nFinal Summary: {success_count} succeeded, {fail_count} failed.")
