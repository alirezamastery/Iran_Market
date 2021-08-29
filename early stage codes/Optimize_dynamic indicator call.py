from __future__ import (absolute_import , division , print_function ,
                        unicode_literals)
import os.path  # To manage paths
import sys  # To find out the script name (in argv[0)]
import time
import numpy as np
import pandas
import symdata as sd
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
        # datas[1] in TEPIX_D and datas[0] is the symbol
        RS_raw = self.datas[0].close / self.datas[1].close
        ratio = self.datas[1].close[1] * 100 / self.datas[0].close[1]
        self.lines.RS = RS_raw * ratio
        self.lines.MA = btind.MovingAverageSimple(self.lines.RS , period=self.params.ma_period)


class maxRiskSizer(bt.Sizer):
    params = (('risk' , 0.9) ,)

    def __init__(self):
        if self.p.risk > 1 or self.p.risk < 0:
            raise ValueError('The risk parameter is a percentage which must be between 0 and 1')

    def _getsizing(self , comminfo , cash , data , isbuy):
        if isbuy == True:
            size = sys_math.floor((cash * self.p.risk) / data[0])
            # print('size: %s' % size)
            # print('margin: %s' % cash)

        else:
            size = sys_math.floor((cash * self.p.risk) / data[0]) * -1
        return size


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
        self.final_symbol = -1
        self.RS_min = 100
        self.buysig = False
        # self.o = dict()  # orders per data (main, stop, limit, manual-close)
        self.holding = dict()  # holding periods per data

        # call RS indicator
        self.inds = dict()
        for i , d in enumerate(self.datas):
            if i == 0:
                pass
            else:
                self.inds[d] = dict()
                self.inds[d]['RS'] = RSInd_100(self.datas[i] , self.datas[0] ,
                                               ma_period=self.params.ma_period ,
                                               plotyticks=[50 , 100 , 150] ,
                                               plothlines=[50 , 100 , 150] ,
                                               )
                # self.inds[d]['RS'].plotinfo.plotmaster = self.inds[self.datas[1]]['RS']
                # print(self.inds[d])

            # if i > 0:  # Check we are not on the first loop of data feed:
            #      d.plotinfo.plotmaster = self.datas[1]

        # print(self.inds)

        # # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[1].close

        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None
        self.in_position = 0
        self.exposure = -1

    def next_open(self):
        # Simply log the closing price of the series from the reference
        # self.log('Close, %.2f' % self.dataclose[0])

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        if len(self.data) == self.data.buflen():
            for i , d in enumerate(self.datas):
                self.order = self.close(data=self.datas[i])
            return

        if self.final_symbol > 0 and self.getposition(data=self.datas[self.final_symbol]).size:

            self.in_position += 1
            if self.inds[self.datas[self.final_symbol]]['RS'].RS[0] < self.inds[self.datas[
                self.final_symbol]]['RS'].MA[0]:
                self.buysig = False
                # SELL, SELL, SELL!!! (with all possible default parameters)
                # self.log('SELL CREATE: %s , %.2f' % (self.symbols[self.final_symbol] , self.datas[
                #     self.final_symbol].close[0]))

                # Keep track of the created order to avoid a 2nd order
                self.order = self.close(data=self.datas[self.final_symbol])


        else:

            self.RS_min = 10
            for i , d in enumerate(self.datas):
                if i == 0:
                    pass
                else:
                    # dt , dn = self.datetime.date() , d._name
                    pos = self.getposition(d).size
                    # print('{} {} Position {}'.format(dt , dn , pos))

                    if not pos:
                        if self.inds[d]['RS'].RS[0] > self.inds[d]['RS'].MA[0] and \
                                self.inds[d]['RS'].RS[0] > self.RS_min:
                            self.buysig = True
                            self.RS_min = self.inds[d]['RS'].RS[0]
                            self.final_symbol = i

            if self.final_symbol > 0 and self.buysig:
                # BUY, BUY, BUY!!! (with all possible default parameters)
                # self.log('BUY CREATE: %s, %.2f' %
                #          (self.symbols[self.final_symbol] , self.datas[self.final_symbol].close[0]))

                # Keep track of the created order to avoid a 2nd order
                self.order = self.buy(data=self.datas[self.final_symbol])

    def notify_order(self , order):
        if order.status in [order.Submitted , order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                        'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                        (order.executed.price ,
                         order.executed.value ,
                         order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price ,
                          order.executed.value ,
                          order.executed.comm))

            self.bar_executed = len(self)

        elif order.status == order.Canceled:
            self.log('Order Problem: Canceled')
        elif order.status == order.Margin:
            self.log('Order Problem: Margin')
            print(self.order)
        elif order.status == order.Rejected:
            self.log('Order Problem: Rejected')

        self.order = None

    def notify_trade(self , trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' % (trade.pnl , trade.pnlcomm))

    def stop(self):

        self.log('(MA Period %2d) Ending Value %.2f' % (self.params.ma_period , self.broker.getvalue()))

        self.exposure = self.in_position / self.data.buflen() * 100
        print('Exposure:' , round(self.exposure , 2) , '%')

        self.value = round(self.broker.get_value() , 2)


if __name__ == '__main__':
    cerebro = bt.Cerebro(optreturn=False , cheat_on_open=True)

    # Add sizer:
    cerebro.addsizer(maxRiskSizer)

    # load data
    sd.add_cerebro_data(cerebro , start='2010-01-01')

    # optimize a strategy
    strats = cerebro.optstrategy(TestStrategy , ma_period=range(34 , 340))

    startcash = 1000000
    cerebro.broker.setcash(startcash)

    # Add a FixedSize sizer according to the stake
    # cerebro.addsizer(bt.sizers.FixedSize , stake=10)

    cerebro.broker.set_coo(coo=True)
    cerebro.broker.set_coc(coc=True)

    # Set the commission - 0.1% ... divide by 100 to remove the %
    cerebro.broker.setcommission(commission=0.01)

    start_time = time.time()

    # opt_runs = cerebro.run(maxcpus=1)
    opt_runs = cerebro.run(stdstats=False)

    end_time = time.time()
    print('\nElapsed time: ' + str(round(end_time - start_time , 2)) + ' seconds')


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
    plt.scatter(ma_period , profit , label='profit')
    plt.margins(y=0.1)
    plt.xticks(np.arange(min(ma_period) , max(ma_period) + 1 , 10))
    plt.xlabel('period')
    plt.ylabel('result')
    plt.legend(loc='upper left')
    plt.show()
