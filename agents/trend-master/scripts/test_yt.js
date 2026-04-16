const { JWT } = require('google-auth-library');
const axios = require('axios');
const fs = require('fs');

async function testYouTube() {
    const creds = JSON.parse(fs.readFileSync('./credentials.json'));
    const auth = new JWT({
        email: creds.client_email,
        key: creds.private_key,
        scopes: ['https://www.googleapis.com/auth/youtube.readonly'],
    });

    try {
        const token = await auth.getAccessToken();
        console.log('Access Token obtained');
        
        const response = await axios.get('https://www.googleapis.com/youtube/v3/search', {
            params: {
                part: 'snippet',
                q: 'cyber security beginner',
                type: 'video',
                maxResults: 5
            },
            headers: {
                Authorization: `Bearer ${token.token}`
            }
        });
        console.log('Search successful:', response.data.items.length, 'results');
    } catch (e) {
        console.error('Error:', e.response ? e.response.data : e.message);
    }
}

testYouTube();
