# bot/main.py
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)
from .settings import BOT_TOKEN, OWNER_IDS

# ---------- logging ----------
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
log = logging.getLogger("bot")

# ---------- menu ----------
MENU = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("📝 Feedback", callback_data="feedback"),
        InlineKeyboardButton("ℹ️ About", callback_data="about"),
    ],
    [InlineKeyboardButton("❓ Help", callback_data="help")],
])

def _users_set(app) -> set:
    if "users" not in app.bot_data:
        app.bot_data["users"] = set()
    return app.bot_data["users"]

# ---------- commands ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    _users_set(context.application).add(user.id)
    await update.message.reply_text(
        f"Hi {user.first_name}! 👋\nChoose an option:",
        reply_markup=MENU
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Commands:\n"
        "/start — open menu\n"
        "/help — this help\n"
        "/stats — owner only\n"
        "/feedback — send feedback"
    )

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in OWNER_IDS:
        return await update.message.reply_text("⛔ Not allowed.")
    users = _users_set(context.application)
    await update.message.reply_text(f"📊 Unique users (this run): {len(users)}")

# ---------- callbacks ----------
async def on_about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    await q.edit_message_text("Sample bot (python-telegram-bot v21, async).")

async def on_help_btn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    await q.edit_message_text("Use the menu buttons or type /help.")

# If user taps “Feedback” button, just prompt like the /feedback command
async def on_feedback_btn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    await feedback_cmd(update, context)  # reuse the same logic

# ---------- Day 3: feedback ----------
WAITING_FEEDBACK = set()

async def feedback_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    WAITING_FEEDBACK.add(user.id)
    # Depending on whether this came from a button or a command:
    if update.message:
        await update.message.reply_text("✍️ Please type your feedback now (send one message).")
    elif update.callback_query:
        await update.callback_query.edit_message_text("✍️ Please type your feedback now (send one message).")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text

    if user.id in WAITING_FEEDBACK:
        WAITING_FEEDBACK.remove(user.id)

        # confirm to user
        await update.message.reply_text("🙏 Thanks for your feedback!")

        # forward to owner(s)
        for oid in OWNER_IDS:
            try:
                await context.bot.send_message(
                    oid,
                    f"💌 Feedback from {user.first_name} (@{user.username} | {user.id}):\n\n{text}"
                )
            except Exception as e:
                log.error("Could not send feedback to owner %s: %s", oid, e)
    else:
        # Non-command loose message
        await update.message.reply_text("💡 Use /help to see commands.")

# ---------- error handler ----------
async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE):
    log.exception("Unhandled error: %s", context.error)

# ---------- app ----------
def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is missing in your .env")

    app = Application.builder().token(BOT_TOKEN).build()

    # commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("feedback", feedback_cmd))

    # callbacks
    app.add_handler(CallbackQueryHandler(on_about, pattern="^about$"))
    app.add_handler(CallbackQueryHandler(on_help_btn, pattern="^help$"))
    app.add_handler(CallbackQueryHandler(on_feedback_btn, pattern="^feedback$"))

    # text messages (captures feedback)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.add_error_handler(on_error)

    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
