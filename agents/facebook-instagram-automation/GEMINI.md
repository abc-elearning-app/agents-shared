# Hướng Dẫn Vận Hành Agent Tự Động Hóa Facebook & Instagram

## Tổng quan
Agent này có nhiệm vụ tự động hóa việc tạo hình ảnh theo template có sẵn và đăng bài viết từ dữ liệu trên **Google Sheets** lên các Fanpage Facebook và tài khoản Instagram.

Dự án hỗ trợ 2 luồng công việc chính tách biệt:
1.  **Luồng 1: Quiz Tự Động (Ảnh câu hỏi scale)** - Render ảnh từ dữ liệu câu hỏi thô bằng template và đăng lên Facebook, Instagram.
2.  **Luồng 2: Đăng Ảnh Tự Tạo (Ảnh tự tạo)** - AI phân tích ảnh có sẵn và tự viết nội dung (lên lịch hoặc đăng ngay).

---

## NGUYÊN TẮC HỆ THỐNG (SYSTEM PROMPT CHO AI)
Áp dụng cho mọi tác vụ sinh nội dung tự động:
- **Ngôn ngữ mục tiêu:** 100% nội dung (Title, Caption, CTA) phải được viết bằng tiếng Anh chuẩn, hướng tới đối tượng người Mỹ.
- **Chiến lược Hashtag chuẩn xác theo Nền tảng:** Yêu cầu AI phải nghiên cứu và lựa chọn hashtag bám sát insight của từng mạng xã hội, tuyệt đối không bịa hashtag chung chung.

---

## LUỒNG 1: QUIZ TỰ ĐỘNG (SHEET: ẢNH CÂU HỎI SCALE)

### 1. Đọc dữ liệu (Cột A - E)
- **Account (Cột A):** Tài khoản đích (PMP, Comptia Easy Prep, CompTIA Ready, DMV).
- **Topic (Cột B):** Chủ đề của câu hỏi.
- **Content (Cột C):** Nội dung câu hỏi thô (theo định dạng template).
- **Type (Cột D):** Phân loại nội dung sẽ tạo ảnh.
- **Status (Cột E):** 
    - `Ready`: Sẵn sàng. Agent chỉ quét và chạy các hàng có trạng thái này.
    - `Processing`: Đang xử lý. Đổi sang trạng thái này ngay khi bắt đầu để khóa luồng (lock), chống chạy trùng lặp.
    - `Error`: Lỗi. Dừng xử lý hàng này.
    - `Done`: Hoàn thành. Đã đăng bài và trả link thành công.

### 2. Tạo dữ liệu bằng AI (Cột F - J)
- **Trigger:** Cột E chuyển status sang `Ready` bắt đầu quá trình làm việc.
- **Title (Cột F):** Tiêu đề bài viết.
- **Caption (Cột G):** Nội dung bài viết (Agent sẽ tự gộp link CTA vào đây khi đăng FB).
- **Hashtag FB (Cột H):** Bộ 5-7 hashtag mở rộng cho Facebook.
- **Hashtag IG (Cột I):** Bộ 10-15 hashtag chuyên sâu ngách cho Instagram.
- **Image (Cột J):** Tên file ảnh local (hoặc Link sau khi upload Cloudinary).

### 3. Render & Đăng bài (Menu số 1 trong `./run.sh`)
- **Tạo ảnh:** Chạy `node scripts/generate_row.js <số_hàng>` để tạo ảnh trước. 
- **Đăng bài:** Chọn menu số **1**.
- **Facebook:** Đăng ảnh với Caption đã gộp link CTA.
- **Instagram:** Đăng qua Buffer MCP.
- **Kết quả:** Link bài viết thành công sẽ trả về **Cột L (Facebook)** và **Cột M (Instagram)**.

---

## LUỒNG 2: ĐĂNG ẢNH TỰ TẠO (SHEET: ẢNH TỰ TẠO)
Sử dụng AI để xử lý các ảnh thiết kế sẵn hoặc ảnh từ Google Drive.

### 1. Đọc đầu vào (Cột A - D)
- **File ảnh (Cột A):** Link Google Drive (Anyone with the link) hoặc file local (`file:///...`). **Tuyệt đối giữ nguyên link, không viết chèn hay thay đổi nội dung cột này.**
- **Status (Cột B):** 
    - `Ready`: Sẵn sàng.
    - `Processing`: Đang xử lý (Khóa luồng).
    - `Error`: Lỗi.
    - `Done`: Hoàn thành.
- **Account (Cột C):** Tài khoản đích.
- **Date (Cột D):** Ngày giờ đăng theo format `YYYY-MM-DD HH:mm:ss`. Để trống nếu muốn đăng ngay lập tức.

### 2. Xử lý AI & Đăng bài (Menu số 2 trong `./run.sh`)
- **Tối ưu nội dung:** Agent tự phân tích hình ảnh và điền vào: **Title (E)**, **Caption FB (F)**, **Caption IG (G)**, **Hashtag FB (H)**, **Hashtag IG (I)**, **CTA Content (J)**.
- **Thực thi:**
    - **Đăng ngay:** Nếu Cột B là `Ready` + Cột D (Date) Trống ➡️ Kích hoạt làm việc ngay lập tức.
    - **Chờ đến giờ:** Nếu Cột D có thời gian ➡️ Agent so sánh với thời gian thực tế. Khi đến giờ set ở cột D (cho phép sai số quét lùi 16 phút để không bỏ lỡ bài), tự động chuyển Cột B sang `Ready` để bắt đầu.
- **Kết quả:** Trả về link vào **Cột K (Facebook)** và **Cột L (Instagram)**. Cập nhật Status sang `Done`.

---

## Cấu hình hệ thống
- **Spreadsheet ID:** `13j1j4kL6XPGxfwPUSwItOP0nAwyaOhLSoVmvb5LWI6k`
- **Biến môi trường (.env):** Cần cấu hình đầy đủ các khóa sau trên server:
    - `GEMINI_API_KEY`: API Key từ Google AI Studio.
    - `FB_USER_TOKEN`: Facebook User Access Token (có quyền quản lý Page).
    - `GOOGLE_CLIENT_ID`: OAuth2 Client ID từ Google Cloud.
    - `GOOGLE_CLIENT_SECRET`: OAuth2 Client Secret.
    - `GOOGLE_REFRESH_TOKEN`: Refresh Token để duy trì quyền truy cập Google Sheets.
    - `BUFFER_TOKEN`: Access Token từ Buffer API.
    - `BUFFER_ORG_ID`: ID của Organization trên Buffer.
    - `CLOUDINARY_URL`: Cấu hình Cloudinary (hoặc cấu hình rời `cloud_name`, `api_key`...).
- **Tài khoản hỗ trợ:** PMP, Comptia Easy Prep, CompTIA Ready, DMV.
- **Vận hành:** Luôn sử dụng `./run.sh` hoặc cấu hình Cron job/PM2 để chạy tự động các script trong thư mục `scripts/`.
