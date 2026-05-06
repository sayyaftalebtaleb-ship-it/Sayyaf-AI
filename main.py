import os, asyncio, requests
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

app = Flask(__name__)
@app.route('/')
def home(): return "Sayyaf AI is Online", 200

user_memory = {}

def fetch_ai_reply(user_id, user_text, user_lang):
    if user_id not in user_memory:
        user_memory[user_id] = []
    
    dev_name = "سياف طالب" if user_lang != 'en' else "Sayyaf Taleb"
    
    # التعليمات
    system_prompt = (
        f"أنت مساعد ذكي اسمك Sayyaf AI ومطورك هو {dev_name}. "
        "لا تذكر اسمك إلا إذا سُئلت. نظم النصوص بجداول داخل (```)."
    )

    # الرابط الصافي بدون أي إضافات أو أقواس
    url = "[https://text.pollinations.ai/](https://text.pollinations.ai/)"
    
    try:
        # تجهيز الطلب
        payload = {
            "messages": [
                {"role": "system", "content": system_prompt},
                *user_memory[user_id][-4:], # آخر 4 رسائل
                {"role": "user", "content": user_text}
            ],
            "model": "openai",
            "private": True
        }
        
        response = requests.post(url, json=payload, timeout=60)
        
        if response.status_code == 200:
            ai_reply = response.text
            user_memory[user_id].append({"role": "user", "content": user_text})
            user_memory[user_id].append({"role": "assistant", "content": ai_reply})
            return ai_reply
        else:
            return f"⚠️ خطأ من السيرفر: {response.status_code}"
            
    except Exception as e:
        return f"⚠️ خطأ تقني: {str(e)}"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    user_text = update.message.text
    user_lang = update.effective_user.language_code

    # وشم الكتابة
    stop_typing = asyncio.Event()
    async def keep_typing():
        while not stop_typing.is_set():
            try:
                await context.bot.send_chat_action(chat_id=chat_id, action="typing")
                await asyncio.sleep(3.5)
            except: break

    typing_task = asyncio.create_task(keep_typing())
    
    try:
        loop = asyncio.get_event_loop()
        answer = await loop.run_in_executor(None, fetch_ai_reply, user_id, user_text, user_lang)
        
        stop_typing.set()
        await typing_task
        
        if answer:
            try:
                await update.message.reply_text(answer, parse_mode='Markdown')
            except:
                await update.message.reply_text(answer)
    except:
        stop_typing.set()

if __name__ == '__main__':
    Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))).start()
    
    # ضع التوكن هنا
    TOKEN = "7965345356:AAEiY2Q3UQ6WZvpFQAAmap0eebvLRvWXVuY"
    
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    application.run_polling(drop_pending_updates=True)
