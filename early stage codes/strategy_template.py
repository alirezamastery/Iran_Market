from __future__ import (absolute_import , division , print_function , unicode_literals)
import datetime  # For datetime objects
import os.path  # To manage paths
import sys  # To find out the script name (in argv[0])
import numpy as np
import statistics
import pandas
import datetime as dt
import symdata as sd
import math as sys_math
import backtrader as bt
import backtrader.indicators as btind
import backtrader.mathsupport as math
import our_indicators as oind
import ctypes

kernel32 = ctypes.windll.kernel32
kernel32.SetConsoleMode(kernel32.GetStdHandle(-11) , 7)

# FRAME = '\033[52m'
FRAME = '\033[0m'
RESET = '\033[0m'
UNDERLINE = '\033[4m'


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
    pnl_net = int(analyzer.pnl.net.total / 10)
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
    print("\nTrade Analysis Results:")
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
    moneydown = int(analyzer.moneydown / 10)
    length = analyzer.len
    max_dd = round(analyzer.max.drawdown , 2)
    max_md = int(analyzer.max.moneydown / 10)
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
    print("\nDrawdown Analysis Results:")
    for i , row in enumerate(print_list):
        if i % 2 == 0:
            row_format = "{:<15}" * (header_length + 1)
            print(row_format.format('' , *row))
        else:
            row_format = "{:<15,}" * header_length
            print(' ' * 15 + row_format.format(*row).replace(',' , '/'))


# Create a Stratey
class strategy_template(bt.Strategy):
    ispairs = False
    data_range_start = 2
    col1_width = 14
    col2_width = 10
    col3_width = 9
    col4_width = 16
    col5_width = 16
    delimiter = '|'

    def __init__(self):
        self.commission = 0.01
        self.position_flag = []
        self.sym_count_o = 0
        self.sym_count_e = 0
        self.sizes = -1
        self.symbols = self.getdatanames()

        # call RS indicator and data names:
        self.inds = dict()
        # if we have pairs:
        if self.ispairs:
            # start and range of symbols:
            self.range_start = self.base_params
            self.range = (1 + self.portfo) * 2
            for i in range(2 , self.range):
                self.inds[i] = dict()
                if i % 2 == 0:
                    self.position_flag.append([i , self.datas[i]._name , False])
                    self.position_flag.append([i + 1 , self.datas[i + 1]._name , False])
                    plotname = self.datas[i]._name + ' / ' + self.datas[i + 1]._name
                    self.inds[i]['RS'] = oind.RS_100(self.datas[i] , self.datas[i + 1] ,
                                                     ma_period=self.params.ma_period ,
                                                     plotname=plotname ,
                                                     plotyticks=[50 , 100 , 150] ,
                                                     plothlines=[50 , 100 , 150] ,
                                                     )
                self.inds[i]['RSI'] = bt.indicators.RSI_Safe(self.datas[i] , period=self.params.rsi_period)

            self.prs = dict()
            for i in range(self.range_start , self.range , 2):
                self.prs[i] = dict()
                self.prs[i]['signal'] = [None , None]
                self.prs[i]['close'] = [None , -1]
                self.prs[i]['pos'] = [None , None]
                self.prs[i]['per'] = True
                self.prs[i]['donothing'] = False
        # if TEPIX is base:
        else:
            self.irs = []
            for i , d in enumerate(self.datas):
                if i == 0:
                    self.position_flag.append([i , d._name , False])
                else:
                    self.position_flag.append([i , self.datas[i]._name , False])
                    self.inds[d] = dict()
                    plotname = self.datas[i]._name + ' / ' + self.datas[0]._name
                    self.inds[d]['RS'] = oind.RS_100(self.datas[i] , self.datas[0] ,
                                                     ma_period=self.params.ma_period ,
                                                     plotname=plotname ,
                                                     plotyticks=[50 , 100 , 150] ,
                                                     plothlines=[50 , 100 , 150] ,
                                                     )
                    self.inds[d]['RSI'] = bt.indicators.RSI_Safe(self.datas[i] , period=self.params.rsi_period)

        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None
        # Final Balance:
        self.final_balance = -1
        # To calculate exposure:
        self.passed = 0
        self.in_position = 0
        self.exposure = -1
        # print('_' * (41 + self.col1_width + self.col2_width + self.col3_width + self.col4_width + self.col5_width))

    def next_open(self):
        # exposure:
        if self.passed != len(self.data):
            self.in_position += self.sym_count_e / self.portfo
            self.passed = len(self.data)

        # Check if an order is pending ... if yes, we cannot send a 2nd one:
        if self.order:
            return

        if len(self.data) == self.data.buflen():
            for i , d in enumerate(self.datas):
                self.order = self.close(data=self.datas[i])
            return

        # calculate volume for each symbol:
        self.sizes = -1
        if self.portfo > self.sym_count_o:
            self.sizes = self.broker.get_cash() // (self.portfo - self.sym_count_o)

    def log(self , txt , dt=None):
        # pass
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print(FRAME + '{}{} {}'.format(dt.isoformat() , self.delimiter , txt) + RESET)

    def log_buy(self , index , size):
        self.log('{}{} {:{}.{}} {} Price: {:>{}.2f} {} Size:{:>{},} {} {:{}} '.format(
                'BUY CREATED'.ljust(self.col1_width , ' ') , self.delimiter ,
                self.symbols[index] , self.col2_width , self.col2_width , self.delimiter ,
                self.datas[index].close[0] , self.col3_width , self.delimiter ,
                size , self.col4_width , self.delimiter ,
                ' ' , self.col5_width + 5).replace(',' , '/')
                 )

    def log_sell(self , index):
        self.log('{}{} {:{}.{}} {} Price: {:>{}.2f} {} {:{}} {} {:{}} '.format(
                'SELL CREATED'.ljust(self.col1_width , ' ') , self.delimiter ,
                self.symbols[index] , self.col2_width , self.col2_width , self.delimiter ,
                self.datas[index].close[0] , self.col3_width , self.delimiter ,
                ' ' , self.col4_width + 5 , self.delimiter ,
                ' ' , self.col5_width + 5)
        )

    def notify_order(self , order):
        if order.status in [order.Submitted , order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                        '{}{} {:{}.{}} {} Price: {:>{}.2f} {} Cost:{:>{},.0f} {} Comm:{:>{},.0f} '.format(
                                'BUY EXECUTED'.ljust(self.col1_width , ' ') , self.delimiter ,
                                order.data._name , self.col2_width , self.col2_width , self.delimiter ,
                                order.executed.price , self.col3_width , self.delimiter ,
                                order.executed.value / 10 , self.col4_width , self.delimiter ,
                                order.executed.comm / 10 , self.col5_width).replace(',' , '/')
                )
                pos = find_in_list_of_lists(self.position_flag , order.data._name)
                self.sym_count_e += 1
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log('{}{} {:{}.{}} {} Price: {:>{}.2f} {} Cost:{:>{},.0f} {} Comm:{:>{},.0f} '.format(
                        'SELL EXECUTED'.ljust(self.col1_width , ' ') , self.delimiter ,
                        order.data._name , self.col2_width , self.col2_width , self.delimiter ,
                        order.executed.price , self.col3_width , self.delimiter ,
                        order.executed.value / 10 , self.col4_width , self.delimiter ,
                        order.executed.comm / 10 , self.col5_width).replace(',' , '/')
                         )
                pos = find_in_list_of_lists(self.position_flag , order.data._name)
                self.sym_count_e -= 1
            self.bar_executed = len(self)

        elif order.status == order.Canceled:
            self.log('Order Problem: %s CANCELED' % (order.data._name))
        elif order.status == order.Margin:
            self.log('Order Problem: %s MARGIN' % (order.data._name))
        elif order.status == order.Rejected:
            self.log('Order Problem: %s REJECTED' % (order.data._name))

        self.order = None

    def notify_trade(self , trade):
        if not trade.isclosed:
            return

        self.log(
                '{}{} {:{}.{}} {} {} {} GROSS:{:>{},.0f} {} NET :{:>{},.0f} '.format(
                        'TRADE PROFIT'.ljust(self.col1_width , ' ') , self.delimiter ,
                        trade.data._name , self.col2_width , self.col2_width , self.delimiter ,
                        ' '.ljust(self.col3_width + 7) , self.delimiter ,
                        trade.pnl / 10 , self.col4_width - 1 , self.delimiter ,
                        trade.pnlcomm / 10 , self.col5_width ,
                        ' ').replace(',' , '/'))

    def stop(self):
        # print('‾' * (41 + self.col1_width + self.col2_width + self.col3_width + self.col4_width + self.col5_width))
        self.exposure = self.in_position / self.data.buflen() * 100
        print('Exposure:' , round(self.exposure , 2) , '%')


class RSI_RS(strategy_template):
    params = (
        ('portfo' , 5) ,
        ('ma_period' , 200) ,
        ('RS_min' , 100) ,
        ('signal_threshold' , 10) ,
        ('RS_max_switch' , True) ,
        ('rsi_period' , 14) ,
        ('rsi_buy_level' , 70) ,
        ('rsi_sell_level' , 50) ,
        ('rsi_above_days' , 1) ,
    )

    def __init__(self):
        super().__init__()
        self.portfo = self.params.portfo
        self.RS_min = self.params.RS_min
        self.rsi_period = self.params.rsi_period
        self.s_th = (self.params.signal_threshold / 100) + 1

    def next_open(self):
        super().next_open()
        # check RS vs MA for each symbol:
        self.irs = []
        for i , d in enumerate(self.datas):
            if d._name == 'TEPIX':
                pass
            # -------------------------------------------------------------------------------------
            # if RS_max_switch == True:
            elif self.params.RS_max_switch and self.inds[d]['RS'].MA[0] * self.s_th < self.inds[d]['RS'].RS[0] and \
                    self.inds[d]['RSI'].rsi[0] > self.params.rsi_buy_level and \
                    self.inds[d]['RS'].RS[0] > self.RS_min and not self.position_flag[i][2]:
                # check how many days RSI was above by level:
                above_days = True
                for j in range(0 , self.params.rsi_above_days):
                    if self.inds[d]['RSI'].rsi[-j] < self.params.rsi_buy_level:
                        above_days = False
                        break
                # if every condition was met add the symbol to irs:
                if above_days:
                    self.irs.append([i , self.inds[d]['RS'].RS[0]])
            # -------------------------------------------------------------------------------------
            # if RS_max_switch == False:
            elif not self.params.RS_max_switch and \
                    self.inds[d]['RS'].MA[0] * self.s_th < self.inds[d]['RS'].RS[0] < self.RS_min and \
                    self.inds[d]['RSI'].rsi[0] > self.params.rsi_buy_level and \
                    not self.position_flag[i][2]:
                # check how many days RSI was above by level:
                above_days = True
                for j in range(0 , self.params.rsi_above_days):
                    if self.inds[d]['RSI'].rsi[-j] < self.params.rsi_buy_level:
                        above_days = False
                        break
                # if every condition was met add the symbol to irs:
                if above_days:
                    self.irs.append([i , self.inds[d]['RS'].RS[0]])

        # create list of signaled symbols for portfo:
        if self.params.RS_max_switch:
            self.irs.sort(key=lambda x: x[1] , reverse=True)
        if not self.params.RS_max_switch:
            self.irs.sort(key=lambda x: x[1] , reverse=False)
        self.portfo_syms = self.irs[:self.portfo]

        # open positions:
        for i , sym in enumerate(self.portfo_syms):
            if self.sym_count_o >= self.portfo or len(self.portfo_syms) < 1:
                break
            if not self.position_flag[sym[0]][2]:
                comm_adj_price = self.datas[sym[0]].close[0] * (1 + (self.commission * 1))
                comm_adj_size = self.sizes / comm_adj_price
                size = sys_math.floor(comm_adj_size)
                self.order = self.buy(data=self.datas[sym[0]] , size=size)
                self.position_flag[sym[0]][2] = True
                self.log_buy(sym[0] , size)
                self.sym_count_o += 1

        # close signals:
        for i , data in enumerate(self.position_flag):
            if data[2] and self.inds[self.datas[data[0]]]['RSI'].rsi[0] < self.params.rsi_sell_level:
                self.log_sell(data[0])
                self.order = self.close(data=self.datas[data[0]])
                self.position_flag[i][2] = False
                self.sym_count_o -= 1


if __name__ == '__main__':
    cerebro = bt.Cerebro(cheat_on_open=True ,
                         # stdstats=False
                         )

    # Add a strategy
    cerebro.addstrategy(RSI_RS)

    # load data:
    sd.add_cerebro_data(cerebro , input_list='Strategies/strategy_template/pairs.txt' , data_path='../Data/' ,
                        start='2010-01-01' , end='2020-01-01' ,
                        show=['SHARAK' , 'Khodro'])

    cerebro.broker.setcash(10000000)
    cerebro.broker.set_checksubmit(checksubmit=False)
    cerebro.broker.set_coc(coc=True)

    # Add the new commissions scheme
    cerebro.broker.setcommission(commission=0.01)

    print('\nStarting Portfolio Value: {:,.0f}\n'.format(cerebro.broker.getvalue() / 10).replace("," , "/"))

    # Add the analyzers we are interested in
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer , _name="ta")
    cerebro.addanalyzer(bt.analyzers.DrawDown , _name="dd")
    cerebro.addanalyzer(bt.analyzers.AnnualReturn , _name="ar")

    # Add the Observers we are interested in
    # cerebro.addobserver(bt.observers.DrawDown)
    # cerebro.addobserver(bt.observers.TimeReturn)
    # cerebro.addobserver(bt.observers.Benchmark , data=cerebro.datas[0])

    # Add writer to save result in a csv file
    # cerebro.addwriter(bt.WriterFile, csv=True, out='results.csv')

    # Run over everything
    strategies = cerebro.run()
    firstStrat = strategies[0]

    # print the analyzers
    printTradeAnalysis(firstStrat.analyzers.ta.get_analysis())
    printDrawDownAnalysis(firstStrat.analyzers.dd.get_analysis())

    # anu_ret = firstStrat.analyzers.ar.get_analysis()
    # print(firstStrat.analyzers.ar.get_analysis())

    print('\nFinal Portfolio Value: {:,.0f}'.format(cerebro.broker.getvalue() / 10).replace("," , "/"))
    # print(firstStrat.analyzers.dd.get_analysis())

    # Plot the result
    # cerebro.plot(style='candlestick' , rowsmajor=2 , rowsminor=1 , barup='#26a69a' , bardown='Yellow' ,
    #              volup='#c3e7d5' , voldown='#f8c1c6' , voltrans=1)
