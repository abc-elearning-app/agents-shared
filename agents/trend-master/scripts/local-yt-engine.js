const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
const fs = require('fs');

puppeteer.use(StealthPlugin());

async function localYouTubeScraper(videoUrl, targetLimit = 100) {
    console.log(`📡 Khởi động Local YouTube Mining cho: ${videoUrl}`);
    const browser = await puppeteer.launch({ 
        headless: "new", // Đổi thành false nếu muốn xem robot làm việc
        args: ['--no-sandbox', '--disable-setuid-sandbox'] 
    });
    const page = await browser.newPage();

    try {
        await page.goto(videoUrl, { waitUntil: 'networkidle2' });
        console.log("🚀 Đã tải xong trang video. Đang tìm khu vực comment...");

        // 1. Cuộn xuống để load comment section
        await page.evaluate(() => window.scrollBy(0, 600));
        await new Promise(r => setTimeout(r, 3000));

        let allComments = [];
        let previousHeight = 0;

        // 2. Vòng lặp cuộn để lấy đủ root comments
        while (allComments.length < targetLimit) {
            const currentComments = await page.evaluate(() => {
                const results = [];
                const items = document.querySelectorAll('ytd-comment-thread-renderer');
                items.forEach(item => {
                    const text = item.querySelector('#content-text')?.innerText;
                    const author = item.querySelector('#author-text')?.innerText.trim();
                    const likes = item.querySelector('#vote-count-middle')?.innerText.trim();
                    if (text) results.push({ text, author, likes });
                });
                return results;
            });

            allComments = currentComments;
            console.log(`📦 Đã thu thập: ${allComments.length} root comments...`);

            if (allComments.length >= targetLimit) break;

            // Cuộn tiếp
            previousHeight = await page.evaluate('document.documentElement.scrollHeight');
            await page.evaluate('window.scrollTo(0, document.documentElement.scrollHeight)');
            await new Promise(r => setTimeout(r, 2000));
            
            let newHeight = await page.evaluate('document.documentElement.scrollHeight');
            if (newHeight === previousHeight) break; // Hết comment để load
        }

        // 3. Mở rộng các replies (Tùy chọn: Đây là phần đào sâu)
        console.log("🔍 Đang thử mở các thảo luận ẩn (Replies)...");
        const replyButtons = await page.$$('ytd-button-renderer#more-replies');
        for (let i = 0; i < Math.min(replyButtons.length, 10); i++) { // Giới hạn mở 10 cụm reply sâu nhất
            try {
                await replyButtons[i].click();
                await new Promise(r => setTimeout(r, 1000));
            } catch (e) {}
        }

        // 4. Trích xuất lại toàn bộ sau khi đã mở rộng
        const finalData = await page.evaluate((currentUrl) => {
            const results = [];
            const items = document.querySelectorAll('ytd-comment-thread-renderer');
            items.forEach(item => {
                const mainComment = item.querySelector('#comment');
                if (!mainComment) return;
                const text = mainComment.querySelector('#content-text')?.innerText;
                const author = mainComment.querySelector('#author-text')?.innerText.trim();
                const likes = mainComment.querySelector('#vote-count-middle')?.innerText.trim();
                
                // Lấy replies nếu có
                const replyItems = item.querySelectorAll('ytd-comment-replier-renderer');
                const replies = [];
                replyItems.forEach(r => {
                    const rText = r.querySelector('#content-text')?.innerText;
                    const rAuthor = r.querySelector('#author-text')?.innerText.trim();
                    if (rText) replies.push({ text: rText, author: rAuthor });
                });

                if (text) results.push({ video_url: currentUrl, text, author, likes, replies });
            });
            return results;
        }, videoUrl);

        const outputFile = process.argv[3] || 'comments_clean.json';
        fs.writeFileSync(outputFile, JSON.stringify(finalData, null, 2));
        console.log(`✅ THÀNH CÔNG! Đã lưu ${finalData.length} thảo luận vào ${outputFile}`);

    } catch (e) {
        console.error(`❌ Lỗi Pipeline: ${e.message}`);
    } finally {
        await browser.close();
    }
}

const url = process.argv[2];
if (url) localYouTubeScraper(url);
