from bot_folder import main_bot

if __name__ == "__main__":
    insta = main_bot.InstagramBot('eranbolan91@gmail.com', 'eranbolan91', False)
    insta._login()
    insta._nav_user('eranbolandian')
    insta._screen_shot('eranbolan')
    insta._send_email('eranbolan', '20', '10/10/2020')
