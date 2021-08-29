import os
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
import time
from symbols import symbols_dropbox
import datetime as dt
import pathlib
from persiantools.jdatetime import JalaliDateTime
import threading
from queue import Queue
import multiprocessing

CPU_CORES = multiprocessing.cpu_count()
DELIMITER = '│'

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


def scrape_tse_hh(symbols=None , print_data=False , log=False):
    # --
    if symbols is None:
        raise ValueError('please choose at list one symbol')
    # to ensure symbols is always a list even if the input is a dict:
    s = list()
    for symbol in symbols:
        s.append(symbol)
    symbols = s

    while True:
        processed = list()
        for i , symbol in enumerate(symbols):

            symbol_id = symbols_dropbox[symbol]
            url = 'http://www.tsetmc.ir/Loader.aspx?ParTree=151311&i=' + symbol_id
            chrome_driver_path = 'C:/Users\ALIREZA\PycharmProjects\Iran_Market\Web Scrapping\webdriver\chromedriver.exe'

            browser = webdriver.Chrome(chrome_driver_path)
            browser.get(url)

            # click حقیقی-حقوقی button
            try:
                python_button = browser.find_elements_by_xpath("//a[@href='#' and @class='violet']")[0]
            except:
                continue
            python_button.click()
            time.sleep(1)

            # get page source code
            source = browser.page_source
            browser.quit()
            page = BeautifulSoup(source , 'lxml')

            # scrapping the page html
            try:
                # year:
                year = int(page.find('td' , id='YearPart').text)
                # rows of data:
                table_main = page.find('tbody' , id='ClientTypeBody')
                table_rows = table_main.find_all('tr')
            except:
                continue

            print(f'{symbol} - {i:<{len(str(len(symbols))) + 1}} of {len(symbols)}')
            # extracting data
            days_data = list()
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
            _path = 'TSETMC_DATA/' + symbol + '_HH' + '.txt'
            with open(_path , 'w') as data_file:
                for day in days_data:
                    data_file.write(str(day))
                    data_file.write('\n')

            # save processed symbol from list
            processed.append(symbol)

            # print data
            if print_data:
                for day in days_data:
                    for row in day:
                        print(row)

            # create log
            if log:
                file_name = symbol + '__HH__' + dt.datetime.now().strftime('%y-%m-%d_%H-%M') + '.txt'
                first_col = 2
                col_width = 20
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
                        file.write(f'{delimiter}{i:<{first_col}}{delimiter}')
                        for j , row in enumerate(day):
                            print(j , row)
                            if 0 < j < 4:
                                file.write(delimiter + ' ' * first_col + delimiter)
                            if j == 0:
                                file.write('Quantity:'.ljust(col_width , ' ') + delimiter)
                                file.write(''.join(f'{cell:<{col_width}}{delimiter}' for cell in row))
                                file.write('\n')
                            elif j == 1:
                                file.write('Volume:'.ljust(col_width , ' ') + delimiter)
                                file.write(''.join(
                                        f'''{f"{cell[0]:<{col_width // 2}}{f'({cell[1]}%)':<{col_width // 2}}":<{col_width}}{delimiter}'''
                                        for cell in row))
                                file.write('\n')
                            elif j == 2:
                                file.write('Value:'.ljust(col_width , ' ') + delimiter)
                                file.write(''.join(f'{cell:<{col_width}}{delimiter}' for cell in row))
                                file.write('\n')
                            elif j == 3:
                                file.write('Average Price:'.ljust(col_width , ' ') + delimiter)
                                file.write(''.join(f'{cell:<{col_width}}{delimiter}' for cell in row))
                                file.write('\n')
                            elif j == 4:
                                continue
                            elif j == 5:
                                continue

                        file.write(row_separator + '\n')

                    file.write(row_end + '\n')

        for symbol in processed:
            symbols.remove(symbol)
        # stop the program if all symbols have been processed
        if len(symbols) == 0:
            break


if __name__ == '__main__':
    data = scrape_tse_hh(symbols=symbols_dropbox , print_data=True)
