import os, asyncio, httpx
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

app = Flask(__name__)
@app.route('/')
def home(): return "Sayyaf AI is Live", 200

# الذاكرة
user_memory = {}

async def get_ai_response(user_id, user_text, user_lang):
    if user_id not in user_memory:
        user_memory[user_id] = []
    
    dev_name = "سياف طالب" if user_lang != 'en' else "Sayyaf Taleb"
    
    # التعليمات الصارمة (System Prompt)
    system_prompt = (
        f"أنت Sayyaf AI ومطورك هو {dev_name}. "
        "لا تذكر اسمك أو مطورك إلا عند السؤال 'من أنت' أو 'من صنعك'. "
        "نظم النصوص بشكل احترافي جداً واستخدم الجداول داخل كود بلوك (```). "
        "لا تتحدث عن قدراتك، فقط أجب على السؤال مباشرة."
    )

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(user_memory[user_id][-6:])
    messages.append({"role": "user", "content": user_text})

    # استخدام httpx لسرعة البرق وتجنب أخطاء الاتصال
    async with httpx.AsyncClient(timeout=40.0) as client:
        try:
            url = "[https://text.pollinations.ai/](https://text.pollinations.ai/)"
            response = await client.post(url, json={
                "messages": messages,
                "model": "openai",
                "private": True
            })
            if response.status_code == 200:
                ai_reply = response.text
                user_memory[user_id].append({"role": "user", "content": user_text})
                user_memory[user_id].append({"role": "assistant", "content": ai_reply})
                return ai_reply
        except Exception as e:
            print(f"Request error: {e}")
            return None
    return None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    user_text = update.message.text
    user_lang = update.effective_user.language_code

    # وشم الكتابة ( Typing... )
    stop_typing = False
    async def typing_loop():
        while not stop_typing:
            try:
                await context.bot.send_chat_action(chat_id=chat_id, action="typing")
                await asyncio.sleep(4)
            except: break

    typing_task = asyncio.create_task(typing_loop())
    
    try:
        # جلب الرد
        answer = await get_ai_response(user_id, user_text, user_lang)
        
        stop_typing = True # إيقاف الوشم قبل إرسال الرد
        await typing_task
        
        if answer:
            try:
                await update.message.reply_text(answer, parse_mode='Markdown')
            except:
                await update.message.reply_text(answer)
        else:
            await update.message.reply_text("عذراً، يبدو أن المحرك يواجه ضغطاً كبيراً حالياً. حاول مجدداً بعد لحظات.")
    except:
        stop_typing = True

if __name__ == '__main__':
    Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))).start()
    
    TOKEN = "7965345356:AAEiY2Q3UQ6WZvpFQAAmap0eebvLRvWXVuY" # ضع التوكن الخاص بك هنا
    
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    application.run_polling(drop_pending_updates=True)
