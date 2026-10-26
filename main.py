import os

# instabot.db, instabot.key, .env, logs/ and screen_shots/ live next to this file. Work from here
# even when the app is started from another folder (a shortcut, another terminal folder), or it
# would open an empty database and make a new password key there.
os.chdir(os.path.dirname(os.path.abspath(__file__)))

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
