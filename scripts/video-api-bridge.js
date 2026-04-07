const { ApifyClient } = require('apify-client');
const axios = require('axios');
require('dotenv').config();

const YOUTUBE_API_KEY = "AIzaSyDqMZL-HCgM3Z8xsoN0hy_3OcoQQb5ftaE";
const APIFY_TOKEN = process.env.APIFY_TOKEN;
const apifyClient = new ApifyClient({ token: APIFY_TOKEN });

const bridge = {
    // === LUỒNG YOUTUBE (Dùng API chính thức) ===
    searchYouTube: async (keyword) => {
        const date = new Date();
        date.setFullYear(date.getFullYear() - 1); // Bộ lọc 1 năm cho YouTube
        const publishedAfter = date.toISOString();
        
        // 1. Tìm video viral
        const searchUrl = `https://www.googleapis.com/youtube/v3/search?part=snippet&q=${encodeURIComponent(keyword)}&type=video&order=viewCount&publishedAfter=${publishedAfter}&maxResults=15&key=${YOUTUBE_API_KEY}`;
        const searchRes = await axios.get(searchUrl);
        const items = searchRes.data.items || [];
        
        const videoIds = items.map(item => item.id.videoId).join(',');
        if (!videoIds) return [];

        // 2. Lấy số liệu Statistics thật
        const statsUrl = `https://www.googleapis.com/youtube/v3/videos?part=snippet,statistics&id=${videoIds}&key=${YOUTUBE_API_KEY}`;
        const statsRes = await axios.get(statsUrl);
        
        return statsRes.data.items.slice(0, 15).map(v => ({
            keyword: keyword,
            platform_found: 'YouTube',
            video_url: `https://www.youtube.com/watch?v=${v.id}`,
            video_title: v.snippet.title,
            channel_name: v.snippet.channelTitle,
            views: v.statistics.viewCount,
            likes: v.statistics.likeCount || 0,
            run_date: new Date().toISOString().split('T')[0],
            status: 'new'
        }));
    },

    // === LUỒNG TIKTOK (Dùng Apify với Payload chuẩn) ===
    searchTikTok: async (keyword) => {
        const input = {
            "searchQueries": [keyword],
            "resultsPerPage": 30,
            "searchSection": "/video",
            "searchSorting": "1", // POPULAR
            "searchDatePosted": "5", // This Year (Sát nhất với 6 tháng)
            "shouldDownloadVideos": false,
            "downloadSubtitlesOptions": "NEVER_DOWNLOAD_SUBTITLES"
        };

        const run = await apifyClient.actor('clockworks/tiktok-scraper').call(input);
        const { items } = await apifyClient.dataset(run.defaultDatasetId).listItems();
        
        return items.filter(v => v.playCount >= 10000).map(v => ({
            keyword: keyword,
            platform_found: 'TikTok',
            video_url: v.webVideoUrl,
            video_title: v.videoDescription,
            channel_name: v.authorMeta ? v.authorMeta.name : 'Unknown',
            views: v.playCount,
            likes: v.diggCount,
            run_date: new Date().toISOString().split('T')[0],
            status: 'new'
        }));
    },

    // === DEEP DIVE TIKTOK ===
    deepDiveTikTok: async (videoUrl) => {
        const videoRun = await apifyClient.actor('clockworks/tiktok-scraper').call({
            "postURLs": [videoUrl],
            "shouldDownloadVideos": true,
            "downloadSubtitlesOptions": "ALWAYS_DOWNLOAD_SUBTITLES"
        });
        const videoData = (await apifyClient.dataset(videoRun.defaultDatasetId).listItems()).items[0];

        const commentRun = await apifyClient.actor('clockworks/tiktok-comments-scraper').call({
            "postURLs": [videoUrl],
            "maxComments": 100
        });
        const comments = (await apifyClient.dataset(commentRun.defaultDatasetId).listItems()).items;

        return {
            ...videoData,
            comments: comments.map(c => ({
                text: c.text,
                author: c.uniqueId,
                likes: c.diggCount
            }))
        };
    }
};

const [,, cmd, keyword] = process.argv;
if (cmd === 'search') {
    Promise.all([bridge.searchYouTube(keyword), bridge.searchTikTok(keyword)])
        .then(results => console.log(JSON.stringify(results.flat())))
        .catch(err => console.error(err.message));
}
