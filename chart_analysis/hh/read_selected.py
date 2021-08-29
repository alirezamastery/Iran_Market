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
import arabic_reshaper as ar
from bidi.algorithm import get_display


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


def moving_average(a , period=8):
    ret = np.cumsum(a , dtype=float)
    ret[period:] = ret[period:] - ret[:-period]
    result = list(ret[period - 1:] / period)
    for i in range(period - 1):
        result.insert(0 , 0)
    return result


def load_data(name , data_path , start='2020-07-23' , end='2020-09-18'):
    path = data_path + name + '.csv'
    df = pd.read_csv(path , index_col='DATE_GREGORIAN')
    df = df.loc[start:end]

    # converting the god damn pandas Timestamp to python datetime:
    date = df.index
    date = [datetime.datetime.strptime(d , '%Y-%m-%d') for d in date]

    # solution for onl date format:
    # dates = [datetime.datetime.strptime(d , "%Y-%m-%d %H:%M:%S").date() for d in cd]

    data = dict()
    for col in df.columns:
        data[col] = df[col].tolist()

    return date , data


if __name__ == '__main__':
    START = '2019-09-16'
    END = '2020-09-16'
    folder = '../../Data/Combined/'

    movav_period = [14]
    width = 18.9
    height = 10.6

    files = ['FEMELI' , 'REMAPNA' , 'VAGHADIR' , 'FARS' , 'SHETRAN']
    # files = [f for f in os.listdir(folder_hh) if isfile(join(folder_hh , f))]
    for file in files:
        # symbol = re.search(r'^[^.]+(?=.)' , file)[0]
        symbol = file
        if symbol in ['ENERGY3' , 'SYSTEM' , 'BOURSE']:
            continue

        # Load data:
        dates , data = load_data(name=symbol , data_path=folder , start=START , end=END)
        if len(dates) == 0 or len(dates) <= max(movav_period):
            print(f'{symbol}: less days than moving average period')
            continue

        # total volume:
        total_vol = [sum(x) for x in zip(data['VOL_BUY_IND'] , data['VOL_BUY_CORP'])]

        # Moving Average:
        movavs = dict()
        for period in movav_period:
            movavs[period] = dict()
            for key in data.keys():
                if key not in ['DATE_JALALI' , 'DATE_GREGORIAN' , 'TICKER' , 'PERIOD']:
                    movavs[period][key] = moving_average(data[key] , period=period)

        # formula:
        formula_buy = list()
        for db , dv in zip(data['BUYERS_IND'] , data['VOL_BUY_IND']):
            try:
                formula_buy.append(dv // db)
            except:
                formula_buy.append(0)
        formula_sell = list()
        for db , dv in zip(data['SELLERS_IND'] , data['VOL_SELL_IND']):
            try:
                formula_sell.append(dv // db)
            except:
                formula_sell.append(0)

        intel_money_buy = list()
        for db , dv , dm in zip(data['BUYERS_IND'] , data['VOL_BUY_IND'], movavs[movav_period[0]]['VOL_BUY_IND']):
            if dv > dm:
                intel_money_buy.append(dv//db)
            else:
                intel_money_buy.append(0)


        # Plot:
        plots = 1
        subplots = 4
        # to prevent a stupid warning:
        register_matplotlib_converters()

        figs = dict()
        axs = dict()
        for i in range(plots):
            figs[i] , axs[i] = plt.subplots(subplots , 1 ,
                                            # constrained_layout=True ,
                                            sharex=True ,
                                            gridspec_kw={'height_ratios': [2 , 1 , 1 , 1]})
            figs[i].set_size_inches(width , height)

        formatter = mdates.DateFormatter('%Y-%m-%d')
        locator = mdates.MonthLocator()
        plt.subplots_adjust(left=0.01 , bottom=0.07 , right=0.93 , top=0.99 , wspace=0 , hspace=0)
        for i in range(plots):
            for ax in axs[i]:
                # Plot settings:
                ax.xaxis.set_major_formatter(formatter)
                ax.xaxis.set_major_locator(locator)
                ax.grid(True)
                ax.yaxis.tick_right()
                # ax.set_facecolor('#BEBEBE')
                # to prevent scientific notion for y axis numbers:
                ax.get_yaxis().set_major_formatter(ticker.FuncFormatter(lambda x , p: format(int(x) , ',')))

            # plotting price and volume:
            axs[i][0].semilogy(dates , data['CLOSE'] , label=f'{symbol} | close price')
            axs[i][1].bar(dates , total_vol , label=f'Volume' , color='gray')
            axs[i][1].plot(dates , movavs[14]['VOLUME'] , label=f'Moving Average | period: {movav_period[0]}' ,
                          color='blue')

        # buy
        # axs[0][1].plot(hh_date , data['CORP_TO_IND'] , label='CORP_TO_IND' , color='#00a300')
        axs[0][2].bar(dates , data['VOL_BUY_IND'] , label=f'VOL_BUY_IND' , color='green')
        axs[0][2].bar(dates , data['VOL_BUY_CORP'] , label=f'VOL_BUY_CORP' , color='red')
        for i , key in enumerate(list(movavs.keys())):
            if i == 0:
                color = 'black'
            elif i == 1:
                color = 'blue'
            elif i == 2:
                color = 'green'
            axs[0][2].plot(dates , movavs[key]['VOL_BUY_IND'] , label=f'Moving Average | period: {movav_period[i]}' ,
                           color=color)

        axs[0][3].bar(dates , intel_money_buy  , label=f'intel_money_buy' , color='green')
        # axs[0][3].plot(dates , formula_sell , '-' , label=f'formula_sell' , color='red')

        plt.xticks(rotation=20)
        for i in range(plots):
            for j , ax in enumerate(axs[i]):
                ax.legend(loc='upper left')

        # for key in figs.keys():
        #     figs[key].savefig('plots/change/' + symbol + '__' + str(key) + '.png' , dpi=100)

        # plt.close('all')
    plt.show()
