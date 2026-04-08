const fs = require('fs');

function extractJson(filePath) {
    const content = fs.readFileSync(filePath, 'utf8');
    // Tìm mảng JSON hợp lệ cuối cùng trong file
    const matches = content.match(/\[[\s\S]*?\]/g);
    if (matches && matches.length > 0) {
        // Lấy mảng cuối cùng vì đó là kết quả của script
        const lastMatch = matches[matches.length - 1];
        try {
            return JSON.parse(lastMatch);
        } catch (e) {
            // Nếu mảng cuối không parse được, thử tìm mảng lớn nhất
            return JSON.parse(matches.sort((a,b) => b.length - a.length)[0]);
        }
    }
    return [];
}

const results = extractJson('discovery_pmp.json');
const existing = extractJson('existing_pmp.json');
const existingUrls = new Set(existing.map(r => r.video_url));

const filtered = results.filter(r => !existingUrls.has(r.video_url));
fs.writeFileSync('filtered_pmp.json', JSON.stringify(filtered));
console.log(`✅ Đã lọc xong: ${filtered.length} video mới.`);
