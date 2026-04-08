const { ApifyClient } = require('apify-client');
require('dotenv').config();

const client = new ApifyClient({
    token: process.env.APIFY_TOKEN,
});

async function run(videoId) {
    const url = `https://www.youtube.com/watch?v=${videoId}`;
    
    // Sử dụng streamers/youtube-scraper
    const run = await client.actor('streamers/youtube-scraper').call({
        urls: [url],
        downloadSubtitles: true,
        saveCaptions: true,
        maxComments: 20
    });

    const { items } = await client.dataset(run.defaultDatasetId).listItems();
    
    if (items.length > 0) {
        console.log(items[0].transcript || "Không tìm thấy nội dung transcript.");
    } else {
        console.log("Apify không trả về kết quả nào.");
    }
}

run(process.argv[2]).catch(console.error);
