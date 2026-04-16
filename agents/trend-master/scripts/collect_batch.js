const fs = require('fs');
const { execSync } = require('child_process');
const path = require('path');

const batch = JSON.parse(fs.readFileSync('batch_sample.json', 'utf8'));
const dataDir = path.join(__dirname, '../data');
if (!fs.existsSync(dataDir)) fs.mkdirSync(dataDir);

async function collectData() {
    for (let i = 0; i < batch.length; i++) {
        const video = batch[i];
        const videoId = video.link.includes('v=') ? video.link.split('v=')[1].split('&')[0] : video.link.split('/').pop().split('?')[0];
        const vDir = path.join(dataDir, videoId);
        if (!fs.existsSync(vDir)) fs.mkdirSync(vDir);

        console.log(`[${i+1}/${batch.length}] Processing ${video.platform}: ${video.link}`);

        // 1. Transcript
        try {
            if (video.platform === 'YouTube') {
                // Try to get auto-subs first
                try {
                    execSync(`yt-dlp --write-auto-subs --sub-lang en --skip-download --output "${vDir}/transcript" "${video.link}"`, { stdio: 'ignore' });
                    // Check if .vtt exists
                    const vttFile = path.join(vDir, 'transcript.en.vtt');
                    if (fs.existsSync(vttFile)) {
                        console.log(`   - YT Transcript (VTT) found.`);
                        // Convert VTT to text (simple stripping)
                        const vttContent = fs.readFileSync(vttFile, 'utf8');
                        const text = vttContent.replace(/<[^>]*>/g, '').replace(/\d{2}:\d{2}:\d{2}\.\d{3} --> \d{2}:\d{2}:\d{2}\.\d{3}/g, '').trim();
                        fs.writeFileSync(path.join(vDir, 'transcript.txt'), text);
                    } else {
                        throw new Error('VTT not found');
                    }
                } catch (e) {
                    // Fallback to whisper
                    console.log(`   - No YT subs. Downloading audio...`);
                    execSync(`yt-dlp -x --audio-format mp3 -o "${vDir}/audio.%(ext)s" "${video.link}"`, { stdio: 'ignore' });
                    console.log(`   - Transcribing with Whisper...`);
                    const transcript = execSync(`python3 scripts/transcribe_local.py "${vDir}/audio.mp3"`).toString();
                    fs.writeFileSync(path.join(vDir, 'transcript.txt'), transcript);
                }
            } else if (video.platform === 'TikTok' || video.platform === 'Tiktok') {
                console.log(`   - Downloading TikTok audio...`);
                execSync(`yt-dlp -x --audio-format mp3 -o "${vDir}/audio.%(ext)s" "${video.link}"`, { stdio: 'ignore' });
                console.log(`   - Transcribing with Whisper...`);
                const transcript = execSync(`python3 scripts/transcribe_local.py "${vDir}/audio.mp3"`).toString();
                fs.writeFileSync(path.join(vDir, 'transcript.txt'), transcript);
            }
        } catch (e) {
            console.error(`   - Transcript Error: ${e.message}`);
        }

        // 2. Comments
        try {
            if (video.platform === 'YouTube') {
                execSync(`node scripts/local-yt-engine.js "${video.link}"`, { stdio: 'ignore' });
                if (fs.existsSync('comments_clean.json')) {
                    fs.renameSync('comments_clean.json', path.join(vDir, 'comments.json'));
                    console.log(`   - YT Comments collected.`);
                }
            } else if (video.platform === 'TikTok' || video.platform === 'Tiktok') {
                execSync(`node scripts/local-tt-engine.js mine "${video.link}"`, { stdio: 'ignore' });
                if (fs.existsSync('comments_clean.json')) {
                    fs.renameSync('comments_clean.json', path.join(vDir, 'comments.json'));
                    console.log(`   - TikTok Comments collected.`);
                }
            }
        } catch (e) {
            console.error(`   - Comments Error: ${e.message}`);
        }
    }
}

collectData();
