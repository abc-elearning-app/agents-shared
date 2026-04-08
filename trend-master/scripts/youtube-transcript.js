const fs = require('fs');
const https = require('https');

async function getAccessToken() {
    const creds = JSON.parse(fs.readFileSync('./credentials_oauth.json'));
    const postData = JSON.stringify({
        client_id: creds.client_id,
        client_secret: creds.client_secret,
        refresh_token: creds.refresh_token,
        grant_type: 'refresh_token'
    });

    return new Promise((resolve, reject) => {
        const req = https.request({
            hostname: 'oauth2.googleapis.com',
            path: '/token',
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Content-Length': postData.length
            }
        }, (res) => {
            let data = '';
            res.on('data', (chunk) => data += chunk);
            res.on('end', () => resolve(JSON.parse(data).access_token));
        });
        req.on('error', reject);
        req.write(postData);
        req.end();
    });
}

async function getTranscript(videoId) {
    const accessToken = await getAccessToken();
    
    // 1. Get caption list
    const listUrl = `https://www.googleapis.com/youtube/v3/captions?part=snippet&videoId=${videoId}`;
    const captionsResponse = await new Promise((resolve) => {
        https.get(listUrl, { headers: { 'Authorization': `Bearer ${accessToken}` } }, (res) => {
            let data = '';
            res.on('data', (chunk) => data += chunk);
            res.on('end', () => resolve(JSON.parse(data)));
        });
    });

    if (!captionsResponse.items || captionsResponse.items.length === 0) {
        console.log("Không tìm thấy transcript cho video này.");
        return;
    }

    // Pick the first available caption (usually English or auto-generated)
    const captionId = captionsResponse.items[0].id;
    
    // 2. Download caption content
    const downloadUrl = `https://www.googleapis.com/youtube/v3/captions/${captionId}?tfmt=vtt`;
    https.get(downloadUrl, { headers: { 'Authorization': `Bearer ${accessToken}` } }, (res) => {
        let data = '';
        res.on('data', (chunk) => data += chunk);
        res.on('end', () => {
            console.log(data); // Output the transcript content
        });
    });
}

const videoId = process.argv[2];
if (videoId) {
    getTranscript(videoId).catch(console.error);
}
