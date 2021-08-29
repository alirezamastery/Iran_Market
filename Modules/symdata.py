import sys
import os
import math
import time
import pandas as pd
import datetime as dt
import dropbox
import backtrader as bt

# download a file from dropbox root folder:
# g = dbx.files_download('/' + 'REMAPNA_Share_D.txt')
# q = dbx.files_list_folder('/Data Rahavard/Rahavard')
rahavard_header = ['Ticker' , 'Per' , 'Date' , 'Time' , 'Open' , 'High' , 'Low' , 'Close' , 'Vol' , 'Openint' , ]


class StratData(bt.feeds.PandasData):
    lines = ('openinterest' , 'volume' , 'BUYERS_IND' , 'BUYERS_CORP' , 'SELLERS_IND' , 'SELLERS_CORP' , 'VOL_BUY_IND' ,
             'VOL_BUY_IND_%' , 'VOL_BUY_CORP' , 'VOL_BUY_CORP_%' , 'VOL_SELL_IND' , 'VOL_SELL_IND_%' , 'VOL_SELL_CORP' ,
             'VOL_SELL_CORP_%' , 'CORP_TO_IND')

    params = (
        ('open' , 'OPEN') ,
        ('high' , 'HIGH') ,
        ('low' , 'LOW') ,
        ('close' , 'CLOSE') ,
        ('volume' , 'VOLUME') ,
        ('openinterest' , 'OPENINT') ,
        ('BUYERS_IND' , 'BUYERS_IND') ,
        ('BUYERS_CORP' , 'BUYERS_CORP') ,
        ('SELLERS_IND' , 'SELLERS_IND') ,
        ('SELLERS_CORP' , 'SELLERS_CORP') ,
        ('VOL_BUY_IND' , 'VOL_BUY_IND') ,
        ('VOL_BUY_IND_%' , 'VOL_BUY_IND_%') ,
        ('VOL_BUY_CORP' , 'VOL_BUY_CORP') ,
        ('VOL_BUY_CORP_%' , 'VOL_BUY_CORP_%') ,
        ('VOL_SELL_IND' , 'VOL_SELL_IND') ,
        ('VOL_SELL_IND_%' , 'VOL_SELL_IND_%') ,
        ('VOL_SELL_CORP' , 'VOL_SELL_CORP') ,
        ('VOL_SELL_CORP_%' , 'VOL_SELL_CORP_%') ,
        ('CORP_TO_IND' , 'CORP_TO_IND') ,
    )


class refresh_all_data:
    ACCESS_TOKEN = 'dPdfl4gIvmAAAAAAAAAAHKdNE3BWJ0v9ngpeZwqOrXv4ks3x_1XT6erwPecaK5GW'
    created_list = '../Lists/all_files.txt'
    storage_path = '../Data/all/'
    other_symbols = ['Dollar_D.txt' , 'TEPIX_D.txt']

    def __init__(self):
        self.dbx = dropbox.Dropbox(self.ACCESS_TOKEN)

        self.result = self.dbx.files_list_folder(path='/Data Rahavard/Rahavard/Eslahi/' , recursive=True)
        self.file_list = list()

        # get all files in the directory:
        self.process_entries(self.result.entries)
        while self.result.has_more:
            self.result = self.dbx.files_list_folder_continue(self.result.cursor)
            self.process_entries(self.result.entries)
        self.file_list.sort()
        for sym in self.other_symbols:
            self.file_list.insert(0 , sym)
        print(f'{len(self.file_list)} files')

        # store the list of files in a file:
        with open(self.created_list , 'w') as data_list:
            for i , d in enumerate(self.file_list):
                line = d.replace('.txt' , '')
                data_list.write(line + '\n')

        for i , d in enumerate(self.file_list):
            self.file_list[i] = [i , d]

        self.download()

    def process_entries(self , entries):
        for entry in entries:
            if isinstance(entry , dropbox.files.FileMetadata) and '_Share_D' in entry.name \
                    and 'conflicted' not in entry.name:
                self.file_list.append(entry.name)

    def download(self):
        print('Download Started')
        time1 = time.time()

        while True:
            downloaded = list()
            for i , d in enumerate(self.file_list):
                try:
                    metadata , res = self.dbx.files_download('/Data Rahavard/Rahavard/Eslahi/' + d[1])
                except:
                    print(f'could not download file number {d[0]}: {d[1]}')
                    continue
                with open(self.storage_path + d[1] , 'wb') as f:
                    f.write(res.content)
                downloaded.append(d)
                print(f'{d[0] + 1:<{len(str(len(self.file_list)))}} {str(d[1])}')
            for symbol in downloaded:
                self.file_list.remove(symbol)
            if len(self.file_list) == 0:
                break

        time2 = time.time()
        print(f'Download Finished in {round((time2 - time1) / 60 , 1)} minutes')


def refresh_data(file_name='symbols.txt' , created_list='../Lists/input_data/pairs.txt'):
    # read symbol names in the file:
    with open(file_name , 'r') as file:
        symbols = file.readlines()
    symbols = [x.strip() for x in symbols]
    # get access to dropbox account:
    ACCESS_TOKEN = 'dPdfl4gIvmAAAAAAAAAAHKdNE3BWJ0v9ngpeZwqOrXv4ks3x_1XT6erwPecaK5GW'
    dbx = dropbox.Dropbox(ACCESS_TOKEN)
    dbx.users_get_current_account()
    # check if file name is in dropbox folder: (uncompleted)
    # source = dbx.files_list_folder(path='/Data Rahavard/Rahavard/Eslahi/')
    # source_files = []
    # for file in source.entries:
    #     source_files.append(file.name.replace('.txt' , ''))
    #     print(file.name)
    # for i , sym in enumerate(symbols):
    #     if sym not in source_files:
    #         symbols.pop(i)

    list_file = open(created_list , 'w')
    for i in range(len(symbols)):
        # add name to list file:
        char_list = []
        for char in symbols[i]:
            if char != '_':
                char_list.append(char)
            else:
                break
        output_string = "".join(char_list)
        if i < len(symbols) - 1:
            list_file.write(output_string + '\n')
        else:
            list_file.write(output_string)
        # save content of the file:
        with open('../Data/selected/' + output_string + '.txt' , 'wb') as f:
            # try:
            metadata , res = dbx.files_download('/Data Rahavard/Rahavard/Eslahi/' + symbols[i] + '.txt')
            f.write(res.content)
            # except:
            #     raise ValueError('file number %d (%s) not found' % (i , symbols[i]))
        # loading bar animation:
        loading_bar(stage=i , process_length=len(symbols))

    list_file.close()


def get_close(symbol , start='2010-01-01' , end=dt.datetime.today()):
    sd = pd.read_csv('Data/' + symbol + '.txt' ,
                     skiprows=1 ,
                     header=None ,
                     parse_dates=[2] ,
                     dayfirst=True
                     )
    dates = sd[2]
    close = sd[7]
    data = pd.DataFrame({'Date': dates , 'Close': close})
    data.set_index('Date' , inplace=True)

    # date format should be like this: '2010-01-01 00:00:00'
    # start = dt.datetime(year=2010, month=1, day=1, hour=0, minute=0, second=0)

    date_index = pd.date_range(start , end)
    new_data = data.reindex(date_index , method='bfill')
    return new_data


def add_cerebro_data(cerebro ,
                     input_list='../../Lists/input_data/pairs.txt' ,
                     data_path='../../Data/selected/' ,
                     start='2010-01-01' ,
                     end='2020-01-01' ,
                     add_fixincome=False ,
                     fill_blanks=True ,
                     combined_data=False ,
                     combined_data_path='../../Data/Combined/' ,
                     show=None ,
                     printnames=False):
    if show is None:
        show = []
    if start < '2005-01-01':
        raise RuntimeError('data start date is before 2005 which is not acceptable')
    with open(input_list , 'r') as fl:
        symbols = fl.readlines()
        symbols = [x.strip() for x in symbols]
        if printnames:
            for i , sym in enumerate(symbols):
                print('%d- %s' % (i + 1 , sym))

    # __OLD CODE__:
    # datalist = []
    # syms = []
    # # add fix income data:
    # if add_fixincome:
    #     datalist.append([data_path + 'FIX_20%.csv' , 'FIX_20%'])
    # # add symbols data:
    # for sym in symbols:
    #     path = data_path + sym + '.txt'
    #     datalist.append([path , sym])
    #     syms.append(sym)
    if add_fixincome:
        symbols.insert(0 , 'FIX_20%')

    for i , symbol in enumerate(symbols):
        if combined_data:
            datapath = combined_data_path + symbol + '.csv'
            df = pd.read_csv(datapath , parse_dates=True , index_col=[0])
            df = df.loc[start:end]

            # Pass it to the backtrader datafeed and add it to the cerebro:
            data = StratData(dataname=df , name=symbol)
            if symbol not in show:
                data.plotinfo.plot = False
            cerebro.adddata(data , name=symbol)

        else:
            # datapath = datalist[i][0]
            if '_Share_D' not in symbol and symbol != 'TEPIX_D':
                datapath = data_path + symbol + '_Share_D' + '.txt'
            else:
                datapath = data_path + symbol + '.txt'
            df = pd.read_csv(datapath ,
                             skiprows=1 ,
                             header=None ,
                             parse_dates=True ,
                             dayfirst=True ,
                             index_col=[2])

            if add_fixincome and i == 0:
                close = df[9]
                candle_open = df[9]
                high = df[9]
                low = df[9]
                datafeed = pd.DataFrame(
                        {'open': candle_open , 'high': high , 'low': low , 'close': close , 'volume': 0})
            else:
                candle_open = df[4]
                high = df[5]
                low = df[6]
                close = df[7]
                volume = df[8]
                datafeed = pd.DataFrame(
                        {'open': candle_open , 'high': high , 'low': low , 'close': close , 'volume': volume})

            # fill the blank dates:
            if fill_blanks:
                date_index = pd.date_range(start , end)
                datafeed = datafeed[~datafeed.index.duplicated(keep='first')]
                datafeed = datafeed.reindex(date_index , method='bfill')
                df_days = pd.to_datetime(datafeed.index.date)
                market_days = pd.bdate_range(start=datafeed.index[0].date() ,
                                             end=datafeed.index[-1].date() ,
                                             weekmask='Sat Sun Mon Tue Wed' ,
                                             freq='C')
                datafeed = datafeed[df_days.isin(market_days)]
            else:
                datafeed = datafeed.loc[start:end]

            # Pass it to the backtrader datafeed and add it to the cerebro:
            data = bt.feeds.PandasData(dataname=datafeed , name=symbol , openinterest=None)
            if symbol not in show:
                data.plotinfo.plot = False
            cerebro.adddata(data , name=symbol)

    return symbols


def load_cerebro_data(input_list='../../Lists/input_data/pairs.txt' ,
                      data_path='../../Data/' ,
                      start='2010-01-01' ,
                      end='2020-01-01' ,
                      add_fixincome=False ,
                      show=None ,
                      printnames=False):
    if show is None:
        show = []
    if start < '2005-01-01':
        raise RuntimeError('data start date is before 2005 which is not acceptable')
    with open(input_list , 'r') as fl:
        symbols = fl.readlines()
        symbols = [x.strip() for x in symbols]
        if printnames:
            for i , sym in enumerate(symbols):
                print('%d- %s' % (i + 1 , sym))

    datalist = []
    syms = []
    # add fix income data:
    if add_fixincome:
        datalist.append([data_path + 'FIX_20%.csv' , 'FIX_20%'])
    # add symbols data:
    for sym in symbols:
        path = data_path + sym + '.txt'
        datalist.append([path , sym])
        syms.append(sym)

    datas = list()
    for i in range(len(datalist)):
        datapath = datalist[i][0]
        df = pd.read_csv(datapath ,
                         skiprows=1 ,
                         header=None ,
                         parse_dates=True ,
                         dayfirst=True ,
                         index_col=[2])

        if add_fixincome and i == 0:
            close = df[9]
            candle_open = df[9]
            high = df[9]
            low = df[9]
            datafeed = pd.DataFrame({'open': candle_open , 'high': high , 'low': low , 'close': close , 'volume': 0})
        else:
            candle_open = df[4]
            high = df[5]
            low = df[6]
            close = df[7]
            volume = df[8]
            datafeed = pd.DataFrame(
                    {'open': candle_open , 'high': high , 'low': low , 'close': close , 'volume': volume})

        # get a certain slice of data:
        # datafeed = datafeed.loc['2019-02-01':'2019-05-01']

        # fill the blank dates:
        date_index = pd.date_range(start , end)
        datafeed = datafeed.reindex(date_index , method='bfill')
        df_days = pd.to_datetime(datafeed.index.date)
        market_days = pd.bdate_range(start=datafeed.index[0].date() ,
                                     end=datafeed.index[-1].date() ,
                                     weekmask='Sat Sun Mon Tue Wed' ,
                                     freq='C')
        datafeed = datafeed[df_days.isin(market_days)]

        # Pass it to the backtrader datafeed and add it to the cerebro:
        data = bt.feeds.PandasData(dataname=datafeed , name=datalist[i][1] , openinterest=None)
        if not datalist[i][1] in show:
            data.plotinfo.plot = False
        # store data:
        datas.append([data , datalist[i][1]])

    return datas


def loading_bar(stage: int = None , process_length: int = None , bar_len: int = 20 ,
                message: str = 'Downloading Files'):
    # safety:
    if process_length is None:
        raise ValueError('process_length is not determined')
    if stage is None:
        raise ValueError('stage is not determined')
    if stage >= process_length:
        raise ValueError('stage should not be equal or bigger than process_length')

    # calculations:
    n = bar_len
    n_count = 0
    n_count += math.ceil(stage * n / process_length)
    if n_count > n:
        n_count = n
    char = '█' * n_count
    sys.stdout.write('\r' + message + ' ' +
                     char + ''.rjust(n - n_count , '▒') +
                     ' ' + str(int(stage * 100 / process_length)) + '%')
    sys.stdout.flush()
    if stage == process_length - 1:
        time.sleep(0.5)
        sys.stdout.write('\r' + message + ' ' + '█' * bar_len + ' 100%')
        sys.stdout.flush()
        print('\n' + message + ' Completed')


def csvw(file_name: str , data: list , header: list , prefix='' , directory='Opt_Results/'):
    if not os.path.exists(directory):
        os.makedirs(directory)
    df = pd.DataFrame(data , columns=header)
    path = directory + prefix + file_name + '__' + dt.datetime.now().strftime('%y-%m-%d__%H-%M') + '.csv'
    df.to_csv(path , index=False)
    print('Report File Created:' , path)


def all_files_dropbox(path='../Data/all/'):
    files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path , f))]
    names = list()
    for i , f in enumerate(files):
        if '_Share_D.txt' in f:
            names.append(f.replace('_Share_D.txt' , ''))
        elif '_D.txt' in f:
            names.append(f.replace('_D.txt' , ''))

    return names


if __name__ == '__main__':
    data = refresh_all_data()
    # refresh_data(file_name='../Lists/stoch_rsi.txt' , created_list='../Lists/input_data/stoch_rsi.txt')
