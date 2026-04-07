const { execSync } = require('child_process');
const fs = require('fs');
require('dotenv').config();

const SPREADSHEET_ID = process.env.GSHEET_ID;
const CHECK_INTERVAL = 60 * 1000; // 1 phút quét một lần

console.log('🚀 TREND MASTER AUTOMATION: Hệ thống đang chạy ngầm...');
console.log('--- Đang giám sát Google Sheet: ' + SPREADSHEET_ID);

async function checkAndProcess() {
    try {
        // 1. Đọc dữ liệu từ sheet
        const output = execSync(`node scripts/gsheet-bridge.js read-tab ${SPREADSHEET_ID} Video_Discovery`).toString();
        const rows = JSON.parse(output.replace('Output: ', ''));

        // 2. Tìm các dòng 'approved' hoặc 'run'
        const approvedRows = rows.filter(r => r.status === 'approved');
        const runRows = rows.filter(r => r.status === 'run');

        // Xử lý tác vụ Discovery (run)
        for (const row of runRows) {
            console.log(`🔍 Phát hiện keyword mới: ${row.keyword}`);
            execSync(`node scripts/video-api-bridge.js search "${row.keyword}" > discovery_results.json`);
            // (Logic ghi kết quả và update status done - tôi sẽ dùng lại các lệnh gsheet-bridge)
            console.log(`✅ Hoàn thành Discovery cho: ${row.keyword}`);
        }

        // Xử lý tác vụ Deep Analysis (approved) - Chế độ Tổng hợp (Synthesis)
        if (approvedRows.length > 0) {
            console.log(`🔥 Phát hiện ${approvedRows.length} video được approved. Bắt đầu thu thập dữ liệu tổng hợp...`);
            
            for (const row of approvedRows) {
                const videoId = row.video_url.includes('v=') ? row.video_url.split('v=')[1].split('&')[0] : row.video_url.split('/').pop();
                
                console.log(`   -> Đang xử lý: ${row.video_url}`);
                
                // Chạy Pipeline nặng: Tải, Gỡ băng, Đào comment
                try {
                    if (row.platform_found === 'TikTok') {
                        execSync(`node scripts/local-tt-engine.js ${row.video_url}`);
                        execSync(`yt-dlp -x --audio-format mp3 -o "temp_audio.mp3" ${row.video_url}`);
                        execSync(`python3 scripts/transcribe_local.py temp_audio.mp3 > reports/${videoId}_transcript.txt`);
                    } else {
                        execSync(`yt-dlp -x --audio-format mp3 -o "temp_audio.mp3" ${row.video_url}`);
                        execSync(`python3 scripts/transcribe_local.py temp_audio.mp3 > reports/${videoId}_transcript.txt`);
                        execSync(`node scripts/apify-youtube-v3.js ${videoId}`);
                    }
                    
                    // Đánh dấu đã thu thập xong để chờ AI bóc Insight
                    console.log(`   ✅ Đã thu thập xong dữ liệu cho video này.`);
                } catch (e) {
                    console.error(`   ❌ Lỗi khi xử lý video: ${e.message}`);
                }
            }

            // Gửi thông báo lên MacOS
            execSync(`osascript -e 'display notification "Đã thu thập xong dữ liệu cho ${approvedRows.length} video. Mời sếp vào chat để bóc Insight!" with title "TREND MASTER READY"'`);
        }

    } catch (err) {
        console.error('Lỗi Monitor:', err.message);
    }
}

// Bắt đầu vòng lặp
setInterval(checkAndProcess, CHECK_INTERVAL);
checkAndProcess();
