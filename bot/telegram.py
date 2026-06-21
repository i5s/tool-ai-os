import sys, logging
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from toll.core.ai import AI
from toll.core.storage import Storage
from toll.engine.content_machine import ContentMachine
from toll.engine.prompt_gen import PromptGenerator
from toll.engine.reports import Reports

logging.basicConfig(level=logging.INFO)
TOKEN = ""  # ضع توكن البوت هنا

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🧠 **مرحباً بك في تول!**\n\n"
        "أنا مساعدك الشخصي، أستطيع:\n"
        "📄 /report <موضوع> — تقرير مفصل\n"
        "🔬 /research <موضوع> — بحث علمي\n"
        "🔍 /search <استعلام> — بحث Google\n"
        "📺 /present <عنوان> — عرض تقديمي\n"
        "🧠 /prompt <مهمة> — برومبت\n"
        "🎠 /carousel <موضوع> — Carousel HTML\n"
        "💻 /code <طلب> — كتابة كود\n"
        "📊 /status — حالة AI\n\n"
        "أو فقط أرسل لي رسالة وأنا أحدد النوع!"
    )

async def chat(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    await update.message.reply_chat_action("typing")
    try:
        ai = AI()
        response = ai.ask(f"أجب بالعربية بشكل مفيد ودقيق:\n\n{text}")
        if len(response) > 4000:
            for i in range(0, len(response), 4000):
                await update.message.reply_text(response[i:i+4000])
        else:
            await update.message.reply_text(response)
    except Exception as e:
        await update.message.reply_text(f"❌ {e}")

async def cmd_report(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    task = " ".join(ctx.args) or "افتراضي"
    await update.message.reply_chat_action("typing")
    try:
        ai = AI()
        response = ai.ask(f"اكتب تقريراً مفصلاً بالعربية عن: {task}\n\nيشمل مقدمة، نقاط رئيسية، تحليل، توصيات.")
        r = Reports()
        path = r.report(task)
        await update.message.reply_text(f"📄 **{task}**\n\n{response[:3500]}\n\n📁 تم الحفظ: {path}")
    except Exception as e:
        await update.message.reply_text(f"❌ {e}")

async def cmd_research(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    task = " ".join(ctx.args) or "افتراضي"
    await update.message.reply_chat_action("typing")
    try:
        ai = AI()
        response = ai.ask(f"اكتب بحثاً علمياً بالعربية عن: {task}\n\nيشمل: الملخص، المقدمة، المنهجية، النتائج، المناقشة، الخاتمة.")
        await update.message.reply_text(f"🔬 **بحث: {task}**\n\n{response[:3500]}")
    except Exception as e:
        await update.message.reply_text(f"❌ {e}")

async def cmd_search(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    task = " ".join(ctx.args) or "افتراضي"
    await update.message.reply_chat_action("typing")
    try:
        from toll.core.browser import BrowserAI
        br = BrowserAI()
        results = br.get(f"https://www.google.com/search?q={task}")
        await update.message.reply_text(f"🔍 **نتائج بحث: {task}**\n\n{results[:3500]}")
    except Exception as e:
        await update.message.reply_text(f"❌ فشل البحث: {e}")

async def cmd_present(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    task = " ".join(ctx.args) or "افتراضي"
    await update.message.reply_chat_action("typing")
    try:
        ai = AI()
        response = ai.ask(f"اكتب محتوى عرض تقديمي بالعربية عن: {task}\n\nوزع على 5 شرائح.")
        r = Reports()
        path = r.presentation(task)
        await update.message.reply_text(f"📺 **{task}**\n\n{response[:3500]}\n\n📁 تم الحفظ: {path}")
    except Exception as e:
        await update.message.reply_text(f"❌ {e}")

async def cmd_prompt(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    task = " ".join(ctx.args) or "افتراضي"
    await update.message.reply_chat_action("typing")
    try:
        pg = PromptGenerator()
        result = pg.generate(task)
        await update.message.reply_text(result[:4000])
    except Exception as e:
        await update.message.reply_text(f"❌ {e}")

async def cmd_carousel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    task = " ".join(ctx.args) or "افتراضي"
    await update.message.reply_chat_action("typing")
    try:
        cm = ContentMachine()
        result = cm.carousel(task)
        await update.message.reply_text(f"🎠 **{task}**\n\n✅ تم إنشاء Carousel!\n📁 {result}")
    except Exception as e:
        await update.message.reply_text(f"❌ {e}")

async def cmd_code(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    task = " ".join(ctx.args) or "افتراضي"
    await update.message.reply_chat_action("typing")
    try:
        ai = AI()
        response = ai.ask(f"اكتب كود لـ: {task}\n\nقدم الكود مع الشرح.")
        await update.message.reply_text(f"💻 **{task}**\n\n{response[:4000]}")
    except Exception as e:
        await update.message.reply_text(f"❌ {e}")

async def cmd_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        ai = AI()
        s = ai.limit_status()
        msg = "📊 **حالة الـ AI**\n\n" + "\n".join(
            f"{'✅' if v['can_use'] else '❌'} **{p}**: {v['remaining']} طلب متبقي" for p, v in s.items()
        )
        await update.message.reply_text(msg)
    except Exception as e:
        await update.message.reply_text(f"❌ {e}")

def main():
    if not TOKEN:
        print("⚠️  ضع توكن البوت في الملف bot/telegram.py (TOKEN = \"...\")")
        return
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(CommandHandler("report", cmd_report))
    app.add_handler(CommandHandler("research", cmd_research))
    app.add_handler(CommandHandler("search", cmd_search))
    app.add_handler(CommandHandler("present", cmd_present))
    app.add_handler(CommandHandler("prompt", cmd_prompt))
    app.add_handler(CommandHandler("carousel", cmd_carousel))
    app.add_handler(CommandHandler("code", cmd_code))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    print("🤖 بوت تول شغال...")
    app.run_polling()

if __name__ == "__main__":
    main()
