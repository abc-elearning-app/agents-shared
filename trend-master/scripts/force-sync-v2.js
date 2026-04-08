const { GoogleSpreadsheet } = require('google-spreadsheet');
const { JWT } = require('google-auth-library');
const fs = require('fs');

const CREDENTIALS_PATH = './credentials.json';
const spreadsheetId = '1GC2BNL1BY1fDiNjK9TcN1W-dUjSp7m_8NUPu-64_Yro';

async function forceSync() {
    const creds = JSON.parse(fs.readFileSync(CREDENTIALS_PATH));
    const auth = new JWT({
        email: creds.client_email,
        key: creds.private_key,
        scopes: ['https://www.googleapis.com/auth/spreadsheets'],
    });

    const doc = new GoogleSpreadsheet(spreadsheetId, auth);
    await doc.loadInfo();

    // 1. Cập nhật Tab Video_Discovery (Dòng 36)
    const discoverySheet = doc.sheetsByTitle['Video_Discovery'];
    const dRows = await discoverySheet.getRows();
    const row36 = dRows.find(r => r.get('_rowNumber') === '36' || r.rowNumber === 36);
    if (row36) {
        row36.set('status', 'done');
        await row36.save();
        console.log("✅ Đã cập nhật dòng 36 thành 'done'");
    }

    // 2. Ghi mới vào Tab Ideas
    const ideasSheet = doc.sheetsByTitle['Ideas'];
    const voiceOverScript = [
        "1. Hơn 19 triệu người đang lo sợ bị lộ dữ liệu mỗi ngày, nhưng họ đang làm sai cách.",
        "2. Bạn nghĩ đổi mật khẩu là đủ? Chuyên gia CompTIA Security sẽ nói cho bạn sự thật.",
        "3. Hacker không chỉ bẻ khóa, họ đánh vào lỗ hổng con người qua các app nhắn tin.",
        "4. Sai lầm lớn nhất là click vào link từ người quen mà không kiểm tra tên miền gốc.",
        "5. Bước 1: Kích hoạt ngay xác thực 2 lớp, nhưng đừng dùng SMS, hãy dùng Authenticator.",
        "6. Bước 2: Kiểm tra quyền truy cập camera và micro của từng ứng dụng trong cài đặt.",
        "7. Bước 3: Tuyệt đối không lưu mật khẩu ngân hàng trực tiếp trên trình duyệt web.",
        "8. hacker mũ trắng dùng tiêu chuẩn NIST để quản lý rủi ro, và bạn cũng nên như thế.",
        "9. Thay vì sợ hãi, hãy đóng gói dữ liệu quan trọng vào một ổ cứng vật lý tách biệt.",
        "10. Đừng đợi đến khi mất tiền mới đi tìm cách cứu, phòng bệnh luôn rẻ hơn chữa bệnh.",
        "11. Tôi đã tóm tắt lộ trình 5 bước bảo mật chuẩn CompTIA trong phần mô tả video này.",
        "12. Nếu bạn muốn thi chứng chỉ hay chỉ muốn an toàn, đây là kiến thức bắt buộc phải biết.",
        "13. Follow tôi ngay để học cách bảo vệ tài sản số theo phong cách của một chuyên gia."
    ].join('\n');

    const newIdea = {
        topic: 'Cybersecurity Protection Standards (13 Scenes)',
        raw_script: 'Phát hiện từ video viral 67M view về Scam và bảo mật dữ liệu.',
        report: 'CHIẾN LƯỢC: Kết hợp nỗi sợ bị hack với tiêu chuẩn chuyên gia CompTIA. Đánh vào Gap: Video viral chỉ cảnh báo, chưa đưa giải pháp chuẩn.',
        voice_over_script: voiceOverScript,
        source_references: 'YouTube: hSpllJCCAu4, CY4hn70K3r8'
    };

    await ideasSheet.addRows([newIdea]);
    console.log("✅ Đã ghi Idea mới với kịch bản 13 cảnh thành công!");
}

forceSync().catch(console.error);
