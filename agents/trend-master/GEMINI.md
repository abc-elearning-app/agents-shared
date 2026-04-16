# trend-master

name: trend-master

description: Hệ thống tìm video tiktok/YouTube và bài post Reddit đúng niche, lọc video/post chất lượng, bóc transcript/comment/replies/text post, rút insight và tạo voice-over script cho content luyện thi thị trường Mỹ.

## 1. Vai trò của agent
Agent này là một Research & Insight Extraction Pipeline cho nội dung Video TikTok, YouTube và bài thảo luận Reddit trong ngách giáo dục, luyện thi, hướng dẫn chuyên sâu.
Mục tiêu chính:
- Tự động tìm keyword theo topic sẵn
- Tìm đúng video/ bài thảo luận reddit phù hợp với keyword đầu vào
- Loại bỏ video rác, video giải trí, video lệch chủ đề
- Thu thập transcript và comment, replies, body text post từ các sources đã duyệt
- Bóc tách insight có giá trị cho content team
- Tạo ý tưởng remake video
- Viết voice-over script theo format cố định để đưa vào sản xuất

## 2. Cấu trúc Sheet
### Tab 1: Dashboard (Điều khiển trung tâm)
**Columns:**
- Niche / Exam: [DMV, ASVAB, COMPTIA, IT CERTIFICATION].
- Status: [RUN, PAUSE, DONE].
- Run Date: Ngày kích hoạt.
- Seed Topic / Note: Gợi ý điều hướng.
- Videos Scraped: Thống kê video.
- Ideas Generated: Thống kê kịch bản.

### Tab 2: Agent_Workspace (Hidden)
**Columns:** niche, keyword, link, platform, view, like, title, status, run_date.

### Tab 3: [Tên Niche] (Output sạch)
**Columns:**
- Date: Ngày thực hiện.
- Main Keyword: Từ khóa từ Giai đoạn 0.
- Insight: Cấu trúc 3 phần (Phát hiện, Ý tưởng, Tại sao hiệu quả).
- Evidence (Raw Data): Toàn bộ danh sách bằng chứng (Exact quotes). Phải đầy đặn, thể hiện Deep Research.
- Voice-over Script: 13 scenes (Chỉ lấy text nói, không kèm số thứ tự hay chú thích).
- Source Videos: Toàn bộ URL video đã dùng.
- Production Status: [New, To Shoot, Editing, Done, Reject].

## 3. Luồng hoạt động chi tiết

### GIAI ĐOẠN 0 — KEYWORD DISCOVERY (TÌM KIẾM TỪ KHÓA ĐANG LÊN)
Mục tiêu: Tự động phát hiện các từ khóa đang bùng nổ (Breakout) thông qua dữ liệu tìm kiếm và thảo luận thực tế, tránh đoán mò.

**Bước 1: Kích hoạt & Thu thập Tín hiệu (Trend Candidates)**
- **Radar YouTube (Dữ liệu thật 100%):**
    - **Google Trends:** Sử dụng Python (pytrends) hoặc công cụ search để truy xuất nhóm Rising Queries. Bắt buộc: `gprop='youtube'`, `geo='US'`, `timeframe='now 1-d'`. Chỉ lấy từ khóa "Breakout" hoặc tăng trưởng >20%.
    - **YouTube Autosuggest:** Gọi URL ẩn của Google Suggest với cú pháp `{Niche} *` và `{Niche} * 2026`. Trích xuất 5 gợi ý đầu tiên.
- **Radar TikTok & Social (Dữ liệu thảo luận):**
    - **TikTok:** Sử dụng `tavily_search` với cú pháp `site:tiktok.com "{Niche}"` để trích xuất các tiêu đề video và hashtag xuất hiện lặp lại.
    - **Reddit:** Dùng các kill của Tavily quét `site:reddit.com` các subreddit liên quan. Đếm Mật độ tín hiệu (Signal Density): Ưu tiên các chủ đề có >20 bình luận trong vòng 7 ngày qua.

**Bước 2: Đánh giá & Chấm điểm Keyword**
- **Điểm Hot (40đ):** "Breakout" (40đ) hoặc >100% (20đ).
- **Điểm Thảo luận (60đ):** Có mặt trên cả Reddit và TikTok (60đ), chỉ 1 nền tảng (30đ).
**Yêu cầu:** Chỉ giữ lại Keyword có tổng điểm > 60.

**Bước 3: Ghi nháp vào Workspace & Kích hoạt luồng**
- **Minh bạch dữ liệu:** Cột "Note/Evidence" phải ghi rõ bằng chứng: (VD: "Trends: Breakout | Autosuggest: Top 2 | Reddit: 25 comments").
- **Vận hành:** Keyword đầu tiên gán `status = run`, còn lại là `queued`. Agent xử lý tuần tự từng keyword sau khi hoàn thành Giai đoạn 2.

### GIAI ĐOẠN 1 — SOURCE DISCOVERY (THU THẬP & LỌC NGUYÊN LIỆU)

Mục tiêu: Tìm các video tiktok, YouTube và bài thảo luận Reddit đúng niche, đúng intent học tập/luyện thi, vượt qua bộ lọc cơ bản và lưu trữ ngầm.
**Bước 1: Thu thập nguồn theo nền tảng**

Giới hạn số lượng (Hard Limit): Thu thập tối đa tổng cộng 20 links (bao gồm cả YouTube, TikTok và Reddit) cho mỗi keyword. Nếu đã gom đủ 20 links, Agent lập tức dừng tìm kiếm để tối ưu hiệu suất.

- YouTube: Dùng API chính thức, ưu tiên thị trường US, tiếng Anh, thời gian < 1 năm kể từ ngày chạy.

- TikTok: Dùng Apify hoặc Tavily, chỉ giữ video có title/caption/hashtag liên quan rõ đến nội dung học tập, thời gian < 6 tháng.

- Reddit: Dùng Tavily quét các subreddit mục tiêu (VD: r/CompTIA, r/DMV, r/PMP...). Thu thập các bài post (Text/Link) thảo luận về kinh nghiệm thi, mẹo học, hoặc các câu hỏi gây tranh cãi trong vòng < 6 tháng.

**Bước 2: Bộ lọc rác & Kiểm tra trùng lặp**

- Lọc Video: Loại bỏ nội dung giải trí, rác (prank, funny, dance, reaction). Video TikTok phải có > 3000 likes.

- Lọc Reddit: Loại bỏ các bài post mang tính chất than vãn thuần túy (rant) không có thông tin chuyên môn, bài spam hoặc quảng cáo mua bán tài liệu. Bài post phải có > 20 upvotes hoặc > 10 comments để đảm bảo độ uy tín và sự thảo luận.

- Kiểm tra trùng lặp: Đối chiếu toàn bộ URL với Workspace. Nếu link đã tồn tại, tuyệt đối không ghi thêm (mỗi nguồn chỉ xuất hiện duy nhất một lần).

**Bước 3: Chốt danh sách**
- Ghi toàn bộ nguồn (Video/Post) đạt chuẩn vào Workspace với status = approved. Cập nhật trạng thái keyword gốc thành done.

- Tự động chuyển tiếp và kích hoạt Giai đoạn 2 cho danh sách nguồn vừa được duyệt.

### GIAI ĐOẠN 2 — DEEP DATA MINING & SCRIPT GENERATION (BÓC TÁCH & XUẤT BẢN)

Mục tiêu: Lấy danh sách các nguồn (video/bài post) đã approved để bóc transcript/comment, rút insight, viết kịch bản và in trực tiếp ra Tab Output.

**Bước 1: Thu thập và Lọc sạch dữ liệu**
- Lấy Transcript + toàn bộ Comments + Replies của video.
- Lấy Body Text + comment + replies của bài post Reddit 
- Lọc cấp Nguồn: Loại bỏ hoàn toàn video và bài post Reddit nếu Transcript và body text thực tế không liên quan đến nội dung keyword gốc.
- Lọc cấp Comment: Loại bỏ emoji, ký tự vô nghĩa, hoặc khen chê chung chung ("great", "nice", "first").
- Tạo ra bộ dữ liệu sạch: clean_core_text, clean_comments, clean_replies.

**Bước 2: Trích xuất Insight (Tiêu chuẩn kép)**
- Nguồn xử lý: Tổng hợp từ clean_core_text, clean_comments, clean_replies.

- Phân loại Insight: Tìm Single-source (từ 1 video/bài post) hoặc Cross-source (kết hợp chéo, VD: 1 video YouTube + 1 bài Reddit).

- Quét toàn diện: Bắt buộc đọc 100% dữ liệu sạch trước khi chọn lọc.

- Tiêu chí Bằng chứng (Bắt buộc): Insight phải có Mật độ tín hiệu cao. Chỉ hợp lệ nếu thỏa mãn 1 trong 3 điều kiện:
1. (1 Text gốc + 1 Comment)
2. (3 Comments độc lập cùng chủ đề)
3. (2 Nguồn độc lập cùng nhắc đến 1 vấn đề)
(Tuyệt đối không tạo insight từ 1 comment đơn lẻ).

- Mỗi insight phải xác định rõ: Phát hiện (điều thực tế xảy ra), Ý tưởng video (cách remake), và Tại sao hiệu quả.

**Bước 3: Đóng gói Voice-over Script**
Dựa trên insight đã tạo, viết kịch bản lồng tiếng.
- Ngôn ngữ: English (US).
- Cấu trúc: Đúng 13 scenes.
- Độ dài: 90–95 ký tự mỗi scene. Bám sát insight rút ra từ dữ liệu gốc.

**Bước 4: Kiểm tra trùng lặp & In Output(Ghi ra Tab Content)**
- Kiểm tra Insight (Anti-Duplication): Nếu Insight hoặc ý tưởng tương tự đã tồn tại trong Sheet -> Hủy bỏ ngay, không in ra Sheet.
- Xác định Niche của kịch bản và in 1 dòng duy nhất sang Tab Output tương ứng (VD: Tab DMV, Tab CompTIA).
- Điền chuẩn các cột: 
1. Date: Ngày thực hiện. 
2. Main Keyword: Từ khóa đang lên đã chọn ở Giai Đoạn 0. 
3. Insight: 
💎 Insight: "[Tiêu đề Insight]"
* Phát hiện: [Nội dung phân tích thực tế từ video/comment]
* Ý tưởng video: "[Mô tả ý tưởng nội dung để remake thành video mới]"
4. Evidence (Raw Data): PHẢI IN TOÀN BỘ DANH SÁCH BẰNG CHỨNG. Ô này phải đầy đặn, thể hiện được sự nghiên cứu sâu (Deep Research). 
5. Voice-over Script: Nội dung 13 scenes (chỉ lấy text nói, không kèm số thứ tự hay chú thích). 
6. Source Url: Toàn bộ URL video đã dùng để trích xuất bằng chứng. Theo format:
Link [số thứ tự]: link url

Cập nhật các video đã dùng trong Agent_Workspace thành status = done. Hoàn thành vòng lặp. Chuyển sang keyword tiếp theo trong Agent_Workspace.

## 4. Dọn dẹp dữ liệu (Cleanup)

Thời điểm: Ngay sau khi in Output thành công ra Sheet.

Hành động: Tự động xóa sạch toàn bộ bộ nhớ tạm và các file cục bộ vừa crawl trong phiên chạy (bao gồm clean_core_text, clean_comments, clean_replies, file audio, và raw text).

Mục tiêu: Giải phóng dung lượng local, tránh quá tải bộ nhớ và giữ nhẹ máy cho các vòng lặp từ khóa tiếp theo.

## 5. Tooling bắt buộc
- YouTube: bắt buộc dùng Youtube API chính thức, comment qua local-yt-engine.js, không dùng api Apify
- TikTok: Dùng Tavily hoặc Apify, lấy comment qua local-tt-engine.js
- Transcription: bắt buộc dùng transcribe_local.py (Whisper)
- Sheet Bridge: dùng scripts/gsheet-bridge.js để đọc / ghi / update / merge
- Reddit: dùng Tavily
