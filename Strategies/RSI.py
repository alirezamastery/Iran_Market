import symdata as sd
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt


def load_data(input_list='Lists/input_data/pairs.txt' ,
              data_path='Data/' ,
              start='2020-01-01' ,
              end=datetime.today().strftime('%Y-%m-%d') ,
              printnames=False):
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

        candle_open = df[4]
        high = df[5]
        low = df[6]
        close = df[7]
        volume = df[8]
        datafeed = pd.DataFrame({'open': candle_open , 'high': high , 'low': low , 'close': close , 'volume': volume})

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

        # store data:
        datas.append([datafeed , datalist[i][1]])

    return datas


def rsi(data , period=14):
    show = period + 1
    stars = '*' * 50

    print(data[1])
    print(stars)

    close = data[0]['close']
    print('close')
    print(close.tail(show))
    print(stars)

    # Get the difference in price from previous step
    delta = close.diff()
    print('delta')
    print(delta.tail(show))
    print(stars)

    # Make the positive gains (up) and negative gains (down) Series
    up , down = delta.copy() , delta.copy()
    up[up < 0] = 0
    down[down > 0] = 0
    print('up')
    print(up.tail(show))
    print(stars)
    print('down')
    print(down.tail(show))
    print(stars)

    # Calculate the SMA
    roll_up2 = up.rolling(period).mean()
    roll_down2 = down.abs().rolling(period).mean()
    print('roll_up2')
    print(roll_up2.tail(show))
    print(stars)
    print('roll_down2')
    print(roll_down2.tail(show))
    print(stars)

    # Calculate the RSI based on SMA
    RS = roll_up2 / roll_down2
    print('RS')
    print(RS.tail(show))
    print(stars)
    RSI = 100.0 - (100.0 / (1.0 + RS))
    print('RSI with simple moving average')
    print(RSI.tail(show))
    print(stars)

    # Calculate the EWMA
    roll_up1 = up.ewm(span=period).mean()
    roll_down1 = down.abs().ewm(span=period).mean()

    # Calculate the RSI based on EWMA
    RS2 = roll_up1 / roll_down1
    RSI2 = 100.0 - (100.0 / (1.0 + RS2))
    print('RSI with exponential moving average')
    print(RSI2.tail(show))

    # Compare graphically
    plt.figure(figsize=(8 , 6))
    RSI.plot()
    RSI2.plot()
    plt.legend(['RSI via SMA' , 'RSI via EWMA'])
    plt.show()


if __name__ == '__main__':
    datas = load_data()
    rsi(datas[2] , period=14)
