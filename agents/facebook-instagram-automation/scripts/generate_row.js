require('dotenv').config();
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

async function generateRow(rowNumber) {
    try {
        const sheets = google.sheets({ version: 'v4', auth });
        const range = `Ảnh câu hỏi scale!A${rowNumber}:K${rowNumber}`;
        const response = await sheets.spreadsheets.values.get({ spreadsheetId: SPREADSHEET_ID, range: range });
        const row = response.data.values[0];
        
        if (!row) {
            console.error(`Row ${rowNumber} not found.`);
            return;
        }

        const app = (row[0] || '').trim();
        const domainOrState = row[1];
        const content = row[2];
        const title = row[5] || '';

        let templateName = '';
        let data = {};

        if (app === 'PMP') {
            templateName = 'template_pmp';
            // PMP Parsing
            const parts = content.split('\n\n\n');
            const mainText = parts[0].trim();
            const optionsText = parts[1].trim();
            const explanationText = parts[2] || '';

            const sentences = mainText.match(/[^\.!\?]+[\.!\?]+/g) || [mainText];
            const question = sentences.pop().trim();
            const scenario = sentences.join(' ').trim();

            const optionLines = optionsText.split('\n');
            const options = [];
            const correctIndices = [];
            optionLines.forEach((line, index) => {
                const cleanLine = line.replace('(Correct)', '').trim();
                options.push(cleanLine);
                if (line.includes('(Correct)')) {
                    correctIndices.push(index);
                }
            });

            let explanation = explanationText;
            let reference = '';
            let refSource = 'PMP Study Guide';

            if (explanationText.includes('Reference:')) {
                const refMatch = explanationText.match(/([\s\S]*?)<br><br><b>.*?Reference:<\/b><br>([\s\S]*)/i);
                if (refMatch) {
                    explanation = refMatch[1].trim();
                    const refFull = refMatch[2].trim();
                    if (refFull.includes('—')) {
                        const refSubParts = refFull.split('—');
                        reference = refSubParts[0].trim();
                        refSource = refSubParts[1].trim();
                    } else {
                        reference = refFull;
                    }
                }
            }

            data = {
                domain: domainOrState,
                topic: title,
                scenario,
                question,
                options,
                correct_indices: correctIndices,
                explanation,
                reference,
                refSource
            };
        } else if (app === 'Security+' || app === 'Network+') {
            templateName = 'template_comptia';
            // CompTIA Parsing
            const parts = content.split('\n\n\n');
            const mainText = parts[0].trim();
            const optionsText = parts[1].trim();
            
            // For CompTIA, we often just have Question and Options in the image
            const dataQuestion = mainText;
            const optionLines = optionsText.split('\n');
            const options = optionLines.map(line => line.replace('(Correct)', '').trim());

            data = {
                exam: `${app} Practice`,
                question: dataQuestion,
                options: options
            };
        } else if (app === 'DMV') {
            templateName = 'template_dmv';
            // DMV Parsing
            const parts = content.split('\n\n\n');
            const question = parts[0].trim();
            const optionsText = parts[1].trim();

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

            data = {
                brandTitle: "DMV EASY PREP",
                website: "abc-elearning.org",
                state: domainOrState || 'General',
                question: question,
                options: options,
                correctIndex: correctIndex
            };
        } else {
            console.error(`Unsupported app type: ${app}`);
            return;
        }

        const dataString = JSON.stringify(data).replace(/'/g, "'\\''");
        const outputPath = path.resolve(__dirname, `../post_row_${rowNumber}.png`);
        
        console.log(`Generating ${app} image for Row ${rowNumber} using ${templateName}...`);

        const cmd = `node scripts/generate_image.js ${templateName} '${dataString}' ${outputPath}`;
        
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

const args = process.argv.slice(2);
const rowNum = parseInt(args[0]);

if (isNaN(rowNum)) {
    console.log("Usage: node scripts/generate_row.js <row_number>");
} else {
    generateRow(rowNum);
}
