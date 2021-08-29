import os
import requests
import concurrent.futures as cf
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
from symbols import symbols_dropbox
import datetime as dt
from persiantools.jdatetime import JalaliDateTime
import mechanize

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


def scrapper_hh(symbol , console=False , log=False):
    while True:
        symbol_id = symbols_dropbox[symbol]
        if symbol_id == 'deleted':
            print(f'{symbol} is deleted')
            break
        url = 'http://www.tsetmc.ir/Loader.aspx?ParTree=151311&i=' + symbol_id
        browser = mechanize.Browser()
        source = browser.open(url)

        page = BeautifulSoup(source , 'lxml')
        print(page.text)

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
            continue

        print(symbol)
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
        _path = '../../Data/TSETMC_DATA/' + symbol + '_HH' + '.txt'
        with open(_path , 'w') as data_file:
            for day in days_data:
                data_file.write(str(day))
                data_file.write('\n')

        # print data
        if console:
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

        break


if __name__ == '__main__':
    url = 'http://www.tsetmc.ir/Loader.aspx?ParTree=151311&i=' + '63917421733088077'
    browser = mechanize.Browser()
    source = browser.open(url)
    source = browser.geturl('http://www.tsetmc.com/tsev2/data/clienttype.aspx?i=63917421733088077')

    page = BeautifulSoup(source , 'lxml')
    print(page.text)
