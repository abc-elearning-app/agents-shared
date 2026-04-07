const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
const fs = require('fs');

puppeteer.use(StealthPlugin());

async function localTikTokScraper(videoUrl, targetLimit = 500) {
    console.log(`📡 Khởi động Pipeline 2-Phase cho: ${videoUrl}`);
    
    const browser = await puppeteer.launch({
        headless: false, // Để quan sát quá trình đào
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--window-size=1400,900']
    });

    const page = await browser.newPage();
    await page.setViewport({ width: 1400, height: 900 });

    const commentsMap = new Map(); // cid -> comment_object
    const rawPayloads = [];

    // === LAYER 3: NETWORK INTERCEPTION (Bắt & Dedupe) ===
    page.on('response', async (response) => {
        const url = response.url();
        if (url.includes('/api/comment/list/') || url.includes('/api/comment/reply/')) {
            try {
                const data = await response.json();
                const rawComments = data.comments || [];
                rawPayloads.push({ url, data });

                rawComments.forEach(c => {
                    if (!commentsMap.has(c.cid)) {
                        commentsMap.set(c.cid, {
                            video_url: videoUrl,
                            comment_id: c.cid,
                            text: c.text,
                            author: c.user?.unique_id || c.user?.nickname || 'unknown',
                            like_count: c.digg_count || 0,
                            reply_count: c.reply_comment_total || 0,
                            replies: [],
                            create_time: new Date(c.create_time * 1000).toISOString(),
                            crawl_time: new Date().toISOString(),
                            source: "network"
                        });
                    }
                });
            } catch (e) {}
        }
    });

    try {
        await page.goto(videoUrl, { waitUntil: 'networkidle2', timeout: 90000 });
        await new Promise(r => setTimeout(r, 5000));

        // Mở comment panel
        await page.evaluate(() => {
            const btn = document.querySelector('[data-e2e="comment-icon"]') || document.querySelector('.comment-icon');
            if (btn) btn.click();
        });
        await new Promise(r => setTimeout(r, 2000));

        // --- PHASE 1: CRAWL TẤT CẢ COMMENT GỐC ---
        console.log("🚀 PHASE 1: Thu thập tất cả comment gốc...");
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

        // --- PHASE 2: CRAWL REPLIES CHO CÁC COMMENT CÓ REPLY ---
        console.log("\n🚀 PHASE 2: Đào sâu Replies...");
        const rootComments = Array.from(commentsMap.values()).filter(c => c.reply_count > 0);
        
        for (const root of rootComments) {
            console.log(`🔍 Đang mở replies cho comment của @${root.author} (${root.reply_count} replies)`);
            
            let noNewReplyCount = 0;
            let currentReplySize = 0;

            // Bấm mở rộng replies liên tục cho đến khi hết
            while (noNewReplyCount < 3) {
                const prevTotalSize = commentsMap.size;
                
                await page.evaluate((cid) => {
                    const commentNode = document.getElementById(cid) || [...document.querySelectorAll('[data-e2e="comment-item"]')].find(el => el.innerText.includes(cid));
                    // Tìm nút View more trong khu vực comment đó
                    const expandBtn = document.querySelector(`[data-e2e="view-more-replies"]`) || document.querySelector(`[class*="DivReplyActionContainer"]`);
                    if (expandBtn && expandBtn.innerText.match(/View|more|replies/i)) {
                        expandBtn.scrollIntoView({ behavior: 'auto', block: 'center' });
                        expandBtn.click();
                    }
                }, root.comment_id);

                await new Promise(r => setTimeout(r, 2500));
                
                if (commentsMap.size === prevTotalSize) noNewReplyCount++;
                else noNewReplyCount = 0;

                // Nếu đã đủ số lượng reply mong muốn thì dừng
                if (noNewReplyCount >= 3) break;
            }
        }

        // --- GỘP REPLIES VÀO ROOT COMMENTS ---
        const allData = Array.from(commentsMap.values());
        // (Logic gộp replies đơn giản dựa trên cấu trúc API của TikTok sẽ được xử lý ở bước phân tích)

        // --- LƯU TRỮ ---
        fs.writeFileSync('raw_comments_local.json', JSON.stringify(rawPayloads, null, 2));
        fs.writeFileSync('comments_clean.json', JSON.stringify(allData, null, 2));
        
        console.log(`\n✅ TẤT CẢ ĐÃ XONG!`);
        console.log(`- Raw payloads: raw_comments_local.json`);
        console.log(`- Normalized data: comments_clean.json (${allData.length} items)`);

    } catch (e) {
        console.error(`❌ Lỗi Pipeline: ${e.message}`);
    } finally {
        await browser.close();
    }
}

const url = process.argv[2];
if (url) localTikTokScraper(url);
