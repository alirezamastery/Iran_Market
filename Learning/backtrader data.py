from __future__ import (absolute_import , division , print_function ,
                        unicode_literals)

import argparse

import backtrader as bt
import backtrader.feeds as btfeeds
import datetime as dt
import pandas

pandas.set_option('display.max_columns' , 15)
pandas.set_option('display.width' , 400)

start = '2019-01-01'
end = dt.datetime.today()
startcash = 1000000


class firstStrategy(bt.Strategy):

    def __init__(self):
        self.rsi = bt.indicators.Ichimoku()
        self.macd = bt.indicators.RSI()

    # def next(self):
    #     if not self.position:
    #         if self.rsi > 70:
    #             self.buy(size=100)


def runstrat():
    args = parse_args()

    # Create a cerebro entity
    cerebro = bt.Cerebro(stdstats=False)
    cerebro.broker.setcash(startcash)
    # Add a strategy
    cerebro.addstrategy(firstStrategy)

    # Get a pandas dataframe
    datapath = ('Data\olagh.txt')

    df = pandas.read_csv(datapath ,
                         skiprows=1 ,
                         header=None ,
                         parse_dates=True ,
                         index_col=[2])

    if not args.noprint:
        print('--------------------------------------------------')
        print(df.head())
        print('--------------------------------------------------')

    open = df[4]
    high = df[5]
    low = df[6]
    close = df[7]
    volume = df[8]
    datafeed = pandas.DataFrame({'open': open , 'high': high , 'low': low , 'close': close , 'volume': volume})
    datafeed = datafeed.tail(300)
    # date_index = pandas.date_range(start , end)
    # datafeed = datafeed.reindex(date_index , method='bfill')
    print(datafeed)

    # Pass it to the backtrader datafeed and add it to the cerebro
    data = bt.feeds.PandasData(dataname=datafeed , openinterest=None)

    cerebro.adddata(data)

    # Run over everything
    cerebro.run()

    # Get final portfolio Value
    portvalue = cerebro.broker.getvalue()
    pnl = portvalue - startcash

    # Print out the final result
    print('Final Portfolio Value: ${}'.format(portvalue))
    print('P/L: ${}'.format(pnl))

    # Plot the result
    cerebro.plot(style='candle')


def parse_args():
    parser = argparse.ArgumentParser(
            description='Pandas test script')

    parser.add_argument('--noheaders' , action='store_true' , default=False ,
                        required=False ,
                        help='Do not use header rows')

    parser.add_argument('--noprint' , action='store_true' , default=False ,
                        help='Print the dataframe')

    return parser.parse_args()


if __name__ == '__main__':
    runstrat()
