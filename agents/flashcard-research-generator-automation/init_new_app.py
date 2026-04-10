import requests
import json

url = "https://script.google.com/macros/s/AKfycbwM_sk8-VNktBMybaRcoqTnqLTat1XVDtDUklQ-e0ZM-wbVZqFR2P3Ah5LM9gfFRX6P/exec"

# Dữ liệu khởi tạo đầy đủ cho 1 app mới
payload = {
    "action": "update_status",
    "app_name": "dmv-ms",
    "column": "research",
    "status": "Research"
}

# Tôi gửi thêm thông tin bổ sung để điền vào các cột trống nếu app mới tạo
# Trong thực tế Apps Script của bạn cần được cập nhật để nhận các trường này
# Ở đây tôi demo việc kích hoạt lệnh Research
try:
    response = requests.post(url, data=json.dumps(payload), headers={'Content-Type': 'application/json'}, allow_redirects=True)
    print(f"Trigger Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
