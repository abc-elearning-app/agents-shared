const path = require('path');
const fs = require('fs');
const { google } = require('googleapis');
const axios = require('axios');
const FormData = require('form-data');
const cloudinary = require('cloudinary').v2;

// --- CONFIGURATION ---
const SPREADSHEET_ID = '13j1j4kL6XPGxfwPUSwItOP0nAwyaOhLSoVmvb5LWI6k';
const RANGE = 'Ảnh câu hỏi scale!A2:M100'; 

// Cloudinary Config
cloudinary.config({ 
  cloud_name: 'domqhgrzf', 
  api_key: '398619221526384', 
  api_secret: 's9c_gx8NFRPm-JKDWf155iOY_T8' 
});

// Google Auth
const CLIENT_ID = process.env.GOOGLE_CLIENT_ID;
const CLIENT_SECRET = process.env.GOOGLE_CLIENT_SECRET;
const REFRESH_TOKEN = process.env.GOOGLE_REFRESH_TOKEN;

const auth = new google.auth.OAuth2(CLIENT_ID, CLIENT_SECRET, 'http://localhost');
auth.setCredentials({ refresh_token: REFRESH_TOKEN });
const sheets = google.sheets({ version: 'v4', auth });

// Facebook Config & EXACT CTAs
const FB_USER_TOKEN = process.env.FB_USER_TOKEN;
const FB_PAGE_MAPPING = {
    'Comptia Easy Prep': { 
        id: '1056781517514830', 
        cta: `🚀 Pass CompTIA faster with smarter prep
💡 Start free: https://abc-elearning.org/comptiaeasyprep/our-apps
Why rely on scattered materials when you can train like the real exam?
✅ Performance-based questions
✅ Personalized study plans
✅ AI-powered guidance
✅ Real exam simulations
✅ Detailed explanations
✅ Competitive Arena mode`
    },
    'CompTIA Ready': {
        id: '1100672153127813',
        cta: `Practice free today: https://abc-elearning.org/comptiaready/our-apps
👉 Everything you need to ace the exam:
🧩 Performance-Based Questions (PBQs) to train real exam skills
📌 Latest exam questions, always up to date
⚡ Custom tests for focused practice
🤖 AI tutor to guide you while you study
📊 Progress tracking to pinpoint improvements
🎯 Daily challenges to stay consistent`
    },
    'PMP': { 
        id: '1064056686789261', 
        cta: `💡 Practice free today:  https://abc-elearning.org/pmpeasyprep/share/pmp   

🚀 Level up your PMP prep with smarter practice
📘 Real PMP exam-style questions, always up to date  
🎯 Custom quizzes focused on your weak areas  
🧠 AI tutor to guide you while you study  
📈 Progress tracking to see exactly where you improve  
⏱️ Daily challenges to stay consistent  
🏆 Trusted by thousands of PMP candidates`
    },
    'DMV': { 
        id: '972455362628067', 
        cta: `🚗 Prepare smarter for your DMV test
💡 Practice free: https://abc-elearning.org/dmveasyprep/share/dmv
📘 Real exam-style questions by state
🗺️ State-specific practice tests
🎯 Target your weak areas
🧠 Guided support with AI`
    }
};

// Buffer MCP Config
const BUFFER_TOKEN = process.env.BUFFER_TOKEN;
const BUFFER_ORG_ID = process.env.BUFFER_ORG_ID;
const IG_MAPPING = {
    'PMP': '69cb4c51af47dacb6971255e',
    'Comptia Easy Prep': '69ca450caf47dacb696c8d6d',
    'DMV': '69cb4cfaaf47dacb69712771'
};

async function uploadToCloudinary(filePath) {
    console.log(`☁️ Uploading to Cloudinary...`);
    const result = await cloudinary.uploader.upload(filePath, { folder: 'fb_agent' });
    return result.secure_url;
}

async function publishToFacebook(appType, caption, imagePath) {
    const config = FB_PAGE_MAPPING[appType];
    const tokenRes = await axios.get(`https://graph.facebook.com/v25.0/${config.id}`, { params: { fields: 'access_token', access_token: FB_USER_TOKEN } });
    const pageToken = tokenRes.data.access_token;
    
    const form = new FormData();
    form.append('source', fs.createReadStream(imagePath));
    form.append('message', caption);
    form.append('access_token', pageToken);
    
    const postRes = await axios.post(`https://graph.facebook.com/v25.0/${config.id}/photos`, form, { headers: form.getHeaders() });
    const postId = postRes.data.post_id || postRes.data.id;
    return `https://www.facebook.com/${postId}`;
}

async function publishToInstagramMCP(appType, caption, imageUrl) {
    const channelId = IG_MAPPING[appType];
    if (!channelId) return 'Skipped (No IG)';
    
    const res = await axios.post('https://mcp.buffer.com/mcp', {
        jsonrpc: '2.0', id: Date.now(), method: 'tools/call',
        params: { 
            name: 'create_post', 
            arguments: { 
                organizationId: BUFFER_ORG_ID, channelId, text: caption,
                assets: { images: [{ url: imageUrl }] },
                mode: 'shareNow', schedulingType: 'automatic',
                metadata: { instagram: { type: 'post', shouldShareToFeed: true } }
            } 
        }
    }, { headers: { 'Authorization': `Bearer ${BUFFER_TOKEN}`, 'Content-Type': 'application/json', 'Accept': 'application/json, text/event-stream' } });
    
    if (res.data.result && res.data.result.isError) throw new Error(`IG Error: ${res.data.result.content[0].text}`);
    return 'Success';
}

async function updateStatus(rowIndex, status) {
    await sheets.spreadsheets.values.update({
        spreadsheetId: SPREADSHEET_ID,
        range: `Ảnh câu hỏi scale!E${rowIndex}`,
        valueInputOption: 'RAW',
        resource: { values: [[status]] }
    });
}

async function runAutomation() {
    try {
        const response = await sheets.spreadsheets.values.get({ spreadsheetId: SPREADSHEET_ID, range: RANGE });
        const rows = response.data.values;
        if (!rows) return;

        for (let i = 0; i < rows.length; i++) {
            const row = rows[i];
            const rowIndex = i + 2; 
            const account = (row[0] || '').trim(); // A
            const status = (row[4] || '').trim();  // E

            if (status === 'Ready') {
                console.log(`\n🔒 Locking Row ${rowIndex} (Processing)...`);
                await updateStatus(rowIndex, 'Processing');

                try {
                    const title = (row[5] || '').trim();    // F
                    const body = (row[6] || '').trim();     // G
                    const hashtagFb = (row[7] || '').trim(); // H
                    const hashtagIg = (row[8] || '').trim(); // I
                    const imageName = (row[9] || '').trim(); // J
                    
                    const outputPath = path.resolve(__dirname, '..', `${imageName}.png`);
                    if (!fs.existsSync(outputPath)) throw new Error(`Image not found: ${outputPath}`);
                    
                    const cloudinaryUrl = await uploadToCloudinary(outputPath);
                    const config = FB_PAGE_MAPPING[account];
                    if (!config) throw new Error(`No config for account: ${account}`);

                    const fbCaption = `${title}\n\n${body}\n\n${config.cta}\n\n${hashtagFb}`;
                    const igCaption = `${title}\n\n${body}\n\nJoin us for more! 🚀\n\n${hashtagIg}`;

                    console.log(`📢 Posting to FB & IG...`);
                    const fbLink = await publishToFacebook(account, fbCaption, outputPath);
                    const igResult = await publishToInstagramMCP(account, igCaption, cloudinaryUrl);

                    // Update Image Column (J) with Cloudinary URL
                    await sheets.spreadsheets.values.update({
                        spreadsheetId: SPREADSHEET_ID,
                        range: `Ảnh câu hỏi scale!J${rowIndex}`,
                        valueInputOption: 'RAW',
                        resource: { values: [[cloudinaryUrl]] }
                    });

                    // Final Status & Links
                    await sheets.spreadsheets.values.update({
                        spreadsheetId: SPREADSHEET_ID,
                        range: `Ảnh câu hỏi scale!E${rowIndex}`,
                        valueInputOption: 'RAW',
                        resource: { values: [['Done']] }
                    });
                    await sheets.spreadsheets.values.update({
                        spreadsheetId: SPREADSHEET_ID,
                        range: `Ảnh câu hỏi scale!L${rowIndex}:M${rowIndex}`,
                        valueInputOption: 'RAW',
                        resource: { values: [[fbLink, igResult]] }
                    });
                    
                    console.log(`🎉 Row ${rowIndex} Successfully Processed!`);
                } catch (err) { 
                    console.error(`❌ Error row ${rowIndex}:`, err.message); 
                    await updateStatus(rowIndex, 'Error');
                }
            }
        }
    } catch (err) { console.error('System Error:', err.message); }
}
runAutomation();
