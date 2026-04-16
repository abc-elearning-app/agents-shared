const fs = require('fs');
const path = require('path');

const dataDir = 'data';
const allComments = [];
const dmvIds = JSON.parse(fs.readFileSync('dmv_ids.json', 'utf8'));

dmvIds.forEach(id => {
    const commentsFile = path.join(dataDir, id, 'comments.json');
    if (fs.existsSync(commentsFile)) {
        try {
            const comments = JSON.parse(fs.readFileSync(commentsFile, 'utf8'));
            comments.forEach(c => {
                if (c.text) {
                    allComments.push({
                        videoId: id,
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

fs.writeFileSync('aggregated_dmv_comments.json', JSON.stringify(allComments, null, 2));
console.log(`Aggregated ${allComments.length} DMV comments into aggregated_dmv_comments.json`);
