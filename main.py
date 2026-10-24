import os

from dotenv import load_dotenv

load_dotenv()  # .env was never loaded before (Mailgun vars)

from ui.app import run

if __name__ == "__main__":
    # bots save block screenshots here and fail if the folder is missing
    os.makedirs("screen_shots", exist_ok=True)
    run()
