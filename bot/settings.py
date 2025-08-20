from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_IDS = {int(x) for x in os.getenv("BOT_OWNER_IDS", "").split(",") if x}
ENV = os.getenv("ENV", "dev")
