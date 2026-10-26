import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

raw_admin_ids = os.getenv("ADMIN_IDS", "").strip()
ADMIN_IDS: list[int] = []
if raw_admin_ids:
    for x in raw_admin_ids.split(","):
        x = x.strip()
        if x.isdigit():
            ADMIN_IDS.append(int(x))

DATABASE_PATH = str(BASE_DIR / os.getenv("DATABASE_PATH", "kino_bot.db"))

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS
