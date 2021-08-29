import os
import requests
import concurrent.futures as cf
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
import time
import symbols
from symbols import symbols_dropbox
import datetime as dt
from persiantools.jdatetime import JalaliDateTime

DELIMITER = '│'
TEMP_FILE = 'failed_update.txt'
PERSIAN_MONTHS = {'فروردین':  1 ,
                  'اردیبهشت': 2 ,
                  'خرداد':    3 ,
                  'تیر':      4 ,
                  'مرداد':    5 ,
                  'شهریور':   6 ,
                  'مهر':      7 ,
                  'آبان':     8 ,
                  'آذر':      9 ,
                  'دی':       10 ,
                  'بهمن':     11 ,
                  'اسفند':    12 ,
                  }


def scrapper_hh_current_year(symbol , print_data=True):
    attempts = 0
    days_data = list()
    while True:
        attempts += 1
        symbol_id = symbols_dropbox[symbol]
        if symbol_id == 'deleted':
            print(f'{symbol} is deleted')
            break

        url = 'http://www.tsetmc.com/Loader.aspx?ParTree=151311&i=' + symbol_id
        chrome_driver_path = 'C:/Users/ALIREZA/PycharmProjects/Iran_Market/Web Scrapping/webdriver/chromedriver.exe'

        chrome_options = ChromeOptions()
        chrome_options.headless = False
        browser = webdriver.Chrome(executable_path=chrome_driver_path , options=chrome_options)
        browser.get(url)

        # click حقیقی-حقوقی button
        try:
            python_button = browser.find_elements_by_xpath("//a[@href='#' and @class='violet']")[0]
        except:
            browser.quit()
            continue
        python_button.click()
        time.sleep(2)

        # get page source code
        source = browser.page_source
        browser.close()
        browser.quit()
        page = BeautifulSoup(source , 'lxml')

        # scrapping the page html
        try:
            check = page.find('div' , class_='MainContainer')
            if 'Demo Version' in check:
                print(f'*** {symbol} said Demo Version ***')
                break
            # year:
            year = int(page.find('td' , id='YearPart').text)
            # rows of data:
            table_main = page.find('tbody' , id='ClientTypeBody')
            table_rows = table_main.find_all('tr')
        except:
            if attempts > 5:
                print(f'could not get {symbol} data. number of attempts: {attempts}')
                with open(TEMP_FILE , 'a' , newline='') as f:
                    f.write(str(symbol) + ',' + str(symbol_id))
                break
            else:
                continue

        print(symbol)
        # extracting data
        day_data = list()
        row_count = 0
        for index , row in enumerate(table_rows):
            row_code = row.find_all('td')
            row_data = list()
            for j , d in enumerate(row_code):
                if row_count == 0:
                    if j == 0:
                        month = d.find('div' , class_='CalMonth').text
                        day = int(d.find('div' , class_='CalDay').text)
                        month = PERSIAN_MONTHS[month]
                        date = JalaliDateTime(year , month , day).to_gregorian().strftime('%Y-%m-%d')
                        day_data.append(date)
                    elif j > 1:
                        row_data.append(int(d.text.replace(',' , '')))
                elif row_count == 1:
                    if j > 0:
                        cell_code = d.find_all('div')
                        cell_data = list()
                        for div in cell_code:
                            cell_data.append(int(div.get('title').replace(',' , '')))
                        row_data.append(cell_data)
                elif row_count == 2:
                    if j > 0:
                        cell_code = d.find('div')
                        cell_data = int(cell_code.get('title').replace(',' , ''))
                        row_data.append(cell_data)
                elif row_count == 3:
                    if j > 0:
                        row_data.append(float(d.text))
                elif row_count == 4:
                    if j == 2:
                        data = d.find('div')
                        row_data.append(int(data.get('title').replace(',' , '')))
                else:
                    continue
            day_data.append(row_data)
            row_count += 1
            if row_count == 6:
                days_data.append(day_data)
                day_data = list()
                row_count = 0

        # print data
        if print_data:
            for day in days_data:
                for row in day:
                    print(row)

        break

    return [symbol , days_data]


def scrapper_hh_history(symbol , print_data=False):
    attempts = 0
    failed = False
    done = False
    first_page = True
    symbol_id = symbols_dropbox[symbol]

    while True:
        days_data = list()
        attempts += 1
        if symbol_id == 'deleted':
            print(f'{symbol} is deleted')
            break

        url = 'http://www.tsetmc.com/Loader.aspx?ParTree=151311&i=' + symbol_id
        chrome_driver_path = 'C:/Users/ALIREZA/PycharmProjects/Iran_Market/Web Scrapping/webdriver/chromedriver.exe'

        chrome_options = ChromeOptions()
        chrome_options.headless = False
        browser = webdriver.Chrome(executable_path=chrome_driver_path , options=chrome_options)
        browser.get(url)

        # click حقیقی-حقوقی button
        try:
            python_button = browser.find_elements_by_xpath("//a[@href='#' and @class='violet']")[0]
        except:
            browser.quit()
            browser.close()
            break
        python_button.click()
        time.sleep(2)
        print(f'{symbol:<25} {DELIMITER} Attempt: {attempts}')

        # scrapping each year data:
        while True:
            # go to previous years after this year:
            if not first_page:
                try:
                    year_button = browser.find_element_by_link_text('-')
                    year_button.click()
                    time.sleep(0.5)
                except:
                    browser.quit()
                    break
            # get page source code
            source = browser.page_source
            page = BeautifulSoup(source , 'lxml')

            # scrapping the page html
            try:
                check = page.find('div' , class_='MainContainer')
                if 'Demo Version' in check:
                    print(f'*** {symbol} said Demo Version ***')
                    failed = True
                    break
                # year:
                year = int(page.find('td' , id='YearPart').text)
                if first_page:
                    first_page = False
                # rows of data:
                table_main = page.find('tbody' , id='ClientTypeBody')
                table_rows = table_main.find_all('tr')
                if len(table_rows) == 0:
                    done = True
                    browser.quit()
                    break
            except:
                if attempts > 5:
                    print(f'could not get {symbol} data. number of attempts: {attempts}')
                    with open(TEMP_FILE , 'a' , newline='') as f:
                        f.write(str(symbol) + ',' + str(symbol_id))
                    failed = True
                    break
                else:
                    continue

            # extracting data
            day_data = list()
            row_count = 0
            for index , row in enumerate(table_rows):
                row_code = row.find_all('td')
                row_data = list()
                for j , d in enumerate(row_code):
                    if row_count == 0:
                        if j == 0:
                            month = d.find('div' , class_='CalMonth').text
                            day = int(d.find('div' , class_='CalDay').text)
                            month = PERSIAN_MONTHS[month]
                            date_shamsi = f'{year}-{month:02d}-{day:02d}'
                            date_miladi = JalaliDateTime(year , month , day).to_gregorian().strftime('%Y-%m-%d')
                            day_data.append([date_shamsi , date_miladi])
                        elif j > 1:
                            row_data.append(int(d.text.replace(',' , '')))
                    elif row_count == 1:
                        if j > 0:
                            cell_code = d.find_all('div')
                            cell_data = list()
                            for div in cell_code:
                                cell_data.append(int(div.get('title').replace(',' , '')))
                            row_data.append(cell_data)
                    elif row_count == 2:
                        if j > 0:
                            cell_code = d.find('div')
                            cell_data = int(cell_code.get('title').replace(',' , ''))
                            row_data.append(cell_data)
                    elif row_count == 3:
                        if j > 0:
                            row_data.append(float(d.text))
                    elif row_count == 4:
                        if j == 2:
                            data = d.find('div')
                            row_data.append(int(data.get('title').replace(',' , '')))
                    else:
                        continue
                day_data.append(row_data)
                row_count += 1
                if row_count == 6:
                    days_data.append(day_data)
                    day_data = list()
                    row_count = 0

            # print data
            if print_data:
                for day in days_data:
                    for row in day:
                        print(row)

        if done or failed:
            break

    # Store Data:
    DATA_PATH = '../../../Data/TSETMC_DATA/HH_History/'
    if len(days_data) > 0:
        file_name = DATA_PATH + symbol + '__HH_History__until_' + days_data[0][0][0] + '.csv'
        with open(file_name , 'w') as file:
            # Header:
            file.write('DATE_JALALI,DATE_GREGORIAN,BUYERS_IND,BUYERS_CORP,SELLERS_IND,'
                       'SELLERS_CORP,VOL_BUY_IND,VOL_BUY_IND_%,VOL_BUY_CORP,'
                       'VOL_BUY_CORP_%,VOL_SELL_IND,VOL_SELL_IND_%,VOL_SELL_CORP,'
                       'VOL_SELL_CORP_%,VALUE_BUY_IND,VALUE_BUY_CORP,VALUE_SELL_IND,'
                       'VALUE_SELL_CORP,AVRG_PRICE_BUY_IND,AVRG_PRICE_BUY_CORP,'
                       'AVRG_PRICE_SELL_IND,AVRG_PRICE_SELL_CORP,CORP_TO_IND')
            file.write('\n')
            # Data:
            for day in days_data:
                file.write(f'{day[0][0]},{day[0][1]},{day[1][0]},{day[1][1]},{day[1][2]},{day[1][3]},{day[2][0][0]},'
                           f'{day[2][0][1]},{day[2][1][0]},{day[2][1][1]},{day[2][2][0]},{day[2][2][1]},{day[2][3][0]},'
                           f'{day[2][3][1]},{day[3][0]},{day[3][1]},{day[3][2]},{day[3][3]},{day[4][0]},{day[4][1]},'
                           f'{day[4][2]},{day[4][3]},{day[5][0]}')
                file.write('\n')

    # return [symbol , days_data]
