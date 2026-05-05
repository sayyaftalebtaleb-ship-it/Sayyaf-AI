import os
import requests
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# 1. إعداد Flask
app = Flask(__name__)
@app.route('/')
def home(): return "Sayyaf AI is Online!", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# 2. وظيفة جلب الرد مع التعليمات الثابتة
def get_ai_response(user_text):
    url = "https://text.pollinations.ai/"
    
    # هذه هي التعليمات الثابتة التي طلبتها (الشخصية وأسلوب الكتابة)
    system_instructions = (
        "أنت اسمك Sayyaf AI. صنعك مبرمج يمني ذكي ومبدع اسمه سياف طالب. "
        "عندما تسأل عن هويتك، أجب بفخر أنك Sayyaf AI من تطوير سياف طالب. "
        "يجب أن يكون أسلوبك في الكتابة احترافياً للغاية، منظماً، وواضحاً. "
        "استخدم النقاط، العناوين، والرموز التعبيرية المناسبة لجعل النص مريحاً للقراءة."
    )
    
    payload = {
        "messages": [
            {"role": "system", "content": system_instructions},
            {"role": "user", "content": user_text}
        ],
        "model": "openai",
        "jsonMode": False
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        if response.status_code == 200:
            return response.text
    except Exception as e:
        print(f"Error: {e}")
    return None

# 3. معالج رسائل تليجرام
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    
    # إشارة "يكتب الآن"
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    user_input = update.message.text
    ai_answer = get_ai_response(user_input)
    
    if ai_answer:
        # إرسال الرد الاحترافي
        await update.message.reply_text(ai_answer, parse_mode='Markdown')
    else:
        await update.message.reply_text("عذراً، واجهت مشكلة في معالجة النص. حاول مرة أخرى.")

if __name__ == '__main__':
    Thread(target=run_flask).start()
    
    # ضع التوكن الخاص بك هنا
    TOKEN = "7965345356:AAEiY2Q3UQ6WZvpFQAAmap0eebvLRvWXVuY"
    
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("Sayyaf AI is starting...")
    application.run_polling(drop_pending_updates=True)
