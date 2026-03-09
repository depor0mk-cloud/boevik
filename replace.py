import os

file_path = './telegram_bot/handlers.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('gold', 'money')
content = content.replace('золото', 'монеты')
content = content.replace('золота', 'монет')
content = content.replace('Золото', 'Монеты')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Replaced successfully.")
