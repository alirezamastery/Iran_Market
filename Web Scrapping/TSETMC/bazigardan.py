import os
import requests
import concurrent.futures as cf
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
import time
from symbols import symbols_dropbox , symbols_dropbox_test
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


def scrapper_hh(symbol , print_data=False , log=False):
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

        # store data
        _path = '../../Data/TSETMC_DATA/' + symbol + '_HH' + '.txt'
        with open(_path , 'w') as data_file:
            for day in days_data:
                data_file.write(str(day))
                data_file.write('\n')

        # print data
        if print_data:
            for day in days_data:
                for row in day:
                    print(row)

        # create log
        if log:
            file_name = symbol + '__HH__' + dt.datetime.now().strftime('%y-%m-%d_%H-%M') + '.txt'
            first_col = 12
            col_width = 15
            delimiter = '│'
            row_line_format = '{}' + '─' * first_col + '{}' + \
                              '─' * col_width + '{}' + \
                              '─' * col_width + '{}' + \
                              '─' * col_width + '{}' + \
                              '─' * col_width + '{}' + \
                              '─' * col_width + '{}'
            row_separator = row_line_format.format('├' , '┼' , '┼' , '┼' , '┼' , '┼' , '┤')
            row_start = row_line_format.format('┌' , '┬' , '┼' , '┼' , '┼' , '┼' , '┤')
            row_end = row_line_format.format('└' , '┴' , '┴' , '┴' , '┴' , '┴' , '┘')

            with open(file_name , 'w' , encoding='utf-8') as file:

                file.write(f'{" ":{first_col + 2}}{" ":{col_width}}'
                           f'┌{"":─<{col_width * 2 + 1}}┬'
                           f'{"":─<{col_width * 2 + 1}}┐\n')
                file.write(f'{" ":{first_col + 2}}{" ":{col_width}}{delimiter}'
                           f'{"Buy":<{col_width * 2 + 1}}{delimiter}'
                           f'{"Sell":<{col_width * 2 + 1}}{delimiter}\n')
                file.write(f'{" ":{first_col + 2}}{" ":{col_width}}'
                           f'├{"":─<{col_width}}┬'
                           f'{"":─<{col_width}}┼'
                           f'{"":─<{col_width}}┬'
                           f'{"":─<{col_width}}┤\n')
                file.write(f'{" ":{first_col + 2}}{" ":{col_width}}{delimiter}'
                           f'{"Haghighi":<{col_width}}{delimiter}{"Hoghooghi":<{col_width}}{delimiter}'
                           f'{"Haghighi":<{col_width}}{delimiter}{"Hoghooghi":<{col_width}}{delimiter}\n')
                file.write(row_start + '\n')

                for i , day in enumerate(days_data):
                    for j , row in enumerate(day):
                        if 2 <= j <= 4:
                            file.write(delimiter + ' ' * first_col + delimiter)
                        if j == 0:
                            file.write(f'{delimiter}{row:^{first_col}}{delimiter}')
                        if j == 1:
                            file.write('Quantity:'.rjust(col_width , ' ') + delimiter)
                            file.write(''.join(f'{cell:<{col_width}}{delimiter}' for cell in row))
                            file.write('\n')
                        elif j == 2:
                            file.write('Volume:'.rjust(col_width , ' ') + delimiter)
                            file.write(''.join(
                                    f'''{f"{cell[0]:<{col_width // 2}}{f'({cell[1]}%)':<{col_width // 2}}":<{col_width}}{delimiter}'''
                                    for cell in row))
                            file.write('\n')
                        elif j == 3:
                            file.write('Value:'.rjust(col_width , ' ') + delimiter)
                            file.write(''.join(f'{cell:<{col_width}}{delimiter}' for cell in row))
                            file.write('\n')
                        elif j == 4:
                            file.write('Average Price:'.rjust(col_width , ' ') + delimiter)
                            file.write(''.join(f'{cell:<{col_width}}{delimiter}' for cell in row))
                            file.write('\n')
                        elif j == 5:
                            continue
                        elif j == 6:
                            continue
                    if i < len(days_data) - 1:
                        file.write(row_separator + '\n')
                file.write(row_end + '\n')

        break
    return [symbol , days_data]


if __name__ == '__main__':
    if os.path.isfile(TEMP_FILE):
        symbols = dict()
        with open(TEMP_FILE , 'r') as tmp_file:
            for line in tmp_file.readlines():
                key , value = line.strip().split(',')
                symbols[key] = value
        os.remove(TEMP_FILE)
    else:
        symbols = symbols_dropbox

    start = time.perf_counter()

    with cf.ThreadPoolExecutor(max_workers=4) as executor:
        results = executor.map(scrapper_hh , symbols)

    finish = time.perf_counter()
    print(f'\nFinished in {round((finish - start) / 60 , 1)} minutes')

    lines = list()
    for res in results:
        if len(res[1]) == 0:
            continue
        sum_buy = 0
        sum_sell = 0
        avrg_buy = 0
        avrg_sell = 0
        for row in res[1]:
            sum_buy += row[2][1][1]
            sum_sell += row[2][3][1]

        avrg_buy = round(sum_buy / len(res[1]) , 2)
        avrg_sell = round(sum_sell / len(res[1]) , 2)
        print(f'{res[0]:<20} {DELIMITER} buy: {avrg_buy:<5.2f} %  {DELIMITER} sell: {avrg_sell:<5.2f} %')
        lines.append([res[0] , avrg_buy , avrg_sell])

    with open('bazargardani.csv' , 'w') as file:
        for l in lines:
            file.write(l)
            file.write('\n')
