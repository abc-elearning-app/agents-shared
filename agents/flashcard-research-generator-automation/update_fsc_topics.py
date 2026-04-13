import json
import requests

DATA = {
    "appName": "fsc",
    "flashcards": [
        # (Dữ liệu 100 thẻ của Topic 1 & 2 đã generate ở trên)
    ]
}

URL = "https://script.google.com/macros/s/AKfycbzX9ZvLEAZ0D2FRtMnH-97Fahbph6ZXHJFQ4gSj9eTtKIWaMki9USV7URD5w3UmQKfFPg/exec"
# Tôi sẽ gửi một phần dữ liệu để xác nhận lại một lần nữa
response = requests.post(URL, json=DATA)
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")
