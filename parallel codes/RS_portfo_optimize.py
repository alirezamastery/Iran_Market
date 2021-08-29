from __future__ import (absolute_import , division , print_function , unicode_literals)
import datetime  # For datetime objects
import os.path  # To manage paths
import sys  # To find out the script name (in argv[0])
import time
import datetime as dt
import numpy as np
import pandas as pd
import symdata as sd
import datetime as dt
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import math as sys_math
import backtrader as bt
import backtrader.indicators as btind
import backtrader.mathsupport as math


class csvw():
    def __init__(self , data: list , header: list):
        # create the folder if it is not there
        self.directory = 'Opt_Results/'
        if not os.path.exists(self.directory):
            os.makedirs(self.directory)

        self.df = pd.DataFrame(data , columns=header)

    def writer(self):
        fil_name = self.directory + 'opt_result__' + dt.datetime.now().strftime('%y-%m-%d__%H-%M') + '.csv'
        self.df.to_csv(fil_name , index=False)


def printTradeAnalysis(analyzer):
    '''
    Function to print the Technical Analysis results in a nice format.
    '''
    # Get the results we are interested in
    total_open = analyzer.total.open
    total_closed = analyzer.total.closed
    total_won = analyzer.won.total
    total_lost = analyzer.lost.total
    win_streak = analyzer.streak.won.longest
    lose_streak = analyzer.streak.lost.longest
    pnl_net = round(analyzer.pnl.net.total , 2)
    strike_rate = round((total_won / total_closed) * 100 , 2)
    # Designate the rows
    h1 = ['Total Open' , 'Total Closed' , 'Total Won' , 'Total Lost']
    h2 = ['Strike Rate' , 'Win Streak' , 'Losing Streak' , 'PnL Net']
    r1 = [total_open , total_closed , total_won , total_lost]
    r2 = [strike_rate , win_streak , lose_streak , pnl_net]
    # Check which set of headers is the longest.
    if len(h1) > len(h2):
        header_length = len(h1)
    else:
        header_length = len(h2)
    # Print the rows
    print_list = [h1 , r1 , h2 , r2]
    row_format = "{:<15}" * (header_length + 1)
    print("Trade Analysis Results:")
    for row in print_list:
        print(row_format.format('' , *row))


def printDrawDownAnalysis(analyzer):
    '''
    Function to print the Technical Analysis results in a nice format.
    '''
    # Get the results we are interested in
    drawdown = round(analyzer.drawdown , 2)
    moneydown = round(analyzer.moneydown , 2)
    length = analyzer.len
    max_dd = round(analyzer.max.drawdown , 2)
    max_md = round(analyzer.max.moneydown , 2)
    max_len = analyzer.max.len

    # Designate the rows
    h1 = ['Drawdown' , 'Moneydown' , 'Length']
    h2 = ['Max drawdown' , 'Max moneydown' , 'Max len']
    r1 = [drawdown , moneydown , length]
    r2 = [max_dd , max_md , max_len]
    # Check which set of headers is the longest.
    if len(h1) > len(h2):
        header_length = len(h1)
    else:
        header_length = len(h2)
    # Print the rows
    print_list = [h1 , r1 , h2 , r2]
    row_format = "{:<15}" * (header_length + 1)
    print("Drawdown Analysis Results:")
    for row in print_list:
        print(row_format.format('' , *row))


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
    params = (('risk' , 0.18) ,)

    def __init__(self):
        if self.p.risk > 1 or self.p.risk < 0:
            raise ValueError('The risk parameter is a percentage which must be between 0 and 1')

    def _getsizing(self , comminfo , cash , data , isbuy):
        if isbuy == True:
            print('cash:' , cash)
            size = sys_math.floor((cash * self.p.risk) / data[0])

        else:
            size = sys_math.floor((cash * self.p.risk) / data[0]) * -1
        return size


# Create a Stratey
class TestStrategy(bt.Strategy):
    params = (
        ('ma_period' , 89) ,
        ('portfo' , 5) ,
        ('RS_min' , 80) ,
        ('signal_threshold' , 0.05)
    )

    def log(self , txt , dt=None):
        pass
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[1].datetime.date(0)
        print('%s, %s' % (dt.isoformat() , txt))

    def __init__(self):
        # for i, d in enumerate(self.datas):
        #     print(i,d.open[0],d.high[-1])

        self.fs = [0] * self.params.portfo
        self.position_flag = []
        self.sym_count = 0
        self.RS_min = 100
        self.s_th = self.params.signal_threshold + 1
        self.buysig = False
        # self.o = dict()  # orders per data (main, stop, limit, manual-close)
        self.holding = dict()  # holding periods per data

        self.symbols = self.getdatanames()
        self.symbol_key = dict()
        # call RS indicator and data names
        self.inds = dict()
        for i , d in enumerate(self.datas):
            if i == 0:
                self.symbol_key[d] = self.symbols[i]
                self.position_flag.append(False)
            else:
                self.symbol_key[d] = self.symbols[i]
                self.inds[d] = dict()
                plotname = self.symbol_key[self.datas[i]] + ' / ' + self.symbol_key[self.datas[0]]
                self.inds[d]['RS'] = RSInd_100(self.datas[i] , self.datas[0] ,
                                               ma_period=self.params.ma_period ,
                                               plotname=plotname ,
                                               plotyticks=[50 , 100 , 150] ,
                                               plothlines=[50 , 100 , 150] ,
                                               )
                self.position_flag.append(False)
                # self.inds[d]['RS'].plotinfo.plotmaster = self.inds[self.datas[1]]['RS']
                # print(self.inds[d])

            # if i > 0:  # Check we are not on the first loop of data feed:
            #      d.plotinfo.plotmaster = self.datas[1]

        # print(self.inds)

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

        # calculate volume for each symbol:
        sizes = -1
        if self.params.portfo > self.sym_count:
            sizes = sys_math.floor(1 * self.broker.get_cash() / (self.params.portfo - self.sym_count))
        comm = 0.01

        # open positions:
        while self.sym_count < self.params.portfo:

            self.RS_min = self.params.RS_min

            for i , d in enumerate(self.datas):
                if i == 0:
                    pass
                elif not self.position_flag[i]:
                    if self.inds[d]['RS'].RS[0] > (self.inds[d]['RS'].MA[0]) * self.s_th and \
                            self.inds[d]['RS'].RS[0] > self.RS_min:
                        self.RS_min = self.inds[d]['RS'].RS[0]
                        self.fs[self.sym_count] = i

            if self.RS_min <= self.params.RS_min:
                break

            self.position_flag[self.fs[self.sym_count]] = True

            com_adj_price = self.datas[self.fs[self.sym_count]].close[0] * (1 + (comm * 2))
            comm_adj_size = sizes / com_adj_price
            size = sys_math.floor(comm_adj_size)

            # print(bt.CommissionInfo.get_margin(self.datas[self.final_symbols[self.sym_count]].close[0]))
            # print(self.order)
            self.order = self.buy(data=self.datas[self.fs[self.sym_count]] , size=size)
            # self.log('BUY CREATED: %s , %.2f' % (self.symbols[self.fs[self.sym_count]] ,
            #                                      self.datas[self.fs[self.sym_count]].close[0]))
            # print('size:' , size)
            # print('cash:' , self.broker.get_cash())
            # print('volume:' , size * self.datas[self.fs[self.sym_count]].close[0])

            self.sym_count += 1

        # close signals:
        for sym in range(5):
            if self.fs[sym] > 0 and self.inds[self.datas[self.fs[sym]]]['RS'].RS[0] < \
                    self.inds[self.datas[self.fs[sym]]]['RS'].MA[0]:
                # self.log('SELL CREATED: %s , %.2f' % (self.symbols[self.fs[sym]] , self.datas[
                #     self.fs[sym]].close[0]))
                self.order = self.close(data=self.datas[self.fs[sym]])
                self.position_flag[self.fs[sym]] = False
                self.fs[sym] = -1
                self.sym_count -= 1

        self.fs.sort(reverse=True)

    def notify_order(self , order):
        if order.status in [order.Submitted , order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return
        #
        #     # Check if an order has been completed
        #     # Attention: broker could reject order if not enough cash
        #     if order.status in [order.Completed]:
        #         if order.isbuy():
        #             self.log(
        #                     'BUY EXECUTED: %s , Price: %.2f, Cost: %.2f, Comm %.2f' %
        #                     (order.data._name ,
        #                      order.executed.price ,
        #                      order.executed.value ,
        #                      order.executed.comm))
        #             self.buyprice = order.executed.price
        #             self.buycomm = order.executed.comm
        #         else:  # Sell
        #             self.log('SELL EXECUTED: %s , Price: %.2f, Cost: %.2f, Comm %.2f' %
        #                      (order.data._name ,
        #                       order.executed.price ,
        #                       order.executed.value ,
        #                       order.executed.comm))
        #
        #         self.bar_executed = len(self)
        #
        #     elif order.status == order.Canceled:
        #         self.log('Order Problem: Canceled , Symbol: %s' % (order.data._name))
        #     elif order.status == order.Margin:
        #         self.log('Order Problem: Margin , Symbol: %s' % (order.data._name))
        #         print('cash:' , self.broker.get_cash())
        #         # print(self.order)
        #     elif order.status == order.Rejected:
        #         self.log('Order Problem: Rejected , Symbol: %s' % (order.data._name))
        #
        self.order = None

    #
    # def notify_trade(self , trade):
    #     if not trade.isclosed:
    #         return
    #
    #     self.log('OPERATION PROFIT:  GROSS: {:<10,.0f} | NET: {:<10,.0f}'.format(trade.pnl ,
    #                                                                              trade.pnlcomm).replace(',' , '/'))

    def stop(self):
        self.log('(MA Period {}) (RS_min {}) Ending Value {:,.0f}'.format(self.params.ma_period ,
                                                                          self.params.RS_min ,
                                                                          self.broker.getvalue()).replace(',' , '/'))
        self.value = round(self.broker.get_value() , 2)

        # self.exposure = self.in_position / self.data.buflen() * 100
        # print('Exposure:' , round(self.exposure , 2) , '%')


if __name__ == '__main__':

    cerebro = bt.Cerebro(optreturn=False ,
                         cheat_on_open=True ,
                         maxcpus=None
                         )

    # Add sizer:
    # cerebro.addsizer(maxRiskSizer)

    # load data:
    sd.add_cerebro_data(cerebro , start='2010-01-01')

    # Add a strategy:
    strats = cerebro.optstrategy(TestStrategy ,
                                 ma_period=range(50 , 52) ,
                                 RS_min=range(80 , 82))

    # initial deposit:
    startcash = 10000000
    cerebro.broker.setcash(startcash)
    cerebro.broker.set_checksubmit(checksubmit=False)
    # cerebro.broker.set_coo(coo=True)
    cerebro.broker.set_coc(coc=True)

    # Set the commission - 0.1% ... divide by 100 to remove the %
    cerebro.broker.setcommission(commission=0.01)

    # Add the analyzers we are interested in
    # cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="ta")
    # cerebro.addanalyzer(bt.analyzers.DrawDown, _name="dd")
    # cerebro.addanalyzer(bt.analyzers.AnnualReturn, _name="ar")

    # Run over everything
    start_time = time.time()

    # opt_runs = cerebro.run(maxcpus=1)
    opt_runs = cerebro.run(stdstats=False)

    end_time = time.time()
    print('\nElapsed time: ' + str(round(end_time - start_time , 2)) + ' seconds')

    # print the analyzers
    # printTradeAnalysis(firstStrat.analyzers.ta.get_analysis())
    # printDrawDownAnalysis(firstStrat.analyzers.dd.get_analysis())
    # print(firstStrat.analyzers.ar.get_analysis())
    # print(firstStrat.analyzers.dd.get_analysis())

    # Generate results list
    final_results_list = []
    Balance = []
    Profit = []
    ma_period = []
    RS_min = []
    result = []
    for run in opt_runs:
        for strategy in run:
            value = strategy.value
            Balance.append(value)
            PnL = round(value - startcash , 2)
            Profit.append(PnL)

            period = strategy.params.ma_period
            ma_period.append(period)

            rs_min = strategy.params.RS_min
            RS_min.append(rs_min)

            final_results_list.append([period , PnL])
            result.append([period , rs_min , value])

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
    print(result)
    print(ma_period)
    print(RS_min)
    print(Balance)

    res_file = csvw(result , ['MA_period' , 'RS_level' , 'Balance'])

    fig = plt.figure()
    fig.tight_layout()
    ax = plt.axes(projection='3d')
    ax.tick_params(axis='z' , which='major' , pad=12)
    surf = ax.plot_trisurf(ma_period , RS_min , Balance , cmap='RdYlGn')
    ax.set_xlabel('MA Period' , color='Blue' , labelpad=10 , fontsize=18)
    ax.set_ylabel('RS Level' , color='Blue' , labelpad=10 , fontsize=18)
    ax.set_zlabel('Final Balance' , color='Blue' , labelpad=20 , fontsize=18)
    fig.colorbar(surf , shrink=0.5 , aspect=5)
    plt.show()
