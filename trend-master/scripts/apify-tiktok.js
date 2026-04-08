const { ApifyClient } = require('apify-client');
require('dotenv').config();

const client = new ApifyClient({
    token: process.env.APIFY_TOKEN,
});

async function run(tiktokUrl) {
    console.error(`Fetching TikTok data for: ${tiktokUrl}`);

    try {
        const run = await client.actor('clockworks/tiktok-scraper').call({
            "postURLs": [tiktokUrl],
            "maxComments": 500,
            "commentsLanguage": "en"
        });

        const { items } = await client.dataset(run.defaultDatasetId).listItems();
        
        if (items.length > 0) {
            const item = items[0];
            // Get Direct Video URL and Comments
            console.log(JSON.stringify({
                videoId: item.id,
                description: item.text,
                videoUrl: item.videoUrl || item.downloadAddr,
                comments: (item.comments || []).map(c => ({
                    text: c.text,
                    author: c.authorMeta.nickName,
                    likes: c.diggCount
                }))
            }, null, 2));
        } else {
            console.error("No data returned from Apify.");
        }
    } catch (e) {
        console.error("Execution error: " + e.message);
    }
}

run(process.argv[2]).catch(console.error);
