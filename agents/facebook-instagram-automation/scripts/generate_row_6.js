require('dotenv').config();
const { google } = require('googleapis');
const { exec } = require('child_process');
const path = require('path');

const SPREADSHEET_ID = process.env.SPREADSHEET_ID;
const RANGE = 'Ảnh câu hỏi scale!A6:K6'; 

const CLIENT_ID = process.env.GOOGLE_CLIENT_ID;
const CLIENT_SECRET = process.env.GOOGLE_CLIENT_SECRET;
const REFRESH_TOKEN = process.env.GOOGLE_REFRESH_TOKEN;

const auth = new google.auth.OAuth2(CLIENT_ID, CLIENT_SECRET, 'http://localhost');
auth.setCredentials({ refresh_token: REFRESH_TOKEN });

async function generateRow6() {
    try {
        const sheets = google.sheets({ version: 'v4', auth });
        const response = await sheets.spreadsheets.values.get({ spreadsheetId: SPREADSHEET_ID, range: RANGE });
        const row = response.data.values[0];
        
        if (!row) {
            console.error('Row 6 not found');
            return;
        }

        const domain = row[1];
        const content = row[2];
        const topic = row[5]; // Title column

        // Parsing logic for content
        // Format: Scenario. Question.\n\n\nOption1\nOption2 (Correct)\n...
        const parts = content.split('\n\n\n');
        const mainText = parts[0].trim();
        const optionsText = parts[1].trim();
        const explanationText = parts[2].trim();

        // Split mainText into scenario and question
        // Usually the question is the last sentence.
        const sentences = mainText.match(/[^\.!\?]+[\.!\?]+/g) || [mainText];
        const question = sentences.pop().trim();
        const scenario = sentences.join(' ').trim();

        // Parse options
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

        // Parse explanation and reference
        let explanation = explanationText;
        let reference = '';
        let refSource = 'Agile Practice Guide';

        // More robust split for Reference: it usually follows <br><br><b>...Reference:</b>
        if (explanationText.includes('Reference:')) {
            // Split by the specific pattern found in the sheet
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
            } else {
                // Fallback to simple split if pattern doesn't match exactly
                const expParts = explanationText.split(/Reference:/i);
                explanation = expParts[0].replace(/<b>.*?$/i, '').trim();
                reference = expParts[1] ? expParts[1].replace(/^<\/b><br>/i, '').trim() : '';
            }
        }

        const data = {
            domain,
            topic,
            scenario,
            question,
            options,
            correct_indices: correctIndices,
            explanation,
            reference,
            refSource
        };

        const dataString = JSON.stringify(data).replace(/'/g, "'\\''");
        const outputPath = path.resolve(__dirname, '../post_row_6.png');
        
        console.log('Generating image with data:', JSON.stringify(data, null, 2));

        const cmd = `node scripts/generate_image.js template_pmp '${dataString}' ${outputPath}`;
        
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

generateRow6();
