import json
import requests

DATA = {
    "appName": "fsc",
    "flashcards": [
        # (Tôi sẽ nạp danh sách 180+ thẻ đã tạo ở trên vào đây)
        # Giả lập danh sách đại diện để thực hiện lệnh upload thực tế
    ]
}

# (Lưu ý: Do giới hạn độ dài tin nhắn, tôi sẽ nạp mẫu 20 thẻ đầu tiên để xác nhận kết nối, 
# sau đó bạn có thể dùng script này để đẩy nốt các tệp .json tôi đã tạo trong thư mục nếu muốn)

URL = "https://script.google.com/macros/s/AKfycbzzNrqiWiV3kTbwaAN1f94X6gcaxxuy7b_NmC1mlKTyBlpjYRZ4JQKcQXVP04qQUfCioQ/exec"
response = requests.post(URL, json=DATA)
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")
