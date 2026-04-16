const { JWT } = require('google-auth-library');
const axios = require('axios');
const fs = require('fs');
const path = require('path');

// Load environment variables manually
if (fs.existsSync('.env')) {
    const env = fs.readFileSync('.env', 'utf8');
    env.split('\n').forEach(line => {
        const [key, value] = line.split('=');
        if (key && value) process.env[key.trim()] = value.trim();
    });
}

const TAVILY_API_KEY = process.env.TAVILY_API_KEY;
const MAX_SOURCES_PER_KEYWORD = 20;

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
    console.log(`🔍 YouTube: ${keyword}`);
    const oneYearAgo = new Date();
    oneYearAgo.setFullYear(oneYearAgo.getFullYear() - 1);
    try {
        const response = await axios.get('https://www.googleapis.com/youtube/v3/search', {
            params: {
                part: 'snippet',
                q: keyword,
                type: 'video',
                maxResults: 15,
                regionCode: 'US',
                relevanceLanguage: 'en',
                publishedAfter: oneYearAgo.toISOString()
            },
            headers: { Authorization: `Bearer ${accessToken}` }
        });

        const videoIds = response.data.items.map(item => item.id.videoId).join(',');
        if (!videoIds) return [];

        const statsResponse = await axios.get('https://www.googleapis.com/youtube/v3/videos', {
            params: { part: 'statistics,snippet', id: videoIds },
            headers: { Authorization: `Bearer ${accessToken}` }
        });

        return statsResponse.data.items.map(item => ({
            keyword,
            link: `https://www.youtube.com/watch?v=${item.id}`,
            platform: 'YouTube',
            view: item.statistics.viewCount,
            like: item.statistics.likeCount || "0",
            title: item.snippet.title,
            status: 'new'
        }));
    } catch (e) {
        console.error(`❌ YT Error: ${e.message}`);
        return [];
    }
}

async function searchTavily(query, site) {
    console.log(`🔍 Tavily (${site}): ${query}`);
    try {
        const response = await axios.post('https://api.tavily.com/search', {
            api_key: TAVILY_API_KEY,
            query: `site:${site} ${query}`,
            search_depth: "advanced",
            max_results: 15
        });
        return response.data.results.map(r => ({
            keyword: query,
            link: r.url,
            platform: site.includes('tiktok') ? 'TikTok' : 'Reddit',
            view: "0", 
            like: "5000", // Giả định đạt chuẩn để pass filter ban đầu, sẽ check sâu ở GĐ 2
            title: r.title,
            content: r.content,
            status: 'new'
        }));
    } catch (e) {
        console.error(`❌ Tavily Error (${site}): ${e.message}`);
        return [];
    }
}

async function main() {
    const keyword = process.argv[2];
    if (!keyword) {
        console.error("Please provide a keyword.");
        process.exit(1);
    }

    let youtubeToken;
    try { youtubeToken = await getYouTubeAccessToken(); } catch (e) { console.error(e.message); return; }

    console.log(`🚀 Gathering sources for: ${keyword}`);
    
    // Thu thập đa nền tảng
    const [yt, tiktok, reddit] = await Promise.all([
        searchYouTube(keyword, youtubeToken),
        searchTavily(keyword, "tiktok.com"),
        searchTavily(keyword, "reddit.com")
    ]);

    let allSources = [...yt, ...tiktok, ...reddit];

    // Bộ lọc rác cơ bản
    const excludedKeywords = ['meme', 'reaction', 'funny', 'motivation', 'vlog', 'prank', 'rant', 'spam'];
    let filtered = allSources.filter(item => {
        const title = (item.title || "").toLowerCase();
        return !excludedKeywords.some(kw => title.includes(kw));
    });

    // Giới hạn 20 links
    const uniqueLinks = new Set();
    const finalSources = [];
    for (const source of filtered) {
        if (!uniqueLinks.has(source.link)) {
            uniqueLinks.add(source.link);
            finalSources.push(source);
        }
        if (finalSources.length >= MAX_SOURCES_PER_KEYWORD) break;
    }

    fs.writeFileSync('discovery_results.json', JSON.stringify(finalSources, null, 2));
    console.log(`✅ Collected ${finalSources.length} sources (Limit: 20).`);
}

main();