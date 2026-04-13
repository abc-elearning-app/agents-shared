import requests
import time
import os

url = "https://script.google.com/macros/s/AKfycbzX9ZvLEAZ0D2FRtMnH-97Fahbph6ZXHJFQ4gSj9eTtKIWaMki9USV7URD5w3UmQKfFPg/exec"
files = ["ccna_t2_s1.json", "ccna_t2_s2.json"]

for f in files:
    if os.path.exists(f):
        print(f"Uploading {f}...")
        with open(f, "rb") as open_file:
            response = requests.post(url, data=open_file, headers={"Content-Type": "application/json"})
            print(f"Status: {response.status_code}, Response: {response.text}")
        time.sleep(2)
    else:
        print(f"File {f} not found!")
