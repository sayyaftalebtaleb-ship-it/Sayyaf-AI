import os
import requests
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# 1. إعداد Flask (عشان Render يظل شغال)
app = Flask(__name__)
@app.route('/')
def home(): return "Pollinations Bot is Live!", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# 2. وظيفة جلب الرد من Pollinations AI (اقتراحك الممتاز)
def get_pollinations_response(user_text):
    url = "https://text.pollinations.ai/"
    payload = {
        "messages": [
            {"role": "user", "content": user_text}
        ],
        "model": "openai" # يمكنك تغيير الموديل إذا أردت
    }
    try:
        # إرسال الطلب بطريقة مباشرة وبسيطة
        response = requests.post(url, json=payload, timeout=30)
        if response.status_code == 200:
            return response.text # الرابط يعيد النص مباشرة
        else:
            return None
    except Exception as e:
        print(f"Error in Pollinations: {e}")
        return None

# 3. معالج رسائل تليجرام
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    
    # إشارة "يكتب الآن"
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    user_input = update.message.text
    ai_answer = get_pollinations_response(user_input)
    
    if ai_answer:
        await update.message.reply_text(ai_answer)
    else:
        await update.message.reply_text("عذراً، واجهت مشكلة في الاتصال بالمحرك الجديد. حاول مرة أخرى.")

# 4. تشغيل كل شيء
if __name__ == '__main__':
    # تشغيل الويب في الخلفية
    Thread(target=run_flask).start()
    
    # ضع التوكن الخاص بك هنا
    TOKEN = "8665085128:AAF_lrCk-Kvn3fhf9N17pP6zwq0T_CNFL_8"
    
    # بناء البوت مع مسح الرسائل القديمة (drop_pending_updates)
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("Bot is starting with Pollinations AI...")
    application.run_polling(drop_pending_updates=True)
