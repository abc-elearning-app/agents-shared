const { ApifyClient } = require('apify-client');
require('dotenv').config();

const client = new ApifyClient({
    token: process.env.APIFY_TOKEN,
});

async function run(videoId) {
    const url = `https://www.youtube.com/watch?v=${videoId}`;
    console.error(`Fetching deep data for: ${url}`);

    try {
        const run = await client.actor('streamers/youtube-scraper').call({
            "startUrls": [{ "url": url }],
            "maxResults": 1,
            "maxComments": 20,
            "subtitlesLanguage": "en",
            "downloadSubtitles": true,
            "saveCaptions": true
        });

        const { items } = await client.dataset(run.defaultDatasetId).listItems();
        
        if (items.length > 0) {
            const item = items[0];
            const transcript = (item.subtitles && item.subtitles[0] && item.subtitles[0].srt) || item.caption || item.transcript || "";
            const comments = (item.comments || []).map(c => ({
                text: c.text,
                author: c.authorText,
                likes: c.likesCount
            }));

            console.log(JSON.stringify({
                videoId,
                title: item.title,
                transcript,
                comments
            }, null, 2));
        } else {
            console.error("No data returned from Apify.");
        }
    } catch (e) {
        console.error("Execution error: " + e.message);
    }
}

run(process.argv[2]).catch(console.error);
