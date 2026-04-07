const https = require('https');

async function getTranscript(videoId) {
    const url = `https://www.youtube.com/watch?v=${videoId}`;
    
    return new Promise((resolve, reject) => {
        https.get(url, (res) => {
            let data = '';
            res.on('data', (chunk) => data += chunk);
            res.on('end', () => {
                try {
                    // Tìm kiếm dữ liệu caption trong mã nguồn trang
                    const regex = /"captionTracks":\[(.+?)\]/;
                    const match = data.match(regex);
                    if (!match) {
                        resolve("Không tìm thấy link transcript trong trang này.");
                        return;
                    }
                    
                    const tracks = JSON.parse(`[${match[1]}]`);
                    const englishTrack = tracks.find(t => t.languageCode === 'en');
                    
                    if (!englishTrack) {
                        resolve("Không tìm thấy transcript tiếng Anh.");
                        return;
                    }

                    // Tải nội dung transcript từ link tìm được
                    https.get(englishTrack.baseUrl, (res2) => {
                        let xml = '';
                        res2.on('data', (chunk) => xml += chunk);
                        res2.on('end', () => resolve(xml));
                    });
                } catch (e) {
                    reject(e);
                }
            });
        }).on('error', reject);
    });
}

getTranscript(process.argv[2]).then(console.log).catch(console.error);
