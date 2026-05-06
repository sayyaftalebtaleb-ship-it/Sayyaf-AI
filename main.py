import os, asyncio, requests
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# 1. إعداد خادم Flask لضمان استمرار عمل البوت
app = Flask(__name__)
@app.route('/')
def home(): return "Sayyaf AI is Online", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# 2. نظام الذاكرة
user_memory = {}

# 3. دالة جلب الرد (محصنة ضد أخطاء الـ API)
def fetch_ai_reply(user_id, user_text, user_lang):
    if user_id not in user_memory:
        user_memory[user_id] = []
    
    dev_name = "سياف طالب" if user_lang != 'en' else "Sayyaf Taleb"
    
    system_prompt = (
        f"أنت مساعد ذكي محترف اسمك Sayyaf AI ومطورك هو {dev_name}. "
        "قواعد هامة: "
        "1. لا تذكر اسمك أو مطورك نهائياً إلا إذا سألك المستخدم من أنت. "
        "2. لا تتحدث عن كيفية تنظيمك للنصوص؛ فقط نفذ. "
        "3. أي جدول تقوم بإنشائه يجب أن يكون بالكامل داخل كود بلوك (```) لضمان ظهوره بشكل احترافي. "
        "4. استخدم لغة مهذبة ومختصرة."
    )

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(user_memory[user_id][-6:])
    messages.append({"role": "user", "content": user_text})

    url = "[https://text.pollinations.ai/openai/chat/completions](https://text.pollinations.ai/openai/chat/completions)"
    
    try:
        response = requests.post(url, json={"messages": messages, "model": "openai"}, timeout=60)
        if response.status_code == 200:
            # هنا يكمن السر: نحاول قراءة الرد كـ JSON، وإذا فشل نقرأه كنص عادي
            try:
                ai_reply = response.json()['choices'][0]['message']['content']
            except:
                ai_reply = response.text
                
            user_memory[user_id].append({"role": "user", "content": user_text})
            user_memory[user_id].append({"role": "assistant", "content": ai_reply})
            return ai_reply
        return None
    except Exception as e:
        print(f"API Error: {e}")
        return None

# 4. معالج الرسائل المطور (وشم كتابة لا يتوقف)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    user_text = update.message.text
    user_lang = update.effective_user.language_code

    # إعداد وشم الكتابة (Typing) ليعمل في الخلفية بقوة
    stop_typing = asyncio.Event()
    async def keep_typing():
        while not stop_typing.is_set():
            try:
                await context.bot.send_chat_action(chat_id=chat_id, action="typing")
                await asyncio.sleep(3.5) # تليجرام يحتاج تحديث الوشم كل 4 ثوانٍ كحد أقصى
            except: break

    typing_task = asyncio.create_task(keep_typing())
    
    try:
        # تشغيل دالة الطلب دون إيقاف الـ async loop
        loop = asyncio.get_event_loop()
        answer = await loop.run_in_executor(None, fetch_ai_reply, user_id, user_text, user_lang)
        
        # إيقاف الوشم فور استلام الرد
        stop_typing.set()
        await typing_task
        
        if answer:
            # معالجة مشكلة تنسيق تليجرام التي تسبب الأخطاء
            try:
                await update.message.reply_text(answer, parse_mode='Markdown')
            except:
                await update.message.reply_text(answer)
        else:
            await update.message.reply_text("عذراً، حدث خطأ تقني في معالجة النص. أعد المحاولة لاحقاً.")
    except Exception as e:
        stop_typing.set()
        print(f"Handler Error: {e}")

if __name__ == '__main__':
    Thread(target=run_flask).start()
    
    # ⚠️ ضع توكن البوت الخاص بك هنا بين علامتي التنصيص
    TOKEN = "7965345356:AAEiY2Q3UQ6WZvpFQAAmap0eebvLRvWXVuY"
    
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("Sayyaf AI is now perfectly running...")
    application.run_polling(drop_pending_updates=True)
