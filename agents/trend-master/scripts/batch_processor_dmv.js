const fs = require('fs');
const { execSync } = require('child_process');
const path = require('path');

function getVideoId(link) {
    if (link.includes('youtube.com') || link.includes('youtu.be')) {
        const url = new URL(link);
        if (link.includes('youtube.com/watch')) return url.searchParams.get('v');
        if (link.includes('youtu.be/')) return url.pathname.slice(1);
    } else if (link.includes('tiktok.com')) {
        const parts = link.split('/');
        const lastPart = parts[parts.length - 1].split('?')[0];
        if (link.includes('/video/')) return lastPart;
        // For /discover/ or /content/ links, use a slugified version of the link
        return lastPart || 'tt-' + Math.random().toString(36).substring(7);
    }
    return null;
}

async function processBatch() {
    const results = JSON.parse(fs.readFileSync('discovery_results.json', 'utf8'));
    console.log(`🚀 Starting batch processing for ${results.length} entries...`);

    for (let i = 0; i < results.length; i++) {
        const video = results[i];
        const videoId = getVideoId(video.link);
        
        if (!videoId) {
            console.warn(`[${i+1}/${results.length}] ⚠️ Could not extract ID for: ${video.link}`);
            continue;
        }

        const videoDir = path.join('data', videoId);
        if (!fs.existsSync(videoDir)) {
            fs.mkdirSync(videoDir, { recursive: true });
        }

        const commentsFile = path.join(videoDir, 'comments.json');
        if (!fs.existsSync(commentsFile)) {
            console.log(`[${i+1}/${results.length}] Mining ${video.platform} comments for: ${video.link}`);
            try {
                if (video.platform === 'YouTube') {
                    execSync(`node scripts/local-yt-engine.js "${video.link}" "${commentsFile}"`, { stdio: 'inherit' });
                } else if (video.platform === 'TikTok') {
                    // local-tt-engine.js has a different CLI: node local-tt-engine.js mine "url"
                    // and it hardcodes output to 'comments_clean.json'
                    // We need to move it after completion
                    execSync(`node scripts/local-tt-engine.js mine "${video.link}"`, { stdio: 'inherit' });
                    if (fs.existsSync('comments_clean.json')) {
                        fs.renameSync('comments_clean.json', commentsFile);
                    }
                }
            } catch (e) {
                console.error(`❌ Failed to mine comments for ${videoId}: ${e.message}`);
            }
        } else {
            console.log(`[${i+1}/${results.length}] Comments already exist for: ${videoId}`);
        }
    }

    console.log("✅ Batch processing finished.");
}

processBatch();