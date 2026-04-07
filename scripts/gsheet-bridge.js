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
    'init-sheet': async (spreadsheetId) => {
        const doc = await getDoc(spreadsheetId);
        const setupTab = async (title, headers) => {
            let sheet = doc.sheetsByTitle[title];
            if (!sheet) {
                sheet = await doc.addSheet({ title, headerValues: headers });
                console.log(`Đã tạo tab: ${title}`);
            } else {
                if (sheet.columnCount < headers.length) {
                    await sheet.resize({ rowCount: sheet.rowCount || 1000, columnCount: headers.length });
                }
                await sheet.setHeaderRow(headers);
                console.log(`Đã cập nhật header cho tab: ${title}`);
            }
        };

        // 1. Video_Discovery (Lớp 1 - Tìm kiếm Video Viral)
        await setupTab('Video_Discovery', [
            'keyword', 'video_url', 'platform_found', 'views', 
            'likes', 'video_title', 'match_reason', 'run_date', 'status'
        ]);
        
        const discoverySheet = doc.sheetsByTitle['Video_Discovery'];
        // Status Dropdown at Column I (index 8)
        await discoverySheet.setDataValidation({
            startColumnIndex: 8, endColumnIndex: 9, startRowIndex: 1, endRowIndex: 1000
        }, {
            condition: {
                type: 'ONE_OF_LIST',
                values: [
                    { userEnteredValue: 'run' }, { userEnteredValue: 'new' },
                    { userEnteredValue: 'approved' }, { userEnteredValue: 'done' },
                    { userEnteredValue: 'reject' }, { userEnteredValue: 'error' },
                    { userEnteredValue: 'Monitor' }
                ]
            }
        });

        // 2. Ideas (Tối giản - 7 Cột Core)
        await setupTab('Ideas', [
            'keyword', 'source_video_url', 'script_raw', 
            'insight', 'voice-over script', 'status', 'insight_score'
        ]);

        const ideasSheet = doc.sheetsByTitle['Ideas'];
        // Status Dropdown for Ideas at Column F (index 5)
        await ideasSheet.setDataValidation({
            startColumnIndex: 5, endColumnIndex: 6, startRowIndex: 1, endRowIndex: 1000
        }, {
            condition: {
                type: 'ONE_OF_LIST',
                values: [
                    { userEnteredValue: 'new' }, { userEnteredValue: 'reviewed' },
                    { userEnteredValue: 'selected' }, { userEnteredValue: 'used' },
                    { userEnteredValue: 'reject' }
                ]
            }
        });
        
        console.log('Hệ thống Trend Master (2-Tier Multi-Platform) đã sẵn sàng.');
    },
    'clear-tab': async (spreadsheetId, tabName) => {
        const doc = await getDoc(spreadsheetId);
        const sheet = doc.sheetsByTitle[tabName];
        if (sheet) {
            await sheet.clearRows();
            console.log(`Đã xóa toàn bộ dữ liệu trong tab: ${tabName}`);
        }
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
    'update-row': async (spreadsheetId, tabName, keyColumn, keyValue, updateDataJson) => {
        const doc = await getDoc(spreadsheetId);
        const sheet = doc.sheetsByTitle[tabName];
        const rows = await sheet.getRows();
        const row = rows.find(r => r.get(keyColumn) === keyValue);
        if (row) {
            const updateData = JSON.parse(updateDataJson);
            for (const [k, v] of Object.entries(updateData)) { row.set(k, v); }
            await row.save();
        }
    },
    'update-by-row': async (spreadsheetId, tabName, rowNumber, updateDataJson) => {
        const doc = await getDoc(spreadsheetId);
        const sheet = doc.sheetsByTitle[tabName];
        const rows = await sheet.getRows();
        // Row number in Google Sheet is 1-based. getRows returns rows starting from index 0 (which is row 2)
        const row = rows.find(r => r.rowNumber === parseInt(rowNumber));
        if (row) {
            const updateData = JSON.parse(updateDataJson);
            for (const [k, v] of Object.entries(updateData)) { row.set(k, v); }
            await row.save();
            console.log(`Đã cập nhật dòng ${rowNumber} thành công.`);
        }
    },
    'merge-rows': async (spreadsheetId, tabName, columnNamesJson) => {
        const doc = await getDoc(spreadsheetId);
        const sheet = doc.sheetsByTitle[tabName];
        const rows = await sheet.getRows();
        const colNames = JSON.parse(columnNamesJson);
        const headers = sheet.headerValues;

        for (const colName of colNames) {
            const colIndex = headers.indexOf(colName);
            if (colIndex === -1) continue;

            let startRow = 2; // Row 1 is header, Row 2 is index 0 in getRows
            let currentValue = null;
            let mergeStart = 0;

            for (let i = 0; i < rows.length; i++) {
                const val = rows[i].get(colName);
                if (val && val === currentValue) {
                    // Same value, continue
                } else {
                    // New value or end, merge previous if any
                    if (i - mergeStart > 1) {
                        await sheet.mergeCells({
                            startRowIndex: mergeStart + 1,
                            endRowIndex: i + 1,
                            startColumnIndex: colIndex,
                            endColumnIndex: colIndex + 1
                        });
                    }
                    currentValue = val;
                    mergeStart = i;
                }
            }
            // Final merge
            if (rows.length - mergeStart > 1) {
                await sheet.mergeCells({
                    startRowIndex: mergeStart + 1,
                    endRowIndex: rows.length + 1,
                    startColumnIndex: colIndex,
                    endColumnIndex: colIndex + 1
                });
            }
        }
        console.log(`Đã hoàn tất merge các cột: ${colNames.join(', ')}`);
    }
};

const [,, cmd, id, ...args] = process.argv;
if (commands[cmd]) {
    commands[cmd](id, ...args).catch(err => {
        console.error(err.message);
        process.exit(1);
    });
}
