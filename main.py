import os
import logging
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from g4f.client import Client

# 1. إعداد Flask ليعمل في الخلفية (عشان Render يظل Live)
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Bot is Running!", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# 2. منطق البوت والرد على الرسائل
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    try:
        # إرسال إشارة "جارٍ الكتابة"
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        client = Client()
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": user_text}]
        )
        answer = response.choices[0].message.content
        await update.message.reply_text(answer)
    except Exception as e:
        print(f"Error in G4F: {e}")
        await update.message.reply_text("عذراً، واجهت مشكلة في معالجة طلبك.")

# 3. تشغيل كل شيء
if __name__ == '__main__':
    # تشغيل Flask في Thread منفصل
    flask_thread = Thread(target=run_flask)
    flask_thread.start()

    # وضع التوكن الخاص بك
    TOKEN = "7965345356:AAEiY2Q3UQ6WZvpFQAAmap0eebvLRvWXVuY" 

    # بناء وتشغيل البوت
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("Telegram Bot is starting...")
    application.run_polling()
