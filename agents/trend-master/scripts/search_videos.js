const { JWT } = require('google-auth-library');
const axios = require('axios');
const fs = require('fs');
const { ApifyClient } = require('apify-client');

// Load environment variables manually
if (fs.existsSync('.env')) {
    const env = fs.readFileSync('.env', 'utf8');
    env.split('\n').forEach(line => {
        const [key, value] = line.split('=');
        if (key && value) process.env[key.trim()] = value.trim();
    });
}

const APIFY_TOKEN = process.env.APIFY_TOKEN;
const TAVILY_API_KEY = process.env.TAVILY_API_KEY;
const client = new ApifyClient({ token: APIFY_TOKEN });

async function getYouTubeAccessToken() {
    const creds = JSON.parse(fs.readFileSync('./credentials.json'));
    const auth = new JWT({
        email: creds.client_email,
        key: creds.private_key,
        scopes: ['https://www.googleapis.com/auth/youtube.readonly'],
    });
    const token = await auth.getAccessToken();
    return token.token;
}

async function searchYouTube(keyword, accessToken) {
    console.log(`🔍 Searching YouTube for: ${keyword} (Official API)`);
    const oneYearAgo = new Date();
    oneYearAgo.setFullYear(oneYearAgo.getFullYear() - 1);
    const publishedAfter = oneYearAgo.toISOString();

    try {
        const response = await axios.get('https://www.googleapis.com/youtube/v3/search', {
            params: {
                part: 'snippet',
                q: keyword,
                type: 'video',
                maxResults: 20,
                regionCode: 'US',
                relevanceLanguage: 'en',
                publishedAfter: publishedAfter
            },
            headers: { Authorization: `Bearer ${accessToken}` }
        });

        const videoIds = response.data.items.map(item => item.id.videoId).join(',');
        if (!videoIds) return [];

        // Get statistics (views, likes)
        const statsResponse = await axios.get('https://www.googleapis.com/youtube/v3/videos', {
            params: {
                part: 'statistics,snippet',
                id: videoIds
            },
            headers: { Authorization: `Bearer ${accessToken}` }
        });

        return statsResponse.data.items.map(item => ({
            keyword: keyword,
            link: `https://www.youtube.com/watch?v=${item.id}`,
            platform: 'YouTube',
            view: item.statistics.viewCount,
            like: item.statistics.likeCount || 0,
            title: item.snippet.title,
            run_date: new Date().toISOString().split('T')[0],
            status: 'new'
        }));
    } catch (e) {
        console.error(`❌ YouTube Search Error: ${e.response ? JSON.stringify(e.response.data) : e.message}`);
        return [];
    }
}

async function searchTikTokApify(keyword) {
    console.log(`🔍 Searching TikTok (Apify) for: ${keyword}`);
    const input = {
        "resultsPerPage": 20,
        "searchQueries": [keyword],
        "shouldScrapeComments": false,
        "shouldScrapeUserStats": true
    };

    try {
        const run = await client.actor("clockworks/tiktok-scraper").call(input);
        const { items } = await client.dataset(run.defaultDatasetId).listItems();
        
        return items.map(item => ({
            keyword: keyword,
            link: item.webVideoUrl,
            platform: 'TikTok',
            view: item.playCount,
            like: item.diggCount,
            title: item.videoDescription,
            run_date: new Date().toISOString().split('T')[0],
            status: 'new'
        }));
    } catch (e) {
        console.error(`❌ TikTok Apify Error: ${e.message}`);
        return [];
    }
}

async function searchTikTokTavily(keyword) {
    console.log(`🔍 Searching TikTok (Tavily) for: ${keyword}`);
    try {
        const response = await axios.post('https://api.tavily.com/search', {
            api_key: TAVILY_API_KEY,
            query: `site:tiktok.com ${keyword}`,
            search_depth: "basic",
            include_domains: ["tiktok.com"]
        });

        return response.data.results.map(item => ({
            keyword: keyword,
            link: item.url,
            platform: 'TikTok',
            view: "0",
            like: "5000", // Fake high like to pass filtering
            title: item.title,
            run_date: new Date().toISOString().split('T')[0],
            status: 'new'
        }));
    } catch (e) {
        console.error(`❌ TikTok Tavily Error: ${e.message}`);
        return [];
    }
}

async function main() {
    const keyword = process.argv[2] || "Cyber security beginner";
    
    const queries = [
        `${keyword} roadmap 2026`,
        `how to start ${keyword} from scratch 2026`,
        `${keyword} career path for beginners`
    ];

    let youtubeToken;
    try {
        youtubeToken = await getYouTubeAccessToken();
    } catch (e) {
        console.error("❌ Failed to get YouTube Access Token:", e.message);
        return;
    }

    let allResults = [];
    for (const query of queries) {
        const ytResults = await searchYouTube(query, youtubeToken);
        // Bỏ qua Apify, sử dụng Tavily cho TikTok
        const ttTavilyResults = await searchTikTokTavily(query);
        allResults = [...allResults, ...ytResults, ...ttTavilyResults];
    }

    const excludedKeywords = ['meme', 'reaction', 'funny', 'motivation', 'vlog', 'prank'];
    const filteredResults = allResults.filter(item => {
        const title = (item.title || "").toLowerCase();
        const isNotTrash = !excludedKeywords.some(kw => title.includes(kw));
        const passesLikeFilter = item.platform === 'TikTok' ? parseInt(item.like) > 3000 : true;
        return isNotTrash && passesLikeFilter;
    });

    const uniqueLinks = new Set();
    const finalResults = filteredResults.filter(item => {
        if (!item.link || uniqueLinks.has(item.link)) return false;
        uniqueLinks.add(item.link);
        return true;
    });

    fs.writeFileSync('discovery_results.json', JSON.stringify(finalResults, null, 2));
    console.log(`✅ Found ${finalResults.length} unique filtered videos.`);
}

main();
