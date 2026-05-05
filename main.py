import os
import logging
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from g4f.client import Client

# إعداد خادم ويب بسيط
app = Flask('')
@app.route('/')
def home(): return "OK"

def run():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        client = Client()
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": update.message.text}]
        )
        await update.message.reply_text(response.choices[0].message.content)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    Thread(target=run).start()
    
    # ضع التوكن الخاص بك هنا بدقة
    TOKEN = '7965345356:AAEiY2Q3UQ6WZvpFQAAmap0eebvLRvWXVuY'
    
    # بناء التطبيق مع ضبط إعدادات الشبكة لتجنب خطأ HTTP
    application = ApplicationBuilder().token(TOKEN).build()
    
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    application.run_polling()
