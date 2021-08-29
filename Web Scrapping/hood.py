import os
import requests
import concurrent.futures as cf
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
import time
from symbols import symbols_dropbox
import datetime as dt

powers = ['850' , '900' , '950' , '1000' , '1050' , '1100']
url = 'https://www.satak.ir/master-plus/masterplus-hood/'
chrome_driver_path = 'C:/Users/ALIREZA/PycharmProjects/Iran_Market/Web Scrapping/webdriver/chromedriver.exe'

chrome_options = ChromeOptions()
chrome_options.headless = False
browser = webdriver.Chrome(executable_path=chrome_driver_path , options=chrome_options)
browser.get(url)

# get page source code
source = browser.page_source
page = BeautifulSoup(source , 'lxml')

articles = page.find_all('article' , class_='post')
links = list()
for article in articles:
    link = article.find('a' , href=True)
    links.append(link['href'])
    # print(link['href'])

for link in links:
    browser.get(link)
    time.sleep(1)
    sub_source = browser.page_source
    page = BeautifulSoup(sub_source , 'lxml')
    rows = page.find_all('li')
    # for row in rows:
    #     print(row.string)
    for row in rows:
        for p in powers:
            if p in row.text:
                print(p)
                print(link)
                print('-' * 100)

# browser.quit()
# browser.close()