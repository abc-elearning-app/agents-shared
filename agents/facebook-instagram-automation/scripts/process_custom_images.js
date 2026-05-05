require('dotenv').config();
const fs = require('fs');
const path = require('path');
const { google } = require('googleapis');
const axios = require('axios');
const FormData = require('form-data');
const cloudinary = require('cloudinary').v2;
const { GoogleGenerativeAI } = require('@google/generative-ai');

// --- CONFIGURATION ---
const SPREADSHEET_ID = '13j1j4kL6XPGxfwPUSwItOP0nAwyaOhLSoVmvb5LWI6k';
const SHEET_NAME = 'Ảnh tự tạo';
const RANGE = `${SHEET_NAME}!A2:M100`; 

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

// Gemini Config
const GEMINI_API_KEY = process.env.GEMINI_API_KEY;

// HELPER FUNCTIONS
function getDirectDriveLink(url) {
    if (url.includes('drive.google.com')) {
        const idMatch = url.match(/\/file\/d\/(.+?)\//) || url.match(/id=(.+?)(&|$)/);
        if (idMatch && idMatch[1]) {
            return `https://docs.google.com/uc?export=download&id=${idMatch[1]}`;
        }
    }
    return url;
}

async function uploadBufferToCloudinary(buffer) {
    return new Promise((resolve, reject) => {
        const uploadStream = cloudinary.uploader.upload_stream(
            { folder: 'fb_agent' },
            (error, result) => {
                if (error) reject(error);
                else resolve(result.secure_url);
            }
        );
        uploadStream.end(buffer);
    });
}

async function getImageBuffer(imagePathOrUrl) {
    let targetUrl = imagePathOrUrl;
    if (imagePathOrUrl.startsWith('file://')) {
        const cleanPath = imagePathOrUrl.replace(/^file:\/\//, '');
        return fs.readFileSync(decodeURIComponent(cleanPath));
    }
    
    targetUrl = getDirectDriveLink(targetUrl);
    const response = await axios.get(targetUrl, { responseType: 'arraybuffer' });
    return Buffer.from(response.data, 'binary');
}

async function analyzeImageWithAI(imageBuffer) {
    if (!GEMINI_API_KEY) throw new Error('GEMINI_API_KEY missing');
    const genAI = new GoogleGenerativeAI(GEMINI_API_KEY);
    const model = genAI.getGenerativeModel({ model: "gemini-1.5-flash" });

    const prompt = `Analyze this image for social media. 
Strict Rules: 
1. 100% English for all content. 
2. Tone should be professional and engaging for a US audience.
3. FB hashtags: 5-7 broad hashtags.
4. IG hashtags: 10-15 niche specific hashtags.

Return JSON:
{
  "title": "Engaging Title with emojis",
  "caption": "Engaging Caption (English) explaining the image",
  "hashtags_fb": "#fb1 #fb2",
  "hashtags_ig": "#ig1 #ig2 #ig3..."
}`;

    const result = await model.generateContent([prompt, { inlineData: { data: imageBuffer.toString("base64"), mimeType: "image/png" } }]);
    const responseText = result.response.text();
    const jsonMatch = responseText.match(/```json\n([\s\S]*?)\n```/) || responseText.match(/{[\s\S]*?}/);
    return JSON.parse(jsonMatch[1] || jsonMatch[0]);
}

async function publishToFacebook(account, caption, imageBuffer) {
    const config = FB_PAGE_MAPPING[account];
    const tokenRes = await axios.get(`https://graph.facebook.com/v25.0/${config.id}`, { params: { fields: 'access_token', access_token: FB_USER_TOKEN } });
    const pageToken = tokenRes.data.access_token;
    
    const tempPath = path.resolve(__dirname, 'temp_custom_fb.png');
    fs.writeFileSync(tempPath, imageBuffer);
    const form = new FormData();
    form.append('source', fs.createReadStream(tempPath));
    form.append('message', caption);
    form.append('access_token', pageToken);
    
    const postRes = await axios.post(`https://graph.facebook.com/v25.0/${config.id}/photos`, form, { headers: form.getHeaders() });
    fs.unlinkSync(tempPath);
    const postId = postRes.data.post_id || postRes.data.id;
    return `https://www.facebook.com/${postId}`;
}

async function publishToInstagramMCP(account, caption, imageUrl) {
    const channelId = IG_MAPPING[account];
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
    }, { headers: { 
        'Authorization': `Bearer ${BUFFER_TOKEN}`, 
        'Content-Type': 'application/json',
        'Accept': 'application/json, text/event-stream'
    } });
    
    if (res.data.result && res.data.result.isError) throw new Error(`IG Error: ${res.data.result.content[0].text}`);
    return 'Success';
}

function shouldPostNow(dateStr) {
    if (!dateStr || dateStr.trim() === '') return true;
    const scheduledTime = new Date(dateStr);
    const now = new Date();
    // Cho phép sai số 16 phút: Nếu thời gian hiện tại nằm trong khoảng từ [Giờ đặt] đến [Giờ đặt + 16 phút]
    // Hoặc nếu đã quá giờ đặt (để đăng bù)
    const diffInMinutes = (now - scheduledTime) / (1000 * 60);
    return diffInMinutes >= 0; // Đã đến hoặc quá giờ đăng
}

async function updateStatus(rowIndex, status) {
    await sheets.spreadsheets.values.update({
        spreadsheetId: SPREADSHEET_ID,
        range: `${SHEET_NAME}!B${rowIndex}`,
        valueInputOption: 'RAW',
        resource: { values: [[status]] }
    });
}

async function runCustomImageAutomation() {
    try {
        const response = await sheets.spreadsheets.values.get({ spreadsheetId: SPREADSHEET_ID, range: RANGE });
        const rows = response.data.values;
        if (!rows) return;

        for (let i = 0; i < rows.length; i++) {
            const row = rows[i];
            const rowIndex = i + 2; 
            const status = (row[1] || '').trim(); 
            const dateStr = (row[3] || '').trim(); 

            // Logic 1: Date Comparison Auto-Trigger
            if (status === '' && dateStr !== '' && shouldPostNow(dateStr)) {
                console.log(`⏰ Time reached for Row ${rowIndex}. Setting to Ready.`);
                await updateStatus(rowIndex, 'Ready');
                continue; // Will be picked up in next cycle or re-fetch
            }

            // Logic 2: Main Processing
            if (status === 'Ready') {
                const imageLink = (row[0] || '').trim();
                const account = (row[2] || '').trim(); 

                if (!imageLink || !account) continue;

                // LOCK: Set to Processing
                console.log(`\n🔒 Locking Row ${rowIndex} (Processing)...`);
                await updateStatus(rowIndex, 'Processing');

                try {
                    const imageBuffer = await getImageBuffer(imageLink);
                    const aiData = await analyzeImageWithAI(imageBuffer);
                    
                    const config = FB_PAGE_MAPPING[account];
                    if (!config) throw new Error(`Account "${account}" mapping missing`);

                    const fbCaption = `${aiData.title}\n\n${aiData.caption}\n\n${config.cta}\n\n${aiData.hashtags_fb}`;
                    const igCaption = `${aiData.title}\n\n${aiData.caption}\n\nJoin us to master your skills! 🚀\n\n${aiData.hashtags_ig}`;
                    
                    const publicUrl = await uploadBufferToCloudinary(imageBuffer);

                    // Update Content columns E-J
                    await sheets.spreadsheets.values.update({
                        spreadsheetId: SPREADSHEET_ID,
                        range: `${SHEET_NAME}!E${rowIndex}:J${rowIndex}`,
                        valueInputOption: 'RAW',
                        resource: { values: [[aiData.title, fbCaption, igCaption, aiData.hashtags_fb, aiData.hashtags_ig, config.cta]] }
                    });

                    console.log(`📢 Posting to Social Media...`);
                    const fbLink = await publishToFacebook(account, fbCaption, imageBuffer);
                    const igLink = await publishToInstagramMCP(account, igCaption, publicUrl);

                    // Final Update: Status Done + Links
                    await sheets.spreadsheets.values.update({
                        spreadsheetId: SPREADSHEET_ID,
                        range: `${SHEET_NAME}!B${rowIndex}`,
                        valueInputOption: 'RAW',
                        resource: { values: [['Done']] }
                    });
                    await sheets.spreadsheets.values.update({
                        spreadsheetId: SPREADSHEET_ID,
                        range: `${SHEET_NAME}!K${rowIndex}:L${rowIndex}`,
                        valueInputOption: 'RAW',
                        resource: { values: [[fbLink, igLink]] }
                    });
                    console.log(`🎉 Row ${rowIndex} Successfully Processed!`);
                } catch (err) { 
                    console.error(`❌ Error Row ${rowIndex}:`, err.message);
                    await updateStatus(rowIndex, 'Error');
                }
            }
        }
    } catch (err) { console.error('System Error:', err.message); }
}
runCustomImageAutomation();
