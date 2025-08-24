# bot/main.py
import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)
from sqlalchemy import select, desc  # NEW: for /feedbacks query

from bot.settings import BOT_TOKEN, OWNER_IDS
from bot.db.base import init_db, Session
from bot.db.crud import get_or_create_user, create_feedback, counts
from bot.db.models import Feedback, User  # NEW: join user+feedback for /feedbacks

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

# ---------- state ----------
WAITING_FEEDBACK: set[int] = set()

# ---------- commands ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    # persist (upsert) user in DB
    async with Session() as session:
        await get_or_create_user(
            session,
            tg_id=user.id,
            username=user.username,
            first=user.first_name,
            lang=(user.language_code or None),
        )
    await update.message.reply_text(
        f"Hi {user.first_name}! 👋\nChoose an option:",
        reply_markup=MENU
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Commands:\n"
        "/start — open menu\n"
        "/help — this help\n"
        "/feedback — send feedback\n"
        "/cancel — cancel feedback mode\n"
        "/stats — owner only\n"
        "/feedbacks [page] — owner only\n"
    )

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in OWNER_IDS:
        return await update.message.reply_text("⛔ Not allowed.")
    async with Session() as session:
        user_count, fb_count = await counts(session)
    await update.message.reply_text(
        f"📊 Stats\n• Users: {user_count}\n• Feedback: {fb_count}"
    )

# ---------- callbacks ----------
async def on_about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await q.edit_message_text("Sample bot with DB (SQLite + SQLAlchemy async).")

async def on_help_btn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await q.edit_message_text("Use the menu buttons or type /help.")

# ---------- feedback flow ----------
async def feedback_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    WAITING_FEEDBACK.add(user.id)
    if update.message:
        await update.message.reply_text("✍️ Please type your feedback now (send one message). Send /cancel to exit.")
    elif update.callback_query:
        await update.callback_query.edit_message_text("✍️ Please type your feedback now (send one message). Send /cancel to exit.")

async def cancel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id in WAITING_FEEDBACK:
        WAITING_FEEDBACK.remove(user.id)
        return await update.message.reply_text("❎ Feedback canceled.")
    return await update.message.reply_text("You’re not in feedback mode.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text

    if user.id in WAITING_FEEDBACK:
        WAITING_FEEDBACK.remove(user.id)

        # persist feedback
        async with Session() as session:
            db_user = await get_or_create_user(
                session,
                tg_id=user.id,
                username=user.username,
                first=user.first_name,
                lang=(user.language_code or None),
            )
            await create_feedback(session, user_id=db_user.id, message=text)

        # confirm to user
        await update.message.reply_text("🙏 Thanks for your feedback! Saved.")

        # forward to owner(s)
        for oid in OWNER_IDS:
            try:
                await context.bot.send_message(
                    oid,
                    f"💌 Feedback from {user.first_name} (@{user.username} | {user.id}):\n\n{text}"
                )
            except Exception as e:
                log.error("Owner notify failed (%s): %s", oid, e)
    else:
        await update.message.reply_text("💡 Use /help to see commands.")

# ---------- admin: list feedbacks with pagination ----------
async def feedbacks_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in OWNER_IDS:
        return await update.message.reply_text("⛔ Not allowed.")

    # parse page number: /feedbacks [page]
    page = 1
    if context.args:
        try:
            page = max(1, int(context.args[0]))
        except ValueError:
            page = 1

    page_size = 5
    offset = (page - 1) * page_size

    async with Session() as session:
        # SELECT Feedback JOIN User, order by newest first, paginate
        stmt = (
            select(Feedback, User)
            .join(User, Feedback.user_id == User.id)
            .order_by(desc(Feedback.created_at))
            .limit(page_size)
            .offset(offset)
        )
        rows = (await session.execute(stmt)).all()

    if not rows:
        return await update.message.reply_text(f"No feedback on page {page}.")

    lines = [f"📥 Recent feedback (page {page}):"]
    for fb, user in rows:
        who = f"{user.first_name or ''} @{user.username}" if user.username else (user.first_name or "")
        uid_str = f"({user.tg_id})" if user.tg_id else ""
        lines.append(f"• #{fb.id} from {who} {uid_str}:\n  {fb.message}")
    await update.message.reply_text("\n".join(lines))

# ---------- error handler ----------
async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE):
    log.exception("Unhandled error: %s", context.error)

# ---------- app entry ----------
def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is missing in your .env")

    # Ensure DB schema exists once before starting
    asyncio.run(init_db())

    app = Application.builder().token(BOT_TOKEN).build()

    # commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("feedback", feedback_cmd))
    app.add_handler(CommandHandler("cancel", cancel_cmd))        # NEW
    app.add_handler(CommandHandler("feedbacks", feedbacks_cmd))  # NEW

    # buttons
    app.add_handler(CallbackQueryHandler(on_about, pattern="^about$"))
    app.add_handler(CallbackQueryHandler(on_help_btn, pattern="^help$"))
    app.add_handler(CallbackQueryHandler(feedback_cmd, pattern="^feedback$"))

    # text messages (captures feedback)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.add_error_handler(on_error)

    # Python 3.12: set a loop so run_polling has one
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
