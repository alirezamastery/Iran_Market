from __future__ import (absolute_import , division , print_function ,
                        unicode_literals)
import datetime  # For datetime objects
import os.path  # To manage paths
import sys  # To find out the script name (in argv[0])
import time
import numpy as np
import pandas
import datetime as dt
import matplotlib.pyplot as plt
import math as sys_math
import backtrader as bt
import backtrader.indicators as btind
import backtrader.mathsupport as math


# RS Indicator
class RSInd(bt.Indicator):
    lines = ('RS' , 'MA' ,)
    params = (('ma_period' , 34) ,)

    def __init__(self):
        self.lines.RS = self.datas[1].close / self.datas[0].close
        self.lines.MA = btind.MovingAverageSimple(self.lines.RS , period=self.params.ma_period)


class RSInd_100(bt.Indicator):
    lines = ('RS' , 'MA' ,)
    params = (('ma_period' , 34) ,)

    def __init__(self):
        RS_raw = self.datas[1].close / self.datas[0].close
        ratio = self.datas[0].close[1] * 100 / self.datas[1].close[1]
        self.lines.RS = RS_raw * ratio
        self.lines.MA = btind.MovingAverageSimple(self.lines.RS , period=self.params.ma_period)
        # print('in the ind: ' , self.datas[0].close[1] * 100 / self.datas[1].close[1] )
        # self.addminperiod(self.params.period)

    # def __next__(self):
    #     value = self.datas[1].close[0] / self.datas[0].close[0]
    # #     # datasum = bt.math.fsum(self.lines.RS(size=self.params.period))
    #     self.lines.MA[0] = 0.02


# Create a Stratey
class TestStrategy(bt.Strategy):
    params = (
        ('ma_period' , 34) ,
    )

    def log(self , txt , dt=None):
        pass
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[1].datetime.date(0)
        print('%s, %s' % (dt.isoformat() , txt))

    def __init__(self):
        # for i, d in enumerate(self.datas):
        #     print(i,d.open[0],d.high[-1])

        # call RS indicator
        self.rs = RSInd(*self.datas , ma_period=self.params.ma_period)
        RSInd_100(*self.datas , ma_period=self.params.ma_period)

        # # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[1].close

        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None

        # Add a MovingAverageSimple indicator
        # self.sma = bt.indicators.SimpleMovingAverage(
        #     self.datas[0], period=self.params.maperiod)

        # Indicators for the plotting show
        # bt.indicators.ExponentialMovingAverage(self.datas[1], period=25)
        # bt.indicators.StochasticSlow(self.datas[2])
        # bt.indicators.MACDHisto(self.datas[0])
        # rsi = bt.indicators.RSI(self.datas[0])
        # bt.indicators.SmoothedMovingAverage(rsi, period=10)
        # bt.indicators.ATR(self.datas[0], plot=False)

    def notify_order(self , order):
        if order.status in [order.Submitted , order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        # if order.status in [order.Completed]:
        #     if order.isbuy():
        #         self.log(
        #                 'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
        #                 (order.executed.price ,
        #                  order.executed.value ,
        #                  order.executed.comm))
        #
        #         self.buyprice = order.executed.price
        #         self.buycomm = order.executed.comm
        #     else:  # Sell
        #         self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
        #                  (order.executed.price ,
        #                   order.executed.value ,
        #                   order.executed.comm))
        #
        #     self.bar_executed = len(self)

        # elif order.status in [order.Canceled , order.Margin , order.Rejected]:
        #     self.log('Order Canceled/Margin/Rejected')

        self.order = None

    def notify_trade(self , trade):
        if not trade.isclosed:
            return

        # self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' % (trade.pnl , trade.pnlcomm))

    def next(self):
        # Simply log the closing price of the series from the reference
        # self.log('Close, %.2f' % self.dataclose[0])

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        if len(self.data) == self.data.buflen():
            self.order = self.close(data=self.datas[1])
            return

        # Check if we are in the market
        if not self.getposition(data=self.datas[1]):

            # Not yet ... we MIGHT BUY if ...
            if self.rs.lines.RS[0] > self.rs.lines.MA[0]:
                # BUY, BUY, BUY!!! (with all possible default parameters)
                # self.log('BUY CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                qty = sys_math.floor(self.broker.get_cash() * 0.97 / self.datas[1].close[0])
                self.order = self.buy(data=self.datas[1] , size=qty)

        else:

            if self.rs.lines.RS[0] < self.rs.lines.MA[0]:
                # SELL, SELL, SELL!!! (with all possible default parameters)
                # self.log('SELL CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.order = self.close(data=self.datas[1])

    def stop(self):
        self.log('(MA Period %2d) Ending Value %.2f' % (self.params.ma_period , self.broker.getvalue()))
        self.value = round(self.broker.get_value() , 2)
    #     if self.getposition(data=self.datas[1]):
    #         self.order = self.close(data=self.datas[1],coc=True)


if __name__ == '__main__':
    cerebro = bt.Cerebro(optreturn=False)

    # optimize a strategy
    strats = cerebro.optstrategy(TestStrategy , ma_period=range(34 , 340))

    datalist = [
        ('Data/TEPIX_D.txt' , 'TEPIX') ,  # [0] = Data file, [1] = Data name
        ('Data/REMAPNA_Share_D.txt' , 'REMAPNA') ,
        # ('Data/AKHABER_Share_D.txt', 'AKHABER'),
    ]

    # print(datalist[0][0])

    for i in range(len(datalist)):
        datapath = datalist[i][0]
        df = pandas.read_csv(datapath ,
                             skiprows=1 ,
                             header=None ,
                             parse_dates=True ,
                             dayfirst=True ,
                             index_col=[2])
        open = df[4]
        high = df[5]
        low = df[6]
        close = df[7]
        volume = df[8]
        datafeed = pandas.DataFrame({'open': open , 'high': high , 'low': low , 'close': close , 'volume': volume})

        # datafeed = datafeed.tail(600)

        # get a certain slice of data:
        # datafeed = datafeed.loc['2019-02-01':'2019-05-01']

        # fill the blank dates:
        start = '2010-01-01'
        end = '2020-01-01'
        date_index = pandas.date_range(start , end)
        datafeed = datafeed.reindex(date_index , method='bfill')
        df_days = pandas.to_datetime(datafeed.index.date)
        bdays = pandas.bdate_range(start=datafeed.index[0].date() ,
                                   end=datafeed.index[-1].date() ,
                                   weekmask='Sat Sun Mon Tue Wed' ,
                                   freq='C')
        datafeed = datafeed[df_days.isin(bdays)]
        # print(datafeed)

        # Pass it to the backtrader datafeed and add it to the cerebro
        data = bt.feeds.PandasData(dataname=datafeed , name=datalist[i][1] , openinterest=None)
        cerebro.adddata(data)

    # data.plotinfo.plot = False

    startcash = 1000000
    cerebro.broker.setcash(startcash)

    # Add a FixedSize sizer according to the stake
    # cerebro.addsizer(bt.sizers.FixedSize , stake=10)

    cerebro.broker.set_coo(coo=True)
    cerebro.broker.set_coc(coc=True)

    # Set the commission - 0.1% ... divide by 100 to remove the %
    cerebro.broker.setcommission(commission=0.01)

    # print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
    start_time = time.time()
    # opt_runs = cerebro.run(maxcpus=1)
    opt_runs = cerebro.run(stdstats=False)

    end_time = time.time()
    print('\nElapsed time: ' + str(round(end_time - start_time , 2)) + ' seconds')
    # print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Plot the backtest result
    # cerebro.plot(style='candle')

    # Generate results list
    final_results_list = []
    profit = []
    ma_period = []
    for run in opt_runs:
        for strategy in run:
            value = strategy.value
            profit.append(value)
            PnL = round(value - startcash , 2)
            period = strategy.params.ma_period
            ma_period.append(period)
            final_results_list.append([period , PnL])
    #
    # Sort Results List
    by_period = sorted(final_results_list , key=lambda x: x[0])
    by_PnL = sorted(final_results_list , key=lambda x: x[1] , reverse=True)

    # Print results
    # print('Results: Ordered by period:')
    # for result in by_period:
    #     print('Period: {}, PnL: {}'.format(result[0] , result[1]))
    # print('Results: Ordered by Profit:')
    # for result in by_PnL:
    #     print('Period: {}, PnL: {}'.format(result[0] , result[1]))

    # plot optimization result:
    plt.plot(ma_period , profit , label='profit')
    plt.margins(y=0.1)
    plt.xticks(np.arange(min(ma_period) , max(ma_period) + 1 , 10))
    plt.xlabel('period')
    plt.ylabel('result')
    plt.legend(loc='upper left')
    plt.show()
