# Contributing

Hướng dẫn đóng góp agent vào kho `agents-shared`.

## Quy trình

### 1. Tạo agent

**Cách 1 — Dùng Agent Factory (khuyến nghị):**
```bash
# Trong project của bạn (đã cài agent-factory)
/agent-factory "mô tả agent của bạn"
# Test và refine → gõ "done"
# Chọn "Share" khi được hỏi → tự động tạo PR
```

**Cách 2 — Tạo thủ công:**
```bash
# Fork repo agents-shared
git clone https://github.com/abc-elearning-app/agents-shared.git
cd agents-shared
git checkout -b add/<agent-name>

# Tạo file agent
cp agents/general/.template.md agents/<category>/<agent-name>.md
# Sửa nội dung...

# Commit và push
git add agents/<category>/<agent-name>.md
git commit -m "Add <agent-name> agent"
git push origin add/<agent-name>
```

### 2. Chọn category

| Category | Dùng cho |
|----------|----------|
| `dev` | Frontend, backend, mobile, DevOps tools |
| `qa` | Testing, code review, security audit |
| `ops` | Deployment, infrastructure, monitoring |
| `data` | Analytics, scraping, data processing, reporting |
| `content` | Writing, editing, translation, documentation |
| `marketing` | Campaigns, SEO, social media, ads |
| `general` | Cross-team utilities, không thuộc team nào cụ thể |

### 3. Mở Pull Request

- Điền đầy đủ PR template
- Đảm bảo agent đã được test trước khi submit
- Mỗi PR chỉ nên chứa 1 agent

### 4. Review

- Reviewer kiểm tra: format đúng, description rõ ràng, tools phù hợp
- Sau khi approve → merge vào main

## Checklist Quality

Trước khi submit PR, đảm bảo agent đáp ứng:

- [ ] **Name:** kebab-case, 3-40 ký tự, không double hyphens
- [ ] **Description:** ≥10 từ, action-oriented, mô tả khi nào nên dùng
- [ ] **Tools:** Chỉ dùng tools cần thiết, tuân thủ 3-tier safety model
- [ ] **System prompt:** Có quy trình rõ ràng, steps đánh số, xử lý edge cases
- [ ] **Tested:** Đã chạy agent ít nhất 1 lần và kết quả đúng ý
- [ ] **Category:** Đặt đúng thư mục team
- [ ] **Tags:** Có ít nhất 2-3 tags để dễ tìm kiếm

## Quy tắc đặt tên

- Dùng kebab-case: `api-endpoint-generator`, không `apiEndpointGenerator`
- Tên nên mô tả chức năng: `python-code-reviewer`, không `reviewer`
- Tránh tên quá generic: `helper`, `tool`, `utility`
- Tránh tên quá dài (>40 ký tự)

## Cập nhật agent đã có

1. Tạo branch: `update/<agent-name>`
2. Sửa file agent
3. Mở PR với mô tả thay đổi
4. Nếu thay đổi tools hoặc behavior → cần review kỹ hơn

## Xoá agent

Mở issue với label `deprecate` và lý do. Team sẽ review trước khi xoá.
