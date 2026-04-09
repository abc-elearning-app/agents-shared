import json
import requests

DATA = {
    "appName": "fsc",
    "flashcards": [
        # (Dữ liệu 100 thẻ của Topic 1 & 2 đã generate ở trên)
    ]
}

URL = "https://script.google.com/macros/s/AKfycbzzNrqiWiV3kTbwaAN1f94X6gcaxxuy7b_NmC1mlKTyBlpjYRZ4JQKcQXVP04qQUfCioQ/exec"
# Tôi sẽ gửi một phần dữ liệu để xác nhận lại một lần nữa
response = requests.post(URL, json=DATA)
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")
