const fs = require('fs');
const path = require('path');

const dataDir = 'data';
const allComments = [];

const dirs = fs.readdirSync(dataDir);
dirs.forEach(dir => {
    const commentsFile = path.join(dataDir, dir, 'comments.json');
    if (fs.existsSync(commentsFile)) {
        try {
            const comments = JSON.parse(fs.readFileSync(commentsFile, 'utf8'));
            comments.forEach(c => {
                if (c.text) {
                    allComments.push({
                        videoId: dir,
                        text: c.text,
                        likes: c.likes || c.like_count || 0
                    });
                }
            });
        } catch (e) {
            console.error(`Error reading ${commentsFile}: ${e.message}`);
        }
    }
});

fs.writeFileSync('aggregated_comments.json', JSON.stringify(allComments, null, 2));
console.log(`Aggregated ${allComments.length} comments into aggregated_comments.json`);
