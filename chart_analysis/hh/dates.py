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
    df = df.loc[start:end]
    candle_open = df[4]
    high = df[5]
    low = df[6]
    close = list(df[7])
    volume = df[8]
    datafeed = pd.DataFrame({'open': candle_open , 'high': high , 'low': low , 'close': close , 'volume': volume})

    # converting the god damn pandas Timestamp to python datetime:
    date = df.index
    date = [str(d) for d in date]
    date = [re.search(r'[^\s]+' , d)[0] for d in date]
    date = [datetime.datetime.strptime(d , '%Y-%m-%d') for d in date]

    data = dict()
    for col in datafeed.columns:
        data[col] = datafeed[col].tolist()

    return date , close , df


def load_hh_data(name , path , start , end):
    only_files = [f for f in os.listdir(path) if isfile(join(path , f))]
    file_name = ''
    for f in only_files:
        if name in f:
            file_name = f
            break

    df = pd.read_csv(path + file_name , index_col='DATE_GREGORIAN')
    df = df.iloc[::-1]  # reverse index order
    # df = df.loc[start:end]
    date = df.index
    date = [datetime.datetime.strptime(d , '%Y-%m-%d') for d in date]

    data = dict()
    for col in df.columns:
        data[col] = df[col].tolist()

    return date , data , df


def intersect(list1: list , list2: list):
    result = list()
    if len(list1) < len(list2):
        for item in list1:
            if item in list2:
                result.append(item)
    else:
        for item in list2:
            if item in list1:
                result.append(item)

    return result


def difference(list1: list , list2: list):
    result = list()
    if len(list1) > len(list2):
        for item in list1:
            if item not in list2:
                result.append(item)
    else:
        for item in list2:
            if item not in list1:
                result.append(item)

    return result


pd.set_option('display.max_columns' , None)
if __name__ == '__main__':
    START = '2000-01-05'
    END = '2020-09-16'
    folder_hh = '../../Data/TSETMC_DATA/HH_History/'
    folder_price = '../../Data/all/'

    # files = ['FEMELI']
    files = [f for f in os.listdir(folder_hh) if isfile(join(folder_hh , f))]
    for file in files:
        symbol = re.search(r'^[^_]+(?=_)' , file)[0]
        if symbol in ['ENERGY3' , 'SYSTEM' , 'BOURSE']:
            continue
        print(symbol)
        # Load HH data:
        hh_date , hh_data , hh_df = load_hh_data(name=symbol , path=folder_hh , start=START , end=END)
        # Load Price data:
        price_date , price_data , price_df = load_price_data(name=symbol , data_path=folder_price , start=START ,
                                                             end=END)
        # dates = difference(hh_date , price_date)
        # print(dates)
        price_df.drop(price_df.columns[[2 , 9 , 10]] , axis=1 , inplace=True)

        price_df.columns = ['TICKER' , 'PERIOD' , 'OPEN' , 'HIGH' , 'LOW' , 'CLOSE' , 'VOLUME' , 'OPENINT']
        # print(price_df)
        new_df = pd.merge(price_df , hh_df , left_index=True , right_index=True , how='inner')
        new_df.to_csv('../../Data/Combined/' + symbol + '.csv' , index_label='DATE_GREGORIAN')
