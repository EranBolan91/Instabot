import os

from dotenv import load_dotenv

load_dotenv()  # .env was never loaded before (Mailgun vars)

from ui.app import run
from utils.log import setup_logging

if __name__ == "__main__":
    # bots save block screenshots here and fail if the folder is missing
    os.makedirs("screen_shots", exist_ok=True)
    # errors go to the log panel and to logs/instabot.log
    setup_logging()
    run()
