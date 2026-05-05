import os
import requests
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# 1. خادم ويب بسيط جداً
app = Flask(__name__)
@app.route('/')
def home(): return "Ready", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# 2. جلب الرد من Pollinations (مستقر جداً)
def get_ai_response(text):
    try:
        # استخدام رابط Pollinations المباشر
        url = f"https://text.pollinations.ai/{text}"
        response = requests.get(url, timeout=20)
        if response.status_code == 200:
            return response.text
    except:
        return None
    return None

# 3. معالجة الرسائل
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    
    # إشارة "يكتب الآن"
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    answer = get_ai_response(update.message.text)
    
    if answer:
        await update.message.reply_text(answer)
    else:
        await update.message.reply_text("عذراً، المحرك مشغول حالياً. حاول مجدداً.")

# 4. تشغيل البوت
if __name__ == '__main__':
    Thread(target=run_flask).start()
    
    # ضع التوكن الخاص بك هنا
    TOKEN = "7965345356:AAEiY2Q3UQ6WZvpFQAAmap0eebvLRvWXVuY"
    
    # أهم سطر: drop_pending_updates=True ينهي أي تصادم فوراً
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("Bot is starting...")
    application.run_polling(drop_pending_updates=True)
