import os, asyncio, httpx
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# 1. تشغيل Flask لضمان استقرار Render
app = Flask(__name__)
@app.route('/')
def home(): return "Sayyaf AI is Online", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# 2. الذاكرة المؤقتة
user_memory = {}

# 3. وظيفة جلب الرد باستخدام API Key الخاص بك
async def get_ai_response(user_id, user_text, user_lang):
    if user_id not in user_memory:
        user_memory[user_id] = []
    
    dev_name = "سياف طالب" if user_lang != 'en' else "Sayyaf Taleb"
    
    system_prompt = (
        f"أنت مساعد ذكي محترف اسمك Sayyaf AI ومطورك هو {dev_name}. "
        "لا تذكر هويتك إلا عند السؤال. نظم النصوص بجداول (داخل كود بلوك ```) "
        "وقوائم واضحة. كن صديقاً ذكياً ومختصراً."
    )

    # تجهيز الرسائل
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(user_memory[user_id][-6:])
    messages.append({"role": "user", "content": user_text})

    # --- إعدادات الـ API الخاص بك ---
    API_KEY = "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"
    API_URL = "[https://api.openai.com/v1/chat/completions](https://api.openai.com/v1/chat/completions)" # غير الرابط إذا كان API لشركة أخرى

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            headers = {
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "gpt-3.5-turbo", # أو الموديل المتوفر في مفتاحك
                "messages": messages
            }
            
            response = await client.post(API_URL, json=payload, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                ai_reply = result['choices'][0]['message']['content']
                # حفظ الذاكرة
                user_memory[user_id].append({"role": "user", "content": user_text})
                user_memory[user_id].append({"role": "assistant", "content": ai_reply})
                return ai_reply
            else:
                # إذا انتهى الرصيد أو فشل المفتاح، نطبع السبب في السيرفر فقط
                print(f"API Error: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"Connection Error: {e}")
            return None

# 4. معالج الرسائل المحسن (وشم الكتابة + الرد)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    user_text = update.message.text
    user_lang = update.effective_user.language_code

    # ميكانيكية وشم الكتابة ( Typing... )
    stop_typing = asyncio.Event()

    async def typing_loop():
        while not stop_typing.is_set():
            try:
                await context.bot.send_chat_action(chat_id=chat_id, action="typing")
                await asyncio.sleep(4)
            except: break

    # بدء الوشم في الخلفية فوراً
    typing_task = asyncio.create_task(typing_loop())
    
    try:
        # جلب الرد
        answer = await get_ai_response(user_id, user_text, user_lang)
        
        # إيقاف الوشم قبل إرسال الرسالة
        stop_typing.set()
        await typing_task
        
        if answer:
            try:
                await update.message.reply_text(answer, parse_mode='Markdown')
            except:
                await update.message.reply_text(answer)
        else:
            # رد موحد عند حدوث أي مشكلة (فلوس، اتصال، إلخ)
            await update.message.reply_text("عذراً، واجهت مشكلة في معالجة طلبك حالياً. يرجى المحاولة مرة أخرى لاحقاً.")
    except:
        stop_typing.set()

if __name__ == '__main__':
    Thread(target=run_flask).start()
    
    TOKEN = "7965345356:AAEiY2Q3UQ6WZvpFQAAmap0eebvLRvWXVuY"
    
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("Sayyaf AI is launching...")
    application.run_polling(drop_pending_updates=True)
