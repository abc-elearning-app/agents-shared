const { ApifyClient } = require('apify-client');
require('dotenv').config();

const client = new ApifyClient({
    token: process.env.APIFY_TOKEN,
});

async function run(videoId) {
    const url = `https://www.youtube.com/watch?v=${videoId}`;
    console.log(`Đang truy quét transcript thực tế cho: ${url}`);

    try {
        const run = await client.actor('heinstev/youtube-transcript-scraper').call({
            url: url,
        });

        const { items } = await client.dataset(run.defaultDatasetId).listItems();
        
        if (items.length > 0) {
            // Trả về toàn bộ text để tôi đọc
            console.log(items.map(i => i.text).join(' '));
        } else {
            console.log("LỖI: Không tìm thấy transcript.");
        }
    } catch (e) {
        console.log("LỖI API: " + e.message);
    }
}

run(process.argv[2]).catch(console.error);
