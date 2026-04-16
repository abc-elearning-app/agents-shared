const { GoogleSpreadsheet } = require('google-spreadsheet');
const { JWT } = require('google-auth-library');
const fs = require('fs');

const CREDENTIALS_PATH = './credentials.json'; 

async function getDoc(spreadsheetId) {
    if (!fs.existsSync(CREDENTIALS_PATH)) {
        throw new Error('Thiếu file credentials.json để kết nối Google Sheets.');
    }
    const creds = JSON.parse(fs.readFileSync(CREDENTIALS_PATH));
    const auth = new JWT({
        email: creds.client_email,
        key: creds.private_key,
        scopes: ['https://www.googleapis.com/auth/spreadsheets'],
    });

    const doc = new GoogleSpreadsheet(spreadsheetId, auth);
    await doc.loadInfo();
    return doc;
}

const commands = {
    'setup-new-flow': async (spreadsheetId) => {
        const doc = await getDoc(spreadsheetId);
        const setupTab = async (title, headers, headerColor = { red: 0.2, green: 0.2, blue: 0.2 }) => {
            let sheet = doc.sheetsByTitle[title];
            if (!sheet) {
                sheet = await doc.addSheet({ title, headerValues: headers });
                console.log(`Đã tạo tab: ${title}`);
            } else {
                await sheet.setHeaderRow(headers);
                console.log(`Đã cập nhật header cho tab: ${title}`);
            }

            // Định dạng Header chuyên nghiệp
            await sheet.loadCells('A1:Z1');
            for (let i = 0; i < headers.length; i++) {
                const cell = sheet.getCell(0, i);
                cell.userEnteredFormat = {
                    backgroundColor: headerColor,
                    textFormat: { 
                        foregroundColor: { red: 1, green: 1, blue: 1 }, 
                        bold: true,
                        fontSize: 10
                    },
                    horizontalAlignment: 'CENTER',
                    verticalAlignment: 'MIDDLE'
                };
            }
            await sheet.saveUpdatedCells();
            
            // Cố định dòng đầu tiên
            await sheet.updateProperties({ gridProperties: { frozenRowCount: 1 } });
            
            return sheet;
        };

        // 1. Dashboard (Màu Xanh Navy)
        const dashboardSheet = await setupTab('Dashboard', [
            'Niche / Exam', 'Status', 'Run Date', 'Seed Topic / Note', 
            'Videos Scraped', 'Ideas Generated'
        ], { red: 0.1, green: 0.2, blue: 0.4 });
        
        // Dropdown cho Niche / Exam (Column A - index 0)
        await dashboardSheet.setDataValidation({
            startColumnIndex: 0, endColumnIndex: 1, startRowIndex: 1, endRowIndex: 100
        }, {
            condition: { 
                type: 'ONE_OF_LIST', 
                values: [
                    { userEnteredValue: 'DMV' }, 
                    { userEnteredValue: 'ASVAB' },
                    { userEnteredValue: 'COMPTIA' },
                    { userEnteredValue: 'IT CERTIFICATION' }
                ] 
            }
        });

        // Dropdown cho Status (Column B - index 1)
        await dashboardSheet.setDataValidation({
            startColumnIndex: 1, endColumnIndex: 2, startRowIndex: 1, endRowIndex: 100
        }, {
            condition: { 
                type: 'ONE_OF_LIST', 
                values: [
                    { userEnteredValue: 'RUN' }, 
                    { userEnteredValue: 'PAUSE' },
                    { userEnteredValue: 'DONE' }
                ] 
            }
        });

        // 2. Agent_Workspace (Màu Xám)
        await setupTab('Agent_Workspace', [
            'niche', 'keyword', 'link', 'platform', 'view', 
            'like', 'title', 'status', 'run_date'
        ], { red: 0.3, green: 0.3, blue: 0.3 });

        // 3. Niche Output Tabs (Màu Xanh Lá)
        const nicheHeaders = [
            'Date', 'Main Keyword', 'Voice-over Script', 
            'Source Videos', 'Evidence (Raw Data)', 'Insight', 'Production Status'
        ];
        const nicheTabs = ['CompTIA', 'DMV', 'ASVAB', 'PMP'];
        for (const title of nicheTabs) {
            const sheet = await setupTab(title, nicheHeaders, { red: 0.1, green: 0.4, blue: 0.2 });
            // Dropdown for Production Status at Column G (index 6)
            await sheet.setDataValidation({
                startColumnIndex: 6, endColumnIndex: 7, startRowIndex: 1, endRowIndex: 1000
            }, {
                condition: {
                    type: 'ONE_OF_LIST',
                    values: [
                        { userEnteredValue: 'New' }, { userEnteredValue: 'To Shoot' },
                        { userEnteredValue: 'Editing' }, { userEnteredValue: 'Done' },
                        { userEnteredValue: 'Reject' }
                    ]
                }
            });
        }

        console.log('Cấu trúc Trend Master (Dashboard UI) đã hoàn tất.');
    },
    'read-tab': async (spreadsheetId, tabName) => {
        const doc = await getDoc(spreadsheetId);
        const sheet = doc.sheetsByTitle[tabName];
        if (!sheet) { console.error(`Tab ${tabName} không tồn tại.`); process.exit(1); }
        const rows = await sheet.getRows();
        console.log(JSON.stringify(rows.map(r => ({ ...r.toObject(), _rowNumber: r.rowNumber }))));
    },
    'write-results': async (spreadsheetId, tabName, dataJson) => {
        const doc = await getDoc(spreadsheetId);
        const sheet = doc.sheetsByTitle[tabName];
        const data = JSON.parse(dataJson);
        await sheet.addRows(data);
        console.log(`Đã ghi ${data.length} dòng vào tab ${tabName}`);
    },
    'update-by-row': async (spreadsheetId, tabName, rowNumber, updateDataJson) => {
        const doc = await getDoc(spreadsheetId);
        const sheet = doc.sheetsByTitle[tabName];
        const rows = await sheet.getRows();
        const row = rows.find(r => r.rowNumber === parseInt(rowNumber));
        if (row) {
            const updateData = JSON.parse(updateDataJson);
            for (const [k, v] of Object.entries(updateData)) { row.set(k, v); }
            await row.save();
            console.log(`Đã cập nhật dòng ${rowNumber} thành công.`);
        }
    }
};

const [,, cmd, id, ...args] = process.argv;
if (commands[cmd]) {
    commands[cmd](id, ...args).catch(err => {
        console.error(err.message);
        process.exit(1);
    });
}
