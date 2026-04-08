const fs = require('fs');
const { ApifyClient } = require('apify-client');
require('dotenv').config();

const client = new ApifyClient({
    token: process.env.APIFY_TOKEN,
});

async function run(videoId) {
    const url = `https://www.youtube.com/watch?v=${videoId}`;
    console.log(`Đang truy quét Transcript cho: ${url}`);

    try {
        const run = await client.actor('streamers/youtube-scraper').call({
            "startUrls": [{ "url": url }],
            "maxResults": 1,
            "subtitlesLanguage": "en",
            "downloadSubtitles": true,
            "saveCaptions": true
        });

        const { items } = await client.dataset(run.defaultDatasetId).listItems();
        
        if (items.length > 0) {
            const item = items[0];
            let transcriptText = "";

            // Trích xuất text từ mảng srt của Apify
            if (item.subtitles && Array.isArray(item.subtitles) && item.subtitles[0].srt) {
                transcriptText = item.subtitles[0].srt;
            } else if (item.caption) {
                transcriptText = item.caption;
            }

            if (transcriptText) {
                // Đảm bảo thư mục reports tồn tại
                if (!fs.existsSync('./reports')) fs.mkdirSync('./reports');
                
                // Lưu transcript sạch vào file
                fs.writeFileSync(`./reports/${videoId}_transcript.txt`, transcriptText);
                console.log(`ĐÃ LƯU TRANSCRIPT VÀO: reports/${videoId}_transcript.txt`);
                
                // Trả về JSON cho các mục đích khác nếu cần
                console.log(JSON.stringify({ title: item.title, id: vId = videoId }, null, 2));
            } else {
                console.log("KHÔNG TÌM THẤY NỘI DUNG TRANSCRIPT TRONG DỮ LIỆU TRẢ VỀ.");
            }
        }
    } catch (e) {
        console.error("LỖI THỰC THI: " + e.message);
    }
}

run(process.argv[2]).catch(console.error);
