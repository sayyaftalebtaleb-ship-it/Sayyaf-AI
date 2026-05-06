import os, requests, asyncio
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# 1. إعداد Flask لـ Render
app = Flask(__name__)
@app.route('/')
def home(): return "Sayyaf AI is Online", 200

# مخزن الذاكرة
user_memory = {}

def get_ai_response(user_id, user_text, user_lang):
    if user_id not in user_memory:
        user_memory[user_id] = []
    
    # اسم سياف حسب لغة السائل
    creator = "سياف طالب" if user_lang != 'en' else "Sayyaf Taleb"
    
    # التعليمات الصارمة (System Prompt)
    system_prompt = (
        f"أنت Sayyaf AI. مطورك هو {creator}. "
        "قواعدك: "
        "1. لا تذكر اسمك أو مطورك إلا إذا سألك المستخدم 'من أنت' أو 'من صنعك'. "
        "2. لا تتحدث عن قدراتك أو تنظيمك؛ نفذ المهام بصمت. "
        "3. أي جدول يجب أن يكون داخل صندوق كود (```) ليظهر مرتباً. "
        "4. كن محترفاً جداً ومختصراً في المقدمات."
    )

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(user_memory[user_id][-8:]) # آخر 8 رسائل للذاكرة
    messages.append({"role": "user", "content": user_text})

    try:
        # الرابط المحدث مع headers لضمان الاستجابة
        url = "[https://text.pollinations.ai/](https://text.pollinations.ai/)"
        headers = {'Content-Type': 'application/json'}
        payload = {
            "messages": messages,
            "model": "openai",
            "private": True,
            "jsonMode": False
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=45)
        if response.status_code == 200:
            ai_reply = response.text
            # حفظ في الذاكرة
            user_memory[user_id].append({"role": "user", "content": user_text})
            user_memory[user_id].append({"role": "assistant", "content": ai_reply})
            return ai_reply
        else:
            print(f"API Error: {response.status_code}")
            return None
    except Exception as e:
        print(f"Request Error: {e}")
        return None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    user_text = update.message.text
    user_lang = update.effective_user.language_code

    # وشم الكتابة المستمر
    stop_typing = False
    async def typing_loop():
        while not stop_typing:
            try:
                await context.bot.send_chat_action(chat_id=chat_id, action="typing")
                await asyncio.sleep(4)
            except: break

    typing_task = asyncio.create_task(typing_loop())
    
    try:
        # تنفيذ الطلب
        loop = asyncio.get_event_loop()
        answer = await loop.run_in_executor(None, get_ai_response, user_id, user_text, user_lang)
        
        stop_typing = True # إيقاف الوشم فوراً
        await typing_task
        
        if answer:
            # محاولة الإرسال بـ Markdown، وإذا فشل يرسل نصاً عادياً
            try:
                await update.message.reply_text(answer, parse_mode='Markdown')
            except:
                await update.message.reply_text(answer)
        else:
            await update.message.reply_text("عذراً يا سياف، المحرك لم يستجب. جرب مرة أخرى.")
    except:
        stop_typing = True

if __name__ == '__main__':
    Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))).start()
    
    TOKEN = "7965345356:AAEiY2Q3UQ6WZvpFQAAmap0eebvLRvWXVuY" # ضع التوكن الخاص بك هنا
    
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    # حل مشكلة الـ Conflict المذكورة في صورك السابقة
    application.run_polling(drop_pending_updates=True)
