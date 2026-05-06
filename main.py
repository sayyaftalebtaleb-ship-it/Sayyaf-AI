import os, requests, asyncio
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

app = Flask(__name__)
@app.route('/')
def home(): return "Sayyaf AI is Online", 200

user_memory = {}

def get_ai_response(user_id, user_text, user_lang):
    if user_id not in user_memory:
        user_memory[user_id] = []
    
    memory = user_memory[user_id]
    
    # اسم المطور حسب اللغة
    creator_name = "Sayyaf Taleb" if user_lang == 'en' else "سياف طالب"
    bot_name = "Sayyaf AI"
    
    system_prompt = (
        f"أنت مساعد ذكي محترف. لا تذكر اسمك ({bot_name}) أو مطورك ({creator_name}) "
        "إلا إذا سألك المستخدم صراحة عن ذلك. "
        "مهمتك الأساسية هي تنظيم النصوص بشكل احترافي جداً. "
        "استخدم الجداول بنظام Markdown الواضح، والقوائم المنقطة، والعناوين العريضة. "
        "اجعل الردود سهلة القراءة ومرتبة كأنها وثيقة رسمية."
    )

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(memory[-10:]) # الاحتفاظ بآخر 10 رسائل للذاكرة
    messages.append({"role": "user", "content": user_text})

    try:
        url = "https://text.pollinations.ai/"
        response = requests.post(url, json={"messages": messages, "model": "openai", "private": True}, timeout=60)
        if response.status_code == 200:
            ai_reply = response.text
            user_memory[user_id].append({"role": "user", "content": user_text})
            user_memory[user_id].append({"role": "assistant", "content": ai_reply})
            return ai_reply
    except: return None
    return None

async def keep_typing(context, chat_id, stop_event):
    """وظيفة لضمان استمرار وشم الكتابة حتى ظهور الرد"""
    while not stop_event.is_set():
        await context.bot.send_chat_action(chat_id=chat_id, action="typing")
        await asyncio.sleep(4)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    user_text = update.message.text
    # تحديد لغة المستخدم
    user_lang = update.effective_user.language_code if update.effective_user.language_code else 'ar'

    # بدء وشم الكتابة في الخلفية
    stop_typing = asyncio.Event()
    typing_task = asyncio.create_task(keep_typing(context, chat_id, stop_typing))
    
    try:
        loop = asyncio.get_event_loop()
        answer = await loop.run_in_executor(None, get_ai_response, user_id, user_text, user_lang)
        
        stop_typing.set() # إيقاف وشم الكتابة فوراً
        await typing_task
        
        if answer:
            await update.message.reply_text(answer, parse_mode='Markdown')
        else:
            await update.message.reply_text("عذراً، حدث خطأ في المعالجة.")
    except Exception as e:
        stop_typing.set()
        print(f"Error: {e}")

if __name__ == '__main__':
    Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))).start()
    TOKEN = "7965345356:AAEiY2Q3UQ6WZvpFQAAmap0eebvLRvWXVuY" # ضع التوكن الخاص بك هنا
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    application.run_polling(drop_pending_updates=True)
