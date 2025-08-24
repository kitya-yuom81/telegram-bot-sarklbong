# bot/handlers/admin.py
from __future__ import annotations
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from bot.settings import OWNER_IDS
from bot.utils.security import is_owner
from bot.db.base import Session
from bot.services.feedback_service import get_recent_feedbacks
from bot.db.crud import counts

def _parse_page(args: list[str]) -> int:
    if not args:
        return 1
    try:
        p = int(args[0])
        return p if p > 0 else 1
    except ValueError:
        return 1

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_owner(uid, OWNER_IDS):
        return await update.message.reply_text("⛔ Not allowed.")
    async with Session() as session:
        user_count, fb_count = await counts(session)
    await update.message.reply_text(f"📊 Stats\n• Users: {user_count}\n• Feedback: {fb_count}")

async def feedbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_owner(uid, OWNER_IDS):
        return await update.message.reply_text("⛔ Not allowed.")

    page = _parse_page(context.args)
    page_size = 5
    offset = (page - 1) * page_size

    async with Session() as session:
        items = await get_recent_feedbacks(session, limit=page_size, offset=offset)

    if not items:
        return await update.message.reply_text("No feedback on this page.")

    lines = [f"📥 Recent feedback (page {page}):"]
    for fb in items:
        user_part = f"{fb['first_name'] or ''} @{fb['username']}" if fb['username'] else f"{fb['first_name'] or ''}"
        lines.append(f"• #{fb['id']} from {user_part} ({fb['user_id']}):\n  {fb['message']}")
    await update.message.reply_text("\n".join(lines))

def register_admin_handlers(app):
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("feedbacks", feedbacks))
