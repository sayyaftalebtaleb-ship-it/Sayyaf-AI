import logging
import os
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from g4f.client import Client
import nest_asyncio

# إعداد خادم وهمي لإبقاء Render سعيداً
app = Flask('')
@app.route('/')
def home():
    return "I am alive"

def run():
    app.run(host='0.0.0.0', port=10000)

def keep_alive():
    t = Thread(target=run)
    t.start()

# كود البوت الأساسي
nest_asyncio.apply()
logging.basicConfig(level=logging.INFO)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.text: return
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    try:
        client = Client()
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": update.message.text}],
        )
        await update.message.reply_text(response.choices[0].message.content)
    except Exception as e:
        await update.message.reply_text("النظام مشغول، جرب مرة أخرى.")

if __name__ == '__main__':
    # --- ضع التوكن الخاص بك هنا ---
    TOKEN = '7965345356:AAEiY2Q3UQ6WZvpFQAAmap0eebvLRvWXVuY'
    
    # تشغيل المنبه قبل البوت
    keep_alive()
    
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    application.run_polling()
