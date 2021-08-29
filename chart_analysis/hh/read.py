import pandas as pd
import numpy as np
import datetime
import os
from os.path import isfile , join
import matplotlib.ticker as ticker
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pandas.plotting import register_matplotlib_converters
import re


def moving_average(a , period=8):
    ret = np.cumsum(a , dtype=float)
    ret[period:] = ret[period:] - ret[:-period]
    result = list(ret[period - 1:] / period)
    for i in range(period - 1):
        result.insert(0 , None)
    return result


def load_price_data(name , data_path , start='2020-07-23' , end='2020-09-18'):
    file_name = ''
    only_files = [f for f in os.listdir(data_path) if isfile(join(data_path , f))]
    for f in only_files:
        if name in f:
            file_name = f
            break

    path = data_path + file_name
    df = pd.read_csv(path ,
                     skiprows=1 ,
                     header=None ,
                     parse_dates=True ,
                     dayfirst=True ,
                     index_col=[2])
    candle_open = df[4]
    high = df[5]
    low = df[6]
    close = df[7]
    volume = df[8]
    datafeed = pd.DataFrame({'open': candle_open , 'high': high , 'low': low , 'close': close , 'volume': volume})

    # fill the blank dates:
    date_index = pd.date_range(start , end)
    datafeed = datafeed.reindex(date_index , method='bfill')
    df_days = pd.to_datetime(datafeed.index.date)
    market_days = pd.bdate_range(start=datafeed.index[0].date() ,
                                 end=datafeed.index[-1].date() ,
                                 weekmask='Sat Sun Mon Tue Wed' ,
                                 freq='C')
    datafeed = datafeed[df_days.isin(market_days)]

    # converting the god damn pandas Timestamp to python datetime:
    date = datafeed.index
    date = [str(d) for d in date]
    date = [re.search(r'[^\s]+' , d)[0] for d in date]
    date = [datetime.datetime.strptime(d , '%Y-%m-%d') for d in date]

    data = dict()
    for col in datafeed.columns:
        data[col] = datafeed[col].tolist()

    return date , data


def load_hh_data(name , path , start , end):
    only_files = [f for f in os.listdir(path) if isfile(join(path , f))]
    file_name = ''
    for f in only_files:
        if name in f:
            file_name = f
            break

    df = pd.read_csv(path + file_name , index_col='DATE_GREGORIAN')
    df = df.iloc[::-1]  # reverse index order
    df = df.loc[START:END]
    date = df.index
    date = [datetime.datetime.strptime(d , '%Y-%m-%d') for d in date]

    data = dict()
    for col in df.columns:
        data[col] = df[col].tolist()

    return date , data


# HH data keys:
# DATE_JALALI
# BUYERS_IND
# BUYERS_CORP
# SELLERS_IND
# SELLERS_CORP
# VOL_BUY_IND
# VOL_BUY_IND_%
# VOL_BUY_CORP
# VOL_BUY_CORP_%
# VOL_SELL_IND
# VOL_SELL_IND_%
# VOL_SELL_CORP
# VOL_SELL_CORP_%
# VALUE_BUY_IND
# VALUE_BUY_CORP
# VALUE_SELL_IND
# VALUE_SELL_CORP
# AVRG_PRICE_BUY_IND
# AVRG_PRICE_BUY_CORP
# AVRG_PRICE_SELL_IND
# AVRG_PRICE_SELL_CORP
# CORP_TO_IND

if __name__ == '__main__':
    START = '2019-12-2'
    END = '2020-09-18'
    folder_hh = '../../Data/TSETMC_DATA/HH_History/'
    folder_price = '../../Data/all/'
    movav_period = 21

    symbol = 'FEMELI'

    # Load HH data:
    hh_date , hh_data = load_hh_data(name=symbol , path=folder_hh , start=START , end=END)
    # Load Price data:
    price_date , price_data = load_price_data(name=symbol , data_path=folder_price , start=START , end=END)

    # Moving Average:
    movavs = dict()
    for key in hh_data.keys():
        if key not in ['DATE_JALALI' , 'DATE_GREGORIAN']:
            movavs[key] = moving_average(hh_data[key] , period=movav_period)

    # Plot:
    plots = 2
    # to prevent a stupid warning:
    register_matplotlib_converters()

    figs = dict()
    axs = dict()
    for i in range(plots):
        figs[i] , axs[i] = plt.subplots(3 , 1 , constrained_layout=True)
        # figs[i].set_size_inches(18.9 , 10.6)

    formatter = mdates.DateFormatter('%Y-%m-%d')
    locator = mdates.MonthLocator()
    for i in range(plots):
        for ax in axs[i]:
            # Plot settings:
            ax.xaxis.set_major_formatter(formatter)
            ax.xaxis.set_major_locator(locator)
            ax.grid(True)
            # to prevent scientific notion for y axis numbers:
            ax.get_yaxis().set_major_formatter(ticker.FuncFormatter(lambda x , p: format(int(x) , ',')))

        # plotting price:
        axs[i][0].plot(price_date , price_data['close'] , label='close price')

    # PLOTTING:
    # buy
    axs[0][1].plot(hh_date , hh_data['VOL_BUY_IND'] , label='VOL_BUY_IND' , color='#00a300')
    axs[0][1].plot(hh_date , movavs['VOL_BUY_IND'] , label=f'moving average | period:{movav_period}' , color='#603cba')

    axs[0][2].plot(hh_date , hh_data['VOL_BUY_CORP'] , label='VOL_BUY_CORP' , color='#00a300')
    axs[0][2].plot(hh_date , movavs['VOL_BUY_CORP'] , label=f'moving average | period:{movav_period}' , color='#603cba')

    # sell
    axs[1][1].plot(hh_date , hh_data['VOL_SELL_IND'] , label='VOL_SELL_IND' , color='red')
    axs[1][1].plot(hh_date , movavs['VOL_SELL_IND'] , label='VOL_BUY_CORP' , color='black')

    axs[1][2].plot(hh_date , hh_data['VOL_SELL_CORP'] , label='VOL_SELL_CORP' , color='red')
    axs[1][2].plot(hh_date , movavs['VOL_SELL_CORP'] , label=f'moving average | period:{movav_period}' , color='black')
    # ax.plot(date , movav_buy)

    # plt.xticks(rotation=30)
    for i in range(plots):
        for ax in axs[i]:
            ax.legend(loc='upper left')

    for key in figs.keys():
        figs[key].savefig(symbol + '__' + str(key) + '.png' , dpi=100)
    plt.show()
