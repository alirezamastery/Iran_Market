from bs4 import BeautifulSoup
from selenium import webdriver
import time
from symbols import symbols as symbols_five_character
import datetime as dt
import pathlib
import symbols

url = 'https://sbunavid.vums.ac.ir/account/loginsama'
chrome_driver_path = 'C:/Users/ALIREZA/PycharmProjects/Iran_Market/Web Scrapping/webdriver/chromedriver.exe'

browser = webdriver.Chrome(chrome_driver_path)  # Optional argument, if not specified will search path.
browser.get(url)
sama_button = browser.find_elements_by_xpath("//a[@href='/account/samasso?uId=60']")[0]
sama_button.click()

user_type = browser.find_element_by_name('usertype')
user_type.send_keys('استاد')

username = browser.find_element_by_name('username')
username.send_keys('10130716')

password = browser.find_element_by_name('password')
password.send_keys('61703101')

sama_button = browser.find_elements_by_xpath("//input[@type='submit']")[0]
print(sama_button)
sama_button.click()
time.sleep(5)
# python_button = browser.find_elements_by_xpath("//a[@href='#' and @class='torquoise']")[0]