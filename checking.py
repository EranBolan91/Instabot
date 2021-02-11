from bot_folder import main_bot
from selenium import webdriver

import time

if __name__ == "__main__":
    #PROXY = "5.253.186.198:213"
    # webdriver.DesiredCapabilities.CHROME['proxy'] = {
    #     "httpProxy": proxy,
    #     "ftpProxy": proxy,
    #     "sslProxy": proxy,
    #     "proxyType": "MANUAL",
    #
    # }
    #
    # with webdriver.Chrome() as driver:
    #     # Open URL
    #     driver.get("https://google.com")
    PROXY = "185.219.162.242:21326"
    #PROXY = "85.209.217.159:21284"
    #chrome_options = webdriver.ChromeOptions()
    #chrome_options.add_argument('--proxy-server=http://%s' % PROXY)

    #chrome = webdriver.Chrome(options=chrome_options)
    #chrome.get("http://whatismyipaddress.com")
    insta = main_bot.InstagramBot('eranbolan91@gmail.com', 'eranbolan91', False)
    insta._login()
    time.sleep(2)

