require('dotenv').config();
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

async function generateImage(templateName, data, outputPath) {
    const browser = await chromium.launch();
    const page = await browser.newPage();
    
    // Fixed viewport for horizontal frame
    await page.setViewportSize({ width: 1350, height: 1200 });
    
    const templatePath = 'file://' + path.resolve(__dirname, `../assets/${templateName}.html`);
    await page.goto(templatePath);
    
    await page.evaluate((data) => {
        if (window.setData) {
            window.setData(data);
        }
    }, data);
    
    await page.waitForLoadState('networkidle');
    
    // --- AUTOMATED VALIDATION STEP ---
    const validation = await page.evaluate(() => {
        const errors = [];
        const bodyText = document.body.innerText;
        
        // 1. Check for raw HTML tags that shouldn't be visible
        const rawTags = ['<code>', '</code>', '<b>', '</b>', '<i>', '</i>', '<br>'];
        rawTags.forEach(tag => {
            if (bodyText.includes(tag)) {
                errors.push(`Raw HTML tag found in text: ${tag}`);
            }
        });

        // 2. Check if Logo loaded correctly
        const logo = document.querySelector('#logo') || document.querySelector('img[alt="PMP Logo"]') || document.querySelector('img[alt="DMV Logo"]');
        if (logo && (!logo.complete || logo.naturalHeight === 0)) {
            errors.push('Logo failed to load or is broken.');
        }

        // 3. Check for specific IDs
        if (!document.querySelector('#pmp-card') && !document.querySelector('#dmv-card') && !document.querySelector('#comptia-card')) {
            errors.push('Main card element (#pmp-card, #dmv-card, or #comptia-card) not found.');
        }

        return {
            isValid: errors.length === 0,
            errors: errors
        };
    });

    if (!validation.isValid) {
        throw new Error(`Image Validation Failed: ${validation.errors.join(' | ')}`);
    }
    
    // Capture specific element instead of viewport to handle dynamic height
    const element = await page.$('#pmp-card') || await page.$('#dmv-card') || await page.$('#comptia-card');
    if (element) {
        await element.screenshot({ path: outputPath });
    } else {
        await page.screenshot({ path: outputPath, fullPage: true });
    }
    
    await browser.close();
}

if (require.main === module) {
    const args = process.argv.slice(2);
    if (args.length < 3) {
        console.error('Usage: node generate_image.js <template_name> \'<json_data>\' <output_path>');
        process.exit(1);
    }
    
    const templateName = args[0];
    const data = JSON.parse(args[1]);
    const outputPath = args[2];
    
    generateImage(templateName, data, outputPath)
        .then(() => console.log(`Successfully generated image: ${outputPath}`))
        .catch(err => {
            console.error('Error generating image:', err);
            process.exit(1);
        });
}
