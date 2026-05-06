import os, requests, asyncio
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

app = Flask(__name__)
@app.route('/')
def home(): return "Sayyaf AI is Active", 200

user_memory = {}

def get_ai_response(user_id, user_text, user_lang):
    if user_id not in user_memory:
        user_memory[user_id] = []
    
    memory = user_memory[user_id]
    
    # تحديد الاسم حسب اللغة
    creator = "سياف طالب" if user_lang != 'en' else "Sayyaf Taleb"
    bot_name = "Sayyaf AI"
    
    # تعليمات صارمة للشخصية والتنسيق
    system_prompt = (
        f"أنت {bot_name}. مطورك هو {creator}. "
        "قواعد صارمة: "
        "1. إذا سُئلت عن هويتك، أجب فقط بـ: (أنا {bot_name}، مساعد ذكي طوره المبرمج {creator}). لا تضف أي تفاصيل أخرى عن قدراتك أو سلوكك. "
        "2. لا تخبر المستخدم أبداً أنك 'منظم' أو 'تستخدم جداول' أو 'تتذكر المحادثة'؛ فقط افعل ذلك بصمت. "
        "3. عند إنشاء جدول، يجب وضعه داخل كود بلوك (```) لضمان ظهوره بشكل احترافي ومتناسق في تليجرام. "
        "4. استخدم لغة عربية فصحى، بسيطة، ومباشرة. "
        "5. كن صديقاً ودوداً لكن دون إطالة غير ضرورية."
    )

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(memory[-10:]) 
    messages.append({"role": "user", "content": user_text})

    try:
        url = "[https://text.pollinations.ai/](https://text.pollinations.ai/)"
        # إرسال الطلب مع ضبط الموديل ليكون أكثر استقراراً
        response = requests.post(url, json={"messages": messages, "model": "openai", "private": True}, timeout=60)
        if response.status_code == 200:
            ai_reply = response.text
            user_memory[user_id].append({"role": "user", "content": user_text})
            user_memory[user_id].append({"role": "assistant", "content": ai_reply})
            return ai_reply
    except: return None
    return None

async def keep_typing(context, chat_id, stop_event):
    while not stop_event.is_set():
        await context.bot.send_chat_action(chat_id=chat_id, action="typing")
        await asyncio.sleep(4)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    user_text = update.message.text
    user_lang = update.effective_user.language_code

    stop_typing = asyncio.Event()
    typing_task = asyncio.create_task(keep_typing(context, chat_id, stop_typing))
    
    try:
        loop = asyncio.get_event_loop()
        answer = await loop.run_in_executor(None, get_ai_response, user_id, user_text, user_lang)
        
        stop_typing.set()
        await typing_task
        
        if answer:
            # استخدام MarkdownV2 أو التقليدي لضمان ظهور الجداول
            await update.message.reply_text(answer, parse_mode='Markdown')
        else:
            await update.message.reply_text("عذراً صديقي، حدث خطأ تقني. حاول مرة أخرى.")
    except:
        stop_typing.set()

if __name__ == '__main__':
    Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))).start()
    TOKEN = "7965345356:AAEiY2Q3UQ6WZvpFQAAmap0eebvLRvWXVuY" # ضع التوكن هنا
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    application.run_polling(drop_pending_updates=True)
