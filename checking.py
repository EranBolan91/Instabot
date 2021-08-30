from bot_folder import main_bot
from selenium import webdriver
from re import search
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
    if search("https://www.instagram.com/restriction/", "https://www.instagram.com/restriction/54"):
        print("yes")
    else:
        print("no")
    #chrome = webdriver.Chrome(options=chrome_options)
    #chrome.get("http://whatismyipaddress.com")
    #insta = main_bot.InstagramBot('eranbolan91@gmail.com', 'eranbolan91', False, 0)
    #insta._login()
    #cur = insta.check_current_url()
    #print(cur)
    #time.sleep(2)

