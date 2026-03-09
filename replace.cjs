const fs = require('fs');

const filePath = './telegram_bot/handlers.py';
let content = fs.readFileSync(filePath, 'utf8');

content = content.replace(/gold/g, 'money');
content = content.replace(/золото/g, 'монеты');
content = content.replace(/золота/g, 'монет');
content = content.replace(/Золото/g, 'Монеты');

fs.writeFileSync(filePath, content, 'utf8');
console.log('Replaced successfully.');
