const { GoogleSpreadsheet } = require('google-spreadsheet');
const { JWT } = require('google-auth-library');
const fs = require('fs');
require('dotenv').config();

const CREDENTIALS_PATH = './credentials.json';
const SPREADSHEET_ID = '1GC2BNL1BY1fDiNjK9TcN1W-dUjSp7m_8NUPu-64_Yro';

async function update() {
    const creds = JSON.parse(fs.readFileSync(CREDENTIALS_PATH));
    const auth = new JWT({
        email: creds.client_email,
        key: creds.private_key,
        scopes: ['https://www.googleapis.com/auth/spreadsheets'],
    });

    const doc = new GoogleSpreadsheet(SPREADSHEET_ID, auth);
    await doc.loadInfo();
    const sheet = doc.sheetsByTitle['Ideas'];
    
    // Xóa dữ liệu cũ
    await sheet.clearRows();

    const data = [
      {
        "keyword": "CompTIA Security+ SY0-701",
        "source_video_url": "https://www.youtube.com/watch?v=Z4he44a3tMs\nhttps://www.youtube.com/watch?v=uBQgi0Hxfl8",
        "script_raw": "1. I passed my test recently, but I am having no luck getting an interview, even for help desk smh. (@konteezy203)\n2. CompTIA may ask you about anything that is on the official exam objectives... You will commonly see a handful of performance based questions at the very beginning of your exam (Messer Transcript)\n3. Only thing on my mind was waiting till i did mine, passed and came back here (@thatfitnessguy-254)",
        "insight": "💎 Insight 1: \"The Certification Paradox\"\n* Phát hiện: Sự xung đột giữa kỳ vọng (có Cert là có việc) và thực tế phũ phàng (không có phỏng vấn ngay cả vị trí Help Desk). Người học đang bị ám ảnh bởi việc đỗ Cert đến mức quên mất kỹ năng thực hành (PBQ) là thứ nhà tuyển dụng cần.\n* Ý tưởng video: \"Remake: From Certified to Hired\" - Video đối chiếu cảnh người học chỉ cày Flashcard và người dùng App thực hành Lab thực tế (Firewall, IAM) để tự tin trả lời phỏng vấn.\n* Tại sao hiệu quả: Đánh trúng nỗi sợ 'có bằng mà vẫn thất nghiệp' cực kỳ phổ biến trong cộng đồng IT năm 2026.",
        "voice-over script": "Your Security Plus certification is just the very beginning of your professional IT journey.\nMany newly certified professionals struggle to even get an interview for a basic help desk.\nThe biggest reason for this failure is the total lack of practical and hands-on technical skills.\nModern hiring managers want to see that you can actually configure a complex firewall today.\nSimply memorizing port numbers and definitions is no longer enough to land a high paying job.\nOur revolutionary app allows you to build real security rules in a simulated lab environment.\nYou can practice performance based questions until they become your absolute second nature.\nLearn how to effectively explain your technical logic to any manager during the interview.\nReal world lab simulations are much more valuable than just using simple digital flashcards.\nStop stressing about the ninety minute exam clock and focus on the skills that actually matter.\nWe focus on teaching the specific practical skills that lead to the highest starting salaries.\nYou can bridge the massive gap between learning for the test and earning a real paycheck now.\nDownload our application today and start building your successful cybersecurity career now.",
        "status": "new"
      },
      {
        "keyword": "CompTIA Security+ SY0-701",
        "source_video_url": "https://www.youtube.com/watch?v=Z4he44a3tMs\nhttps://www.youtube.com/watch?v=uBQgi0Hxfl8",
        "script_raw": "1. FFW right to the questions and if i get it wrong ill listen to the response why i got it wrong (@moemiles2646)\n2. Instead of watching one single video that goes on for hours, we focus on one or two individual topics (Messer Transcript)\n3. Go through each and every single video of his practice group. And purchase all his practice tests. (@farhanana469)",
        "insight": "💎 Insight 2: \"Reverse Learning Strategy\"\n* Phát hiện: Hành vi 'Học ngược' (Reverse Learning) đang trở thành tiêu chuẩn: Bỏ qua bài giảng dài, lao thẳng vào test/PBQ và chỉ xem giải thích khi làm sai. Người học muốn 'Cheat Code' và sự nhanh gọn trong 5-10 phút.\n* Ý tưởng video: \"The 5-Minute Daily Drill\" - Video Split-screen so sánh một người xem video 60 phút và một người dùng App làm 5 câu PBQ thực tế trong 5 phút.\n* Tại sao hiệu quả: Phù hợp hoàn hảo với đối tượng người đi làm bận rộn, ghét sự rườm rà và muốn đo lường kết quả ngay lập tức.",
        "voice-over script": "You should stop wasting your precious hours on long and extremely boring video lectures now.\nModern successful learners are now using the highly efficient reverse study method today.\nYou can jump straight into the hardest performance based questions to test your knowledge.\nMaking mistakes early in the process helps you to learn the material much faster than before.\nOur mobile app provides you with instant and detailed feedback on every single click you make.\nThere is no more need to search through long and tedious training videos for one answer.\nGet the exact technical explanation that you need right now to understand the complex topic.\nYou can master one complex security concept in under five minutes of focused daily practice.\nThis is perfect for busy professionals who want to study during their short lunch breaks.\nScientific research proves that active testing is far superior to passive video watching.\nBuild your technical muscle memory for the actual exam by solving real world problems now.\nYour study time is very precious so you must choose to study much smarter and not harder.\nGet started today with our reverse learning app and pass your certification on the first try.",
        "status": "new"
      }
    ];

    await sheet.addRows(data);
    console.log('✅ Đã cập nhật xong Ideas chuẩn xác.');
}

update().catch(console.error);
