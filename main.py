import os, asyncio, httpx
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# 1. إعداد Flask لـ Render
app = Flask(__name__)
@app.route('/')
def home(): return "Sayyaf AI is Online", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# 2. الذاكرة
user_memory = {}

# 3. جلب الرد من الرابط الذي اخترته أنت (Pollinations)
async def get_ai_response(user_id, user_text, user_lang):
    if user_id not in user_memory:
        user_memory[user_id] = []
    
    # اسم المطور حسب اللغة
    dev_name = "سياف طالب" if user_lang != 'en' else "Sayyaf Taleb"
    
    # التعليمات الصارمة (System Prompt)
    system_prompt = (
        f"أنت مساعد ذكي محترف اسمك Sayyaf AI ومطورك هو {dev_name}. "
        "قواعد لا تنساها: "
        "1. لا تذكر اسمك أو مطورك إلا إذا سُئلت صراحة عن هويتك. "
        "2. لا تصف طريقة عملك أو قدراتك (مثل: لا تقل أنا أنظم الجداول). "
        "3. أي جدول يجب أن يكون داخل صندوق كود (```) لضمان التنسيق الاحترافي. "
        "4. استخدم Markdown (Bold، Lists) لتنظيم النص بشكل جمالي."
    )

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(user_memory[user_id][-6:]) # الذاكرة لآخر 6 رسائل
    messages.append({"role": "user", "content": user_text})

    # الرابط الذي طلبته
    API_URL = "[https://text.pollinations.ai/openai/chat/completions](https://text.pollinations.ai/openai/chat/completions)"

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            payload = {
                "messages": messages,
                "model": "openai"
            }
            response = await client.post(API_URL, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                ai_reply = data['choices'][0]['message']['content']
                # تحديث الذاكرة
                user_memory[user_id].append({"role": "user", "content": user_text})
                user_memory[user_id].append({"role": "assistant", "content": ai_reply})
                return ai_reply
            else:
                print(f"Error: {response.status_code}")
                return None
        except Exception as e:
            print(f"Conn Error: {e}")
            return None

# 4. معالج الرسائل (وشم الكتابة + إرسال الرد)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    user_text = update.message.text
    user_lang = update.effective_user.language_code

    # تشغيل وشم الكتابة (Typing) بشكل مستمر
    stop_typing = asyncio.Event()
    async def typing_loop():
        while not stop_typing.is_set():
            try:
                await context.bot.send_chat_action(chat_id=chat_id, action="typing")
                await asyncio.sleep(4)
            except: break

    typing_task = asyncio.create_task(typing_loop())
    
    try:
        # الحصول على الرد من AI
        answer = await get_ai_response(user_id, user_text, user_lang)
        
        # إيقاف الوشم فوراً بمجرد استلام الرد
        stop_typing.set()
        await typing_task
        
        if answer:
            try:
                # محاولة الإرسال بتنسيق Markdown
                await update.message.reply_text(answer, parse_mode='Markdown')
            except:
                # في حال وجود خطأ في تنسيق الماركداون يرسل نص عادي
                await update.message.reply_text(answer)
        else:
            await update.message.reply_text("عذراً، حدث خطأ تقني في معالجة النص. أعد المحاولة لاحقاً.")
    except:
        stop_typing.set()

if __name__ == '__main__':
    Thread(target=run_flask).start()
    
    # ضع التوكن الخاص بك هنا
    TOKEN = "7965345356:AAEiY2Q3UQ6WZvpFQAAmap0eebvLRvWXVuY"
    
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("Sayyaf AI is launching...")
    application.run_polling(drop_pending_updates=True)
