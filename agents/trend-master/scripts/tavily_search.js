const axios = require('axios');
const fs = require('fs');

let TAVILY_API_KEY = "";
if (fs.existsSync('.env')) {
    const env = fs.readFileSync('.env', 'utf-8');
    const lines = env.split('\n');
    for (const line of lines) {
        if (line.startsWith('TAVILY_API_KEY=')) {
            TAVILY_API_KEY = line.split('=')[1].trim();
        }
    }
}

async function tavilySearch(query) {
    try {
        const response = await axios.post('https://api.tavily.com/search', {
            api_key: TAVILY_API_KEY,
            query: query,
            search_depth: "basic",
            max_results: 10
        });
        return response.data.results;
    } catch (e) {
        console.error(e.message);
        return [];
    }
}

async function run() {
    const niche = process.argv[2] || "DMV";
    console.log(`Searching TikTok for ${niche}...`);
    const tiktokRes = await tavilySearch(`site:tiktok.com "${niche}" 2026`);
    console.log("TIKTOK_TITLES");
    tiktokRes.forEach(r => console.log(`- ${r.title}`));

    console.log(`Searching Reddit for ${niche}...`);
    const redditRes = await tavilySearch(`site:reddit.com "${niche}" exam 2026`);
    console.log("REDDIT_TITLES");
    redditRes.forEach(r => console.log(`- ${r.title}`));
}

run();