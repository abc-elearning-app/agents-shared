# Agents Shared

Kho agent dùng chung cho toàn công ty. Mỗi agent là một file markdown với YAML frontmatter + system prompt, tương thích Claude Code, Gemini CLI, và Antigravity.

## Cài đặt

### Cài tất cả agents của một team

```bash
./install.sh --category dev        # Cài tất cả agents trong agents/dev/
./install.sh --category qa         # Cài tất cả agents trong agents/qa/
```

### Cài một agent cụ thể

```bash
./install.sh --agent agents/dev/api-endpoint-generator.md
```

### Cài tất cả agents

```bash
./install.sh --all
```

Script sẽ tự detect thư mục agent phù hợp: `./agents/` → `.claude/agents/` → `.agent/agents/`.

## Catalog

### dev — Development (FE, BE, Mobile)

| Agent | Description | Tools | Author |
|-------|-------------|-------|--------|
| *(chưa có agent)* | | | |

### qa — Testing, Review, Audit

| Agent | Description | Tools | Author |
|-------|-------------|-------|--------|
| *(chưa có agent)* | | | |

### ops — Deploy, Infra, Monitoring

| Agent | Description | Tools | Author |
|-------|-------------|-------|--------|
| *(chưa có agent)* | | | |

### data — Analytics, Scraping, Reporting

| Agent | Description | Tools | Author |
|-------|-------------|-------|--------|
| *(chưa có agent)* | | | |

### content — Writing, Editing, Translation

| Agent | Description | Tools | Author |
|-------|-------------|-------|--------|
| *(chưa có agent)* | | | |

### marketing — Campaigns, SEO, Social

| Agent | Description | Tools | Author |
|-------|-------------|-------|--------|
| *(chưa có agent)* | | | |

### general — Cross-team, Utilities

| Agent | Description | Tools | Author |
|-------|-------------|-------|--------|
| *(chưa có agent)* | | | |

## Đóng góp agent mới

Xem [CONTRIBUTING.md](CONTRIBUTING.md) để biết quy trình đóng góp.

**Tóm tắt nhanh:**

1. Fork repo → tạo branch
2. Tạo agent bằng `/agent-factory` (có sẵn option publish)
3. Hoặc copy thủ công vào `agents/<category>/`
4. Mở PR — điền template đầy đủ
5. Review → merge

## Agent File Format

```yaml
---
name: kebab-case-name
description: mô tả action-oriented, tối thiểu 10 từ
tools: Read, Glob, Grep, WebFetch
model: inherit
color: green
field: data
expertise: expert
author: your-name
tags: keyword1, keyword2, keyword3
---

System prompt content ở đây...
```

### Required fields

| Field | Format | Ví dụ |
|-------|--------|-------|
| `name` | kebab-case, 3-40 ký tự | `vnexpress-scraper` |
| `description` | ≥10 từ, action-oriented | `Thu thập tiêu đề và URL bài viết từ trang VnExpress` |
| `tools` | comma-separated string | `Read, Glob, Grep, WebFetch` |
| `model` | sonnet\|opus\|haiku\|inherit | `inherit` |
| `color` | blue\|green\|red\|purple\|orange | `green` |

### Optional fields

| Field | Format | Ví dụ |
|-------|--------|-------|
| `field` | frontend\|backend\|testing\|security\|data\|ai\|... | `data` |
| `expertise` | beginner\|intermediate\|expert | `expert` |
| `author` | tên người tạo | `hiep` |
| `tags` | comma-separated keywords | `scraping, web, vnexpress` |

## Tìm kiếm agent

Tìm theo tag:
```bash
grep -rl "tags:.*scraping" agents/
```

Tìm theo author:
```bash
grep -rl "author:.*hiep" agents/
```

Tìm theo field:
```bash
grep -rl "field:.*data" agents/
```
