const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
const fs = require('fs');

puppeteer.use(StealthPlugin());

// ==========================================
// TÍNH NĂNG MỚI: VALIDATE LINK TIKTOK
// ==========================================
async function validateTikTokVideos(urlList) {
    console.log(`🛡️ Bắt đầu Validate ${urlList.length} video TikTok...`);
    const browser = await puppeteer.launch({
        headless: "new",
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--window-size=1400,900']
    });
    const page = await browser.newPage();
    await page.setViewport({ width: 1400, height: 900 });

    const validResults = [];

    for (const url of urlList) {
        if (!url.includes('tiktok.com')) continue;
        console.log(`🔍 Đang kiểm tra: ${url}`);
        try {
            await page.goto(url, { waitUntil: 'networkidle2', timeout: 60000 });
            await new Promise(r => setTimeout(r, 3000));

            const isUnavailable = await page.evaluate(() => {
                const text = document.body.innerText;
                return text.includes("Video currently unavailable") || 
                       text.includes("Couldn't find this video") || 
                       text.includes("Content unavailable") ||
                       document.querySelector('[data-e2e="error-page"]') !== null;
            });

            if (isUnavailable) {
                console.log(`❌ Bỏ qua: Video không khả dụng.`);
                continue;
            }

            const metadata = await page.evaluate((videoUrl) => {
                return {
                    link: videoUrl,
                    title: document.querySelector('[data-e2e="browse-video-desc"]')?.innerText || 
                           document.querySelector('h1')?.innerText || "No Title",
                    views: document.querySelector('[data-e2e="browse-view-count"]')?.innerText || "0",
                    like: document.querySelector('[data-e2e="browse-like-count"]')?.innerText || "0",
                    platform: 'TikTok',
                    status: 'approved',
                    run_date: new Date().toISOString().split('T')[0]
                };
            }, url);

            console.log(`✅ Hợp lệ: ${metadata.title.substring(0, 30)}...`);
            validResults.push(metadata);

        } catch (e) {
            console.error(`⚠️ Lỗi khi mở link ${url}: ${e.message}`);
        }
    }

    fs.writeFileSync('discovery_results.json', JSON.stringify(validResults, null, 2));
    console.log(`\n🎉 HOÀN TẤT! Đã lưu ${validResults.length} video sống vào discovery_results.json`);
    await browser.close();
}

// ==========================================
// TÍNH NĂNG GỐC: MINING COMMENTS & REPLIES
// ==========================================
async function localTikTokScraper(videoUrl, targetLimit = 500) {
    console.log(`📡 Khởi động Pipeline 2-Phase cho: ${videoUrl}`);
    const browser = await puppeteer.launch({
        headless: "new",
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--window-size=1400,900']
    });
    const page = await browser.newPage();
    await page.setViewport({ width: 1400, height: 900 });
    const commentsMap = new Map();

    // Layer 3: Network Interception
    page.on('response', async (response) => {
        const url = response.url();
        if (url.includes('/api/comment/list/') || url.includes('/api/comment/reply/')) {
            try {
                const data = await response.json();
                const rawComments = data.comments || [];
                rawComments.forEach(c => {
                    if (!commentsMap.has(c.cid)) {
                        commentsMap.set(c.cid, {
                            video_url: videoUrl,
                            comment_id: c.cid,
                            text: c.text,
                            author: c.user?.unique_id || 'unknown',
                            like_count: c.digg_count || 0,
                            reply_count: c.reply_comment_total || 0,
                            create_time: new Date(c.create_time * 1000).toISOString()
                        });
                    }
                });
            } catch (e) {}
        }
    });

    try {
        await page.goto(videoUrl, { waitUntil: 'networkidle2', timeout: 90000 });
        await new Promise(r => setTimeout(r, 5000));
        await page.evaluate(() => {
            const btn = document.querySelector('[data-e2e="comment-icon"]');
            if (btn) btn.click();
        });

        console.log("🚀 PHASE 1: Thu thập comment gốc...");
        let noNewRootCount = 0;
        while (commentsMap.size < targetLimit && noNewRootCount < 3) {
            const prevSize = commentsMap.size;
            await page.evaluate(() => {
                const container = document.querySelector('[class*="DivCommentListContainer"]') || window;
                container.scrollBy(0, 1500);
            });
            await new Promise(r => setTimeout(r, 3000));
            console.log(`📦 Đã lấy: ${commentsMap.size} root comments`);
            if (commentsMap.size === prevSize) noNewRootCount++;
            else noNewRootCount = 0;
        }

        fs.writeFileSync('comments_clean.json', JSON.stringify(Array.from(commentsMap.values()), null, 2));
        console.log(`\n✅ THÀNH CÔNG! Đã lưu ${commentsMap.size} thảo luận.`);

    } catch (e) {
        console.error(`❌ Lỗi Pipeline: ${e.message}`);
    } finally {
        await browser.close();
    }
}

const [,, mode, arg] = process.argv;
if (mode === 'validate-list') {
    const urls = arg.split(',');
    validateTikTokVideos(urls);
} else if (mode === 'mine') {
    localTikTokScraper(arg);
} else {
    console.log('Sử dụng:');
    console.log('1. Validate: node local-tt-engine.js validate-list "url1,url2"');
    console.log('2. Cào comment: node local-tt-engine.js mine "url_video"');
}
