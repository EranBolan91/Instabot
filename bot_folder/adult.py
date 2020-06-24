from selenium import webdriver
from selenium.webdriver.common.keys import Keys

#/html/body/div[2]/div/div/div/div[1]/table/tbody/tr

driver = webdriver.Chrome('../chromedriver.exe')
driver.get('https://www.hubtraffic.com/login')
driver.find_element_by_name('username').send_keys('eranbolan')
driver.find_element_by_name('password').send_keys('eranbolan91' + Keys.RETURN)
driver.get('https://www.hubtraffic.com/rss?site_id=3')

rows = len(driver.find_elements_by_xpath('/html/body/div[2]/div/div/div/div[1]/table/tbody/tr'))
list = []
for row in range(2, rows+1):
    list.append(driver.find_element_by_xpath("/html/body/div[2]/div/div/div/div[1]/table/tbody/tr["+str(row)+"]/td[2]").text)


print(list)
