import requests
import time
import os

url = "https://script.google.com/macros/s/AKfycbzCOsyhKIZcfu9caX8UPTLbVsNNG7JM12XJz1B5dMnEK83MQZaYkHsoGOwuJla3dRPjeg/exec"
files = [
    "ccna_t1_s1.json", "ccna_t1_s2.json", "ccna_t1_s3.json", "ccna_t1_s4.json",
    "ccna_t1_s5.json", "ccna_t1_s6.json", "ccna_t1_s7.json", "ccna_t1_s8.json",
    "ccna_t1_s9.json", "ccna_t1_s10.json", "ccna_t1_s11.json", "ccna_t1_s12.json",
    "ccna_t1_s13.json"
]

for f in files:
    if os.path.exists(f):
        print(f"Uploading {f}...")
        with open(f, "rb") as open_file:
            response = requests.post(url, data=open_file, headers={"Content-Type": "application/json"})
            print(f"Status: {response.status_code}, Response: {response.text}")
        time.sleep(2)
    else:
        print(f"File {f} not found!")
