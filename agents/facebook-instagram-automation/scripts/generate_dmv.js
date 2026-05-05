const { google } = require('googleapis');
const { exec } = require('child_process');
const path = require('path');
const fs = require('fs');

const SPREADSHEET_ID = process.env.SPREADSHEET_ID;
const CLIENT_ID = process.env.GOOGLE_CLIENT_ID;
const CLIENT_SECRET = process.env.GOOGLE_CLIENT_SECRET;
const REFRESH_TOKEN = process.env.GOOGLE_REFRESH_TOKEN;

const auth = new google.auth.OAuth2(CLIENT_ID, CLIENT_SECRET, 'http://localhost');
auth.setCredentials({ refresh_token: REFRESH_TOKEN });

async function generateDMV(rowNumber) {
    try {
        const sheets = google.sheets({ version: 'v4', auth });
        const range = `Ảnh câu hỏi scale!A${rowNumber}:K${rowNumber}`;
        const response = await sheets.spreadsheets.values.get({ spreadsheetId: SPREADSHEET_ID, range: range });
        const row = response.data.values[0];
        
        if (!row || row[0] !== 'DMV') {
            console.error(`Row ${rowNumber} is not a DMV entry or not found.`);
            return;
        }

        const state = row[1] || 'General';
        const content = row[2];
        const topic = row[5] || 'Practice Test';

        // Parsing logic for content (Format: Question\n\n\nOption1\nOption2 (Correct)\n...)
        const parts = content.split('\n\n\n');
        const question = parts[0].trim();
        const optionsText = parts[1].trim();

        // Parse options
        const optionLines = optionsText.split('\n');
        const options = [];
        let correctIndex = 0;
        optionLines.forEach((line, index) => {
            const cleanLine = line.replace('(Correct)', '').trim();
            options.push(cleanLine);
            if (line.includes('(Correct)')) {
                correctIndex = index;
            }
        });

        const data = {
            brandTitle: "DMV EASY PREP",
            website: "abc-elearning.org",
            state: state,
            question: question,
            options: options,
            correctIndex: correctIndex
        };

        const dataString = JSON.stringify(data).replace(/'/g, "'\\''");
        const outputPath = path.resolve(__dirname, `../post_row_${rowNumber}.png`);
        
        console.log(`Generating DMV image for Row ${rowNumber}...`);

        const cmd = `node scripts/generate_image.js template_dmv '${dataString}' ${outputPath}`;
        
        exec(cmd, (error, stdout, stderr) => {
            if (error) {
                console.error(`exec error: ${error}`);
                return;
            }
            console.log(stdout);
            console.error(stderr);
        });

    } catch (err) {
        console.error('Error:', err.message);
    }
}

// Lấy row number từ tham số dòng lệnh
const args = process.argv.slice(2);
const rowNum = parseInt(args[0]);

if (isNaN(rowNum)) {
    console.log("Usage: node scripts/generate_dmv.js <row_number>");
} else {
    generateDMV(rowNum);
}
