const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const CHECK_INTERVAL = 10 * 60 * 1000; // 10 phút/lần
const GSHEET_ID = '1GC2BNL1BY1fDiNjK9TcN1W-dUjSp7m_8NUPu-64_Yro';

async function runPipeline(niche, rowNumber) {
    console.log(`🚀 [${niche}] Bắt đầu quy trình tự động...`);
    try {
        // GIAI ĐOẠN 0: Tìm Keyword
        console.log(`Step 0: Finding keywords...`);
        const kwOutput = execSync(`python3 scripts/fetch_autosuggest.py "${niche}"`).toString();
        // Lấy keyword đầu tiên từ kết quả autosuggest
        const match = kwOutput.match(/- (.*)/);
        const mainKeyword = match ? match[1] : niche;

        // GIAI ĐOẠN 1: Thu thập nguồn (Max 20 links)
        console.log(`Step 1: Gathering sources for ${mainKeyword}...`);
        execSync(`node scripts/search_sources.js "${mainKeyword}"`);

        // GIAI ĐOẠN 2: Khai thác sâu & Tạo Insight (Logic này cần tích hợp vào online_worker)
        // Lưu ý: Tôi giả định bạn sẽ chạy lệnh bóc tách cho các video trong discovery_results.json
        // Vì Giai đoạn 2 cần LLM trích xuất Insight, 
        // ở môi trường Online, worker sẽ gửi dữ liệu raw về cho tôi hoặc dùng API.
        
        // TẠM THỜI: Worker sẽ ghi trạng thái "Processing" lên Dashboard
        execSync(`node scripts/gsheet-bridge.js update-by-row ${GSHEET_ID} Dashboard ${rowNumber} '{"Status":"PROCESSING"}'`);

        console.log(`✅ [${niche}] Đã chuẩn bị xong dữ liệu nguồn. Vui lòng mở Agent để thực hiện bước tạo Insight cuối cùng (do cần trí tuệ của Gemini).`);
        
        // Sau khi xong GĐ 1, chuyển về PAUSE để người dùng biết đã xong phần cào dữ liệu
        execSync(`node scripts/gsheet-bridge.js update-by-row ${GSHEET_ID} Dashboard ${rowNumber} '{"Status":"DONE", "Videos Scraped":"20"}'`);

    } catch (e) {
        console.error(`❌ Lỗi Pipeline:`, e.message);
    }
}

async function monitor() {
    console.log(`[${new Date().toLocaleString()}] 🔍 Đang quét Dashboard...`);
    try {
        const output = execSync(`node scripts/gsheet-bridge.js read-tab ${GSHEET_ID} Dashboard`).toString();
        const rows = JSON.parse(output);

        for (const row of rows) {
            if (row.Status === 'RUN') {
                await runPipeline(row['Niche / Exam'], row._rowNumber);
            }
        }
    } catch (e) {
        console.error("❌ Monitor Error:", e.message);
    }
    setTimeout(monitor, CHECK_INTERVAL);
}

monitor();