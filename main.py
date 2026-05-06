import os, requests, asyncio
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

app = Flask(__name__)
@app.route('/')
def home(): return "Sayyaf AI Online", 200

# الذاكرة
user_memory = {}

def get_ai_response(user_id, user_text, user_lang):
    if user_id not in user_memory:
        user_memory[user_id] = []
    
    # اسمك يظهر فقط عند الضرورة وباللغة المناسبة
    dev_name = "سياف طالب" if user_lang != 'en' else "Sayyaf Taleb"
    
    system_prompt = (
        f"أنت Sayyaf AI. مطورك هو {dev_name}. "
        "لا تذكر هويتك إلا إذا سُئلت عنها. "
        "نظم إجاباتك بشكل احترافي. الجداول يجب أن تكون داخل كود بلوك (```). "
        "لا تتحدث عن قدراتك التقنية، فقط أجب على السؤال."
    )

    messages = [{"role": "system", "content": system_prompt}]
    # نرسل فقط آخر 5 رسائل لضمان استقرار المحرك وعدم حدوث خطأ
    messages.extend(user_memory[user_id][-5:]) 
    messages.append({"role": "user", "content": user_text})

    try:
        # استخدام الرابط المباشر الأسرع
        url = f"[https://text.pollinations.ai/](https://text.pollinations.ai/){user_text}?model=openai&system={system_prompt}"
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            ai_reply = response.text
            user_memory[user_id].append({"role": "user", "content": user_text})
            user_memory[user_id].append({"role": "assistant", "content": ai_reply})
            return ai_reply
    except:
        return None
    return None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    user_text = update.message.text
    user_lang = update.effective_user.language_code

    # وشم الكتابة
    stop_typing = False
    async def typing_loop():
        while not stop_typing:
            try:
                await context.bot.send_chat_action(chat_id=chat_id, action="typing")
                await asyncio.sleep(4)
            except: break

    typing_task = asyncio.create_task(typing_loop())
    
    try:
        loop = asyncio.get_event_loop()
        answer = await loop.run_in_executor(None, get_ai_response, user_id, user_text, user_lang)
        
        stop_typing = True
        await typing_task
        
        if answer:
            # إرسال الرد
            try:
                await update.message.reply_text(answer, parse_mode='Markdown')
            except:
                await update.message.reply_text(answer)
        else:
            await update.message.reply_text("عذراً، واجهت مشكلة في معالجة طلبك حالياً. يرجى المحاولة مرة أخرى.")
    except:
        stop_typing = True

if __name__ == '__main__':
    Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))).start()
    TOKEN = "7965345356:AAEiY2Q3UQ6WZvpFQAAmap0eebvLRvWXVuY" # ضع التوكن هنا
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    application.run_polling(drop_pending_updates=True)
