from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import symbols
import pandas as pd
import copy

wrong = list()
syms = copy.deepcopy(symbols.symbols_dropbox)
column_width1 = 15
column_width2 = 12

print()
while True:
    processed = list()
    for key , value in syms.items():
        sym = str(key).replace('_Share_D' , '')
        if str(value) == 'deleted':
            print(f'   {sym:<{column_width1}} │ {"DELETED":<{column_width2}} │')
            processed.append(key)
            continue

        ur = str(value)
        url = 'http://www.tsetmc.ir/Loader.aspx?ParTree=151311&i=' + ur

        path = '../all/' + str(key) + '.txt'
        df = pd.read_csv(path ,
                         skiprows=1 ,
                         header=None ,
                         parse_dates=True ,
                         dayfirst=True ,
                         index_col=[2])
        open_price = df[4]
        time.sleep(10)
        from_file = int(open_price[-1])
        latest = df.index[-1].strftime('%Y-%m-%d')

        chrome_driver_path = 'C:/Users/ALIREZA/PycharmProjects/Iran_Market/Data/web/webdriver/chromedriver.exe'

        chrome_options = Options()
        chrome_options.headless = True
        browser = webdriver.Chrome(options=chrome_options , executable_path=chrome_driver_path)
        browser.get(url)

        try:
            python_button = browser.find_elements_by_xpath("//a[@href='#' and @class='red']")[0]
        except:
            continue
        python_button.click()
        time.sleep(8)

        # get page source code
        source = browser.page_source
        browser.quit()
        page = BeautifulSoup(source , 'lxml')

        try:
            mainbox = page.find('div' , class_='box1 zFull silver' , id='MainBox')
            MainContent = mainbox.find('div' , class_='tabcontent content' , id='MainContent')
            TopBox = MainContent.find('div' , id='TopBox')
            box2 = TopBox.find('div' , class_='box2 zi1')
            box6 = box2.find('div' , class_='box6 h80')
            table = box6.find('table')
            tbody = table.find('tbody')
            tr = tbody.find_all('tr')
        except:
            continue

        if tr[3].td.text == '':
            continue

        from_site = int(tr[3].td.text.replace(',' , ''))

        if from_site == 0:
            print(f'   {sym:<{column_width1}} │ {"DELETED":<{column_width2}} │')
        elif latest != '2020-05-20':
            print(f'   {sym:<{column_width1}} │ {"NOT UPDATED":<{column_width2}} │')
        elif from_file != from_site:
            wrong.append(key)
            print(f' * {sym:<{column_width1}} │ {"WRONG":<{column_width2}} │ '
                  f'from file: {from_file:<10} from tsetmc: {from_site:<10}')
        else:
            print(f'   {sym:<{column_width1}} │ {"OK":<{column_width2}} │')

        processed.append(key)

    for p in processed:
        del syms[p]
    # stop the program if all symbols have been processed
    if len(syms) == 0:
        break

if len(wrong) > 0:
    print('\nWrong URLs:')
    with open('wrong_url.txt' , 'w') as file:
        for sym in wrong:
            file.write(sym + '\n')
            print(sym)
