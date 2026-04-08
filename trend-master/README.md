# 🚀 TREND MASTER - MULTI-VIDEO SYNTHESIS ENGINE (24/7 SERVER READY)

Hệ thống theo dõi xu hướng (Discovery) và phân tích Insight (Synthesis) tự động cho YouTube & TikTok. Thiết kế tối ưu chi phí: Sử dụng Apify chỉ để săn link và Whisper/Puppeteer Local để đào sâu dữ liệu thô.

---

## 🛠️ YÊU CẦU HỆ THỐNG (SERVER SETUP)

Để hệ thống vận hành trơn tru 24/7, server cần cài đặt các môi trường sau:

### 1. Node.js & NPM
- Phiên bản tối thiểu: `v18.x` trở lên.
- Cài đặt thư viện: `npm install`

### 2. Python 3 & FFmpeg (Bắt buộc cho Whisper)
- Cài đặt Python: `python3 -m pip install -r requirements.txt`
- Cài đặt FFmpeg (Dùng để xử lý audio trước khi gỡ băng):
  - **Ubuntu/Debian:** `sudo apt update && sudo apt install ffmpeg`
  - **CentOS:** `sudo yum install ffmpeg`
  - **macOS:** `brew install ffmpeg`

### 3. Chromium / Google Chrome
- Dùng để chạy Puppeteer (Local Mining) ở chế độ `headless`.
- Nếu dùng Ubuntu Server, hãy cài đặt các gói hỗ trợ:
  `sudo apt install -y libgbm-dev wget gnupg ca-certificates`

---

## 🔐 CẤU HÌNH BẢO MẬT (IMPORTANT)

Các file sau **KHÔNG** được push lên GitHub (Đã có trong `.gitignore`). Bạn cần tạo thủ công trên server:

1. **`.env`**:
   ```env
   APIFY_TOKEN=your_apify_token_here
   GSHEET_ID=your_google_spreadsheet_id_here
   ```

2. **`credentials.json`**: 
   - File Service Account lấy từ Google Cloud Console để truy cập Google Sheet API.

---

## 🚀 QUY TRÌNH VẬN HÀNH

### Bước 1: Khởi động hệ thống (Chế độ giám sát 24/7)
Sử dụng **PM2** để đảm bảo script luôn chạy ngay cả khi bạn thoát server:
```bash
npm install pm2 -g
pm2 start scripts/monitor.js --name "trend-master-bot"
```

### Bước 2: Theo dõi hoạt động
```bash
pm2 logs trend-master-bot
```

### Bước 3: Cách thức hoạt động
1. **Discovery:** Bot sẽ quét Google Sheet (Tab `Video_Discovery`) để tìm Keyword cần săn lùng.
2. **Deep Mining:** Tự động lấy link TikTok qua Apify, sau đó dùng Whisper Local để gỡ băng và Puppeteer để đào comment (Tiết kiệm chi phí).
3. **Synthesis:** Tự động tổng hợp Insight 💎 theo chuẩn 13 cảnh (90-95 ký tự) và nộp bài về tab `Ideas`.

---

## 🚦 LUẬT CHƠI (HIẾN PHÁP GEMINI.MD)

Mọi thay đổi về logic phân tích hoặc định dạng Output phải được cập nhật trong file **`GEMINI.md`**. Hệ thống sẽ tự động đồng bộ sang Agent cấu hình để thực thi.

- **TikTok:** Chỉ dùng Apify để Discovery (Săn link). Mining dùng Local Engine.
- **YouTube:** Dùng Google API chính thức.
- **Transcription:** Luôn dùng Whisper Local (`transcribe_local.py`).
- **Output Ideas:** 13 cảnh kịch bản, 90-95 ký tự/dòng, không số thứ tự.

---

**© 2026 Trend Master Engine | Powered by Gemini CLI**
