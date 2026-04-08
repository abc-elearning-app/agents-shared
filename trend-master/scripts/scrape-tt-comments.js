const { ApifyClient } = require('apify-client');
require('dotenv').config();

const client = new ApifyClient({
    token: process.env.APIFY_TOKEN,
});

async function run(tiktokUrl) {
    console.error(`Fetching TikTok comments for: ${tiktokUrl}`);

    try {
        // Sử dụng Actor chuyên biệt cho comment để đảm bảo ổn định
        const run = await client.actor('clockworks/tiktok-comments-scraper').call({
            "postURLs": [tiktokUrl],
            "maxComments": 100
        });

        const { items } = await client.dataset(run.defaultDatasetId).listItems();
        
        // Cấu trúc dữ liệu trả về từ clockworks/tiktok-comments-scraper
        const allComments = items.map(c => ({
            text: c.text,
            likes: c.diggCount,
            author: c.uniqueId || 'unknown',
            createTime: c.createTimeISO
        }));

        console.log(JSON.stringify(allComments, null, 2));
    } catch (e) {
        console.error("Error: " + e.message);
    }
}

run(process.argv[2]).catch(console.error);
