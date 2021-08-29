from __future__ import (absolute_import , division , print_function , unicode_literals)
import datetime  # For datetime objects
import os
import sys  # To find out the script name (in argv[0])
import numpy as np
import statistics
import pandas
import datetime as dt
import time
import symdata as sd
import math as sys_math
import backtrader as bt
import backtrader.indicators as btind
import backtrader.mathsupport as math
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import our_indicators as oind


def find_in_list_of_lists(mylist , char):
    for sub_list in mylist:
        if char in sub_list:
            return mylist.index(sub_list)
    raise ValueError("'{char}' is not in list".format(char=char))


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
    pnl_net = int(analyzer.pnl.net.total)
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
    # row_format = "{:<15}" * (header_length + 1)
    print("Trade Analysis Results:")
    for i , row in enumerate(print_list):
        if i % 2 == 0:
            row_format = "{:<15}" * (header_length + 1)
            print(row_format.format('' , *row))
        else:
            row_format = "{:<15,}" * header_length
            print(' ' * 15 + row_format.format(*row).replace(',' , '/'))


def printDrawDownAnalysis(analyzer):
    '''
    Function to print the Technical Analysis results in a nice format.
    '''
    # Get the results we are interested in
    drawdown = round(analyzer.drawdown , 2)
    moneydown = int(analyzer.moneydown)
    length = analyzer.len
    max_dd = round(analyzer.max.drawdown , 2)
    max_md = int(analyzer.max.moneydown)
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
    # row_format = "{:<15}" * (header_length + 1)
    print("Drawdown Analysis Results:")
    for i , row in enumerate(print_list):
        if i % 2 == 0:
            row_format = "{:<15}" * (header_length + 1)
            print(row_format.format('' , *row))
        else:
            row_format = "{:<15,}" * header_length
            print(' ' * 15 + row_format.format(*row).replace(',' , '/'))


# Create a Stratey
class TestStrategy(bt.Strategy):

    # place strategy parameters here:
    # ------------------------
    # ------------------------
    # ------------------------

    def log(self , txt , dt=None):
        # pass
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat() , txt))

        # place strategy '__init__' and 'next' code here:
        # ------------------------
        # ------------------------
        # ------------------------
        # ------------------------
        # ------------------------
        # ------------------------
        # ------------------------
        # ------------------------
        # ------------------------

    def notify_order(self , order):
        if order.status in [order.Submitted , order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return
        self.order = None

    def stop(self):
        report_txt = 'ma_period {} │ signal_threshold {} │ portfo {} │ rsi_period {} │' \
                     ' rsi_buy_level {} │ rsi_sell_level {} │ rsi_above_days {} │ Ending Value {:,.0f}'
        print(report_txt.format(self.params.ma_period ,
                                self.params.signal_threshold ,
                                self.params.portfo ,
                                self.params.rsi_period ,
                                self.params.rsi_buy_level ,
                                self.params.rsi_sell_level ,
                                self.params.rsi_above_days ,
                                self.broker.getvalue() / 10).replace(',' , '/'))
        self.final_balance = round(self.broker.get_value() , 2)
        self.exposure = round(self.in_position / self.data.buflen() * 100 , 2)


if __name__ == '__main__':
    cerebro = bt.Cerebro(optreturn=False ,
                         cheat_on_open=True ,
                         maxcpus=None
                         )

    # Add a strategy:
    strats = cerebro.optstrategy(TestStrategy ,
                                 ma_period=range(50 , 53) ,
                                 rsi_period=range(5 , 8))

    # load data:
    sd.add_cerebro_data(cerebro , start='2010-01-01' , end='2020-01-01')

    startcash = 10000000
    cerebro.broker.setcash(startcash)
    cerebro.broker.set_checksubmit(checksubmit=False)
    cerebro.broker.set_coc(coc=True)

    # Add the new commissions scheme:
    cerebro.broker.setcommission(commission=0.01)

    # Add the analyzers we are interested in
    # cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="ta")
    cerebro.addanalyzer(bt.analyzers.DrawDown , _name="dd")
    # cerebro.addanalyzer(bt.analyzers.AnnualReturn, _name="ar")

    print('Starting Portfolio Value: {:,.0f}'.format(cerebro.broker.getvalue() / 10).replace("," , "/"))

    # Run over everything:
    start_time = time.time()
    opt_runs = cerebro.run(stdstats=False)
    end_time = time.time()
    print('\nElapsed time: ' + str(round(end_time - start_time , 2)) + ' seconds')

    # Generate results list:
    final_results_list = []
    result = []
    for run in opt_runs:
        for strategy in run:
            drawdown = round(strategy.analyzers.dd.get_analysis().max.drawdown , 2)
            final_balance = int(strategy.final_balance / 10)
            profit = int(final_balance - (startcash / 10))
            period = strategy.params.ma_period
            final_results_list.append([period , profit])

            result.append([
                strategy.params.ma_period ,
                strategy.params.signal_threshold ,
                strategy.params.portfo ,
                strategy.params.rsi_period ,
                strategy.params.rsi_buy_level ,
                strategy.params.rsi_sell_level ,
                strategy.params.rsi_above_days ,
                # defaults:
                strategy.exposure ,
                drawdown ,
                final_balance ,
                profit
            ])

    # save result to a csv file:
    current_name = os.path.basename(__file__)
    if '.py' in current_name:
        current_name = current_name.replace('.py' , '')
    sd.csvw(current_name , result ,
            ['ma_period' ,
             'signal_threshold' ,
             'portfo' ,
             'rsi_period' ,
             'rsi_buy_level' ,
             'rsi_sell_level' ,
             'rsi_above_days' ,
             # defaults:
             'exposure' ,
             'drawdown' ,
             'final_balance' ,
             'profit'
             ])

    # Sort Results List:
    by_period = sorted(final_results_list , key=lambda x: x[0])
    by_PnL = sorted(final_results_list , key=lambda x: x[1] , reverse=True)

    # Print results
    # print('Results: Ordered by period:')
    # for result in by_period:
    #     print('Period: {}, PnL: {}'.format(result[0] , result[1]))
    # print('Results: Ordered by Profit:')
    # for result in by_PnL:
    #     print('Period: {}, PnL: {}'.format(result[0] , result[1]))
