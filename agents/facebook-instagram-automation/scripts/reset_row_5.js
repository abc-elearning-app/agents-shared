const axios = require('axios');

const SPREADSHEET_ID = '13j1j4kL6XPGxfwPUSwItOP0nAwyaOhLSoVmvb5LWI6k';
const CLIENT_ID = process.env.GOOGLE_CLIENT_ID;
const CLIENT_SECRET = process.env.GOOGLE_CLIENT_SECRET;
const REFRESH_TOKEN = process.env.GOOGLE_REFRESH_TOKEN;

async function reset() {
    const res = await axios.post('https://oauth2.googleapis.com/token', {
        client_id: CLIENT_ID,
        client_secret: CLIENT_SECRET,
        refresh_token: REFRESH_TOKEN,
        grant_type: 'refresh_token'
    });
    const token = res.data.access_token;
    
    await axios.put(`https://sheets.googleapis.com/v4/spreadsheets/${SPREADSHEET_ID}/values/Ảnh câu hỏi scale!E5?valueInputOption=RAW`, 
        { values: [['FB Done']] },
        { headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' } }
    );
    console.log('Row 5 reset to FB Done using axios.');
}
reset();
