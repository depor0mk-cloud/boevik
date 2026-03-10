import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8555470613:AAEgNXzgg59KUUPEOYdh4Wtgr9ZU7EPR1AM")
WAR_TICK_HOURS = int(os.getenv("WAR_TICK_HOURS", 1))
