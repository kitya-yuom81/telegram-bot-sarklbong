# Telegram Feedback Bot (Python, Async, SQLite)

A simple, production-style Telegram bot built with **python-telegram-bot v21** (async) and **SQLAlchemy**.  
It supports a feedback flow, owner-only admin commands, and a tidy, scalable code structure.

---

## ✨ Features
- `/start` shows an inline menu (About / Help / Feedback)
- `/feedback` → user sends one message; it’s **saved to DB** and **forwarded to owners**
- `/cancel` cancels feedback mode
- `/help` lists commands
- **Owner only:**  
  - `/stats` shows total users & feedback count  
  - `/feedbacks [page]` lists recent feedback (5 per page)

---

## 🧰 Tech
- Python 3.11+ (tested on 3.12)
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) v21 (async)
- SQLAlchemy 2 (async) + SQLite (via `aiosqlite`)
- Structured project: handlers / services / db / utils

---

