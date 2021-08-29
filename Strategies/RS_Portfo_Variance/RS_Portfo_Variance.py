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


# Create a Stratey
class TestStrategy(bt.Strategy):
    params = (
        ('ma_period' , 89) ,
        ('portfo' , 5) ,
        ('RS_min' , 100) ,
        ('signal_threshold' , 0.05) ,
        ('RS_max_switch' , True) ,
        ('VAR_max_switch' , False)
    )

    def log(self , txt , dt=None):
        # pass
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat() , txt))

    def __init__(self):
        self.fs = [0] * self.params.portfo
        self.portfo = self.params.portfo
        self.s_th = (self.params.signal_threshold / 100) + 1
        self.position_flag = []
        self.sym_count_o = 0
        self.sym_count_e = 0
        self.RS_min = self.params.RS_min
        self.buysig = False

        self.symbols = self.getdatanames()
        self.symbol_key = dict()

        # call RS indicator and data names:
        self.inds = dict()
        for i , d in enumerate(self.datas):
            if i == 0:
                self.symbol_key[d] = self.symbols[i]
                self.position_flag.append([i , d._name , False])
            else:
                self.symbol_key[d] = self.symbols[i]
                self.position_flag.append([i , d._name , False])
                self.inds[d] = dict()
                plotname = self.symbol_key[self.datas[i]] + ' / ' + self.symbol_key[self.datas[0]]
                self.inds[d]['RS'] = oind.RS_100(self.datas[i] , self.datas[0] ,
                                                 ma_period=self.params.ma_period ,
                                                 plotname=plotname ,
                                                 plotyticks=[50 , 100 , 150] ,
                                                 plothlines=[50 , 100 , 150] ,
                                                 )

        self.irs = [[0 , 0] for item in range(len(self.symbols))]
        for i in range(len(self.symbols)):
            self.irs[i][0] = i

        self.variance = [-1 for x in range(len(self.symbols))]

        self.portfo_syms = []
        self.inserted = [-1 , False]

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

    def next_open(self):
        # exposure:
        if self.sym_count_e > self.portfo:
            print(self.sym_count_e)
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
        sizes = -1
        if self.portfo > self.sym_count_o:
            sizes = sys_math.floor(1 * self.broker.get_cash() / (self.portfo - self.sym_count_o))
        comm = 0.01

        # open inserted position:
        if self.inserted[1]:
            comm_adj_price = self.datas[self.inserted[0]].close[0] * (1 + (comm * 1))
            comm_adj_size = sizes / comm_adj_price
            size = sys_math.floor(comm_adj_size)
            self.order = self.buy(data=self.datas[self.inserted[0]] , size=size)
            self.log('inserted BUY CREATED: %s , Price: %.2f , Size: %d' % (self.symbols[self.inserted[0]] ,
                                                                            self.datas[self.inserted[0]].close[0] ,
                                                                            size))
            self.position_flag[self.inserted[0]][2] = True
            self.inserted = [-1 , False]
            self.sym_count_o += 1

        # calculate variance of 'ma_period' candles before:
        for i , d in enumerate(self.datas):
            var_data = []
            for j in range(self.params.ma_period):
                var_data.append(d.close[-j])
            self.variance[i] = np.var(var_data)

        # check RS vs MA for each symbol:
        self.irs = []
        for i , d in enumerate(self.datas):
            if d._name == 'TEPIX':
                pass
            # if RS_max_switch == True:
            elif self.params.RS_max_switch and self.inds[d]['RS'].MA[0] * self.s_th < self.inds[d]['RS'].RS[0] and \
                    self.inds[d]['RS'].RS[0] > self.RS_min and not self.position_flag[i][2]:
                self.irs.append([i , self.inds[d]['RS'].RS[0]])
            # if RS_max_switch == False:
            elif not self.params.RS_max_switch and \
                    self.inds[d]['RS'].MA[0] * self.s_th < self.inds[d]['RS'].RS[0] < self.RS_min and \
                    not self.position_flag[i][2]:
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
                comm_adj_price = self.datas[sym[0]].close[0] * (1 + (comm * 1))
                comm_adj_size = sizes / comm_adj_price
                size = sys_math.floor(comm_adj_size)
                self.order = self.buy(data=self.datas[sym[0]] , size=size)
                self.position_flag[sym[0]][2] = True
                self.log('BUY CREATED: %s , Price: %.2f , Size: %d' % (self.symbols[sym[0]] ,
                                                                       self.datas[sym[0]].close[0] ,
                                                                       size))
                self.sym_count_o += 1

        # check variance for new signals:
        opens = []
        vars = []
        if self.sym_count_e >= self.portfo:
            for i , d in enumerate(self.position_flag):
                if d[2]:
                    opens.append(d)
                    vars.append(self.variance[d[0]])
            # variance min:
            if self.params.VAR_max_switch and len(self.irs) > 0 and min(vars) > self.variance[self.irs[0][0]]:
                # close the min position:
                selector = self.variance.index(min(vars))
                self.order = self.close(data=self.datas[selector])
                self.position_flag[selector][2] = False
                self.sym_count_o -= 1
                self.log('inserted SELL CREATED: %s , %.2f' % (self.symbols[selector] , self.datas[selector].close[0]))
                # open new signal:
                self.inserted = [self.irs[0][0] , True]
            # variance max
            if not self.params.VAR_max_switch and len(self.irs) > 0 and max(vars) < self.variance[self.irs[0][0]]:
                # close the min position:
                selector = self.variance.index(min(vars))
                self.order = self.close(data=self.datas[selector])
                self.position_flag[selector][2] = False
                self.sym_count_o -= 1
                self.log('inserted SELL CREATED: %s , %.2f' % (self.symbols[selector] , self.datas[selector].close[0]))
                # open new signal:
                self.inserted = [self.irs[0][0] , True]

        # close signals:
        for i , data in enumerate(self.position_flag):
            if data[2] and self.inds[self.datas[data[0]]]['RS'].RS[0] < self.inds[self.datas[data[0]]]['RS'].MA[0]:
                self.log('SELL CREATED: %s , %.2f' % (self.symbols[data[0]] , self.datas[data[0]].close[0]))
                self.order = self.close(data=self.datas[data[0]])
                self.position_flag[i][2] = False
                self.sym_count_o -= 1

    def notify_order(self , order):
        if order.status in [order.Submitted , order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                        'BUY EXECUTED: %s , Price: %.2f, Cost: %.2f, Comm %.2f' %
                        (order.data._name ,
                         order.executed.price ,
                         order.executed.value ,
                         order.executed.comm))
                pos = find_in_list_of_lists(self.position_flag , order.data._name)
                self.sym_count_e += 1
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log('SELL EXECUTED: %s , Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.data._name ,
                          order.executed.price ,
                          order.executed.value ,
                          order.executed.comm))
                pos = find_in_list_of_lists(self.position_flag , order.data._name)
                self.sym_count_e -= 1
            self.bar_executed = len(self)

        elif order.status == order.Canceled:
            self.log('Order Problem: Canceled , Symbol: %s' % (order.data._name))
        elif order.status == order.Margin:
            self.log('Order Problem: Margin , Symbol: %s' % (order.data._name))
        elif order.status == order.Rejected:
            self.log('Order Problem: Rejected , Symbol: %s' % (order.data._name))

        self.order = None

    def notify_trade(self , trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT:  GROSS: {:<10,.0f} | NET: {:<10,.0f}'.format(trade.pnl ,
                                                                                 trade.pnlcomm).replace(',' , '/'))

    def stop(self):
        self.exposure = self.in_position / self.data.buflen() * 100
        print('Exposure:' , round(self.exposure , 2) , '%')


if __name__ == '__main__':
    cerebro = bt.Cerebro(cheat_on_open=True ,
                         # stdstats=False
                         )

    # Add a strategy
    cerebro.addstrategy(TestStrategy)

    # load data:
    sd.add_cerebro_data(cerebro , input_list='../../Lists/input_data/pairs.txt' ,
                        start='2010-01-01' , end='2020-01-01' ,
                        show=[])

    cerebro.broker.setcash(1000000)
    cerebro.broker.set_checksubmit(checksubmit=False)
    cerebro.broker.set_coc(coc=True)

    # Add the new commissions scheme
    cerebro.broker.setcommission(commission=0.01)

    print('Starting Portfolio Value: {:,.0f}'.format(cerebro.broker.getvalue()).replace("," , "/"))

    # Add the analyzers we are interested in
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer , _name="ta")
    cerebro.addanalyzer(bt.analyzers.DrawDown , _name="dd")
    cerebro.addanalyzer(bt.analyzers.AnnualReturn , _name="ar")

    # Add the Observers we are interested in
    # cerebro.addobserver(bt.observers.DrawDown)
    # cerebro.addobserver(bt.observers.TimeReturn)
    # cerebro.addobserver(bt.observers.Benchmark , data=cerebro.datas[0])

    # Add writer to save result in a csv file
    # cerebro.addwriter(bt.WriterFile , csv=True , out='results.csv')

    # Run over everything
    strategies = cerebro.run()
    firstStrat = strategies[0]

    # print the analyzers
    printTradeAnalysis(firstStrat.analyzers.ta.get_analysis())
    printDrawDownAnalysis(firstStrat.analyzers.dd.get_analysis())

    anu_ret = firstStrat.analyzers.ar.get_analysis()
    # print(firstStrat.analyzers.ar.get_analysis())

    print('Final Portfolio Value: {:,.0f}'.format(cerebro.broker.getvalue()).replace("," , "/"))
    # print(firstStrat.analyzers.dd.get_analysis())

    # Plot the result
    cerebro.plot(style='candlestick' , rowsmajor=1 , rowsminor=1 , barup='#26a69a' , bardown='#ef5350' ,
                 volup='#c3e7d5' , voldown='#f8c1c6' , voltrans=1)
