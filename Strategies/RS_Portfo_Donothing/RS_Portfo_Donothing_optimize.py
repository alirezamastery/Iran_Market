from __future__ import (absolute_import , division , print_function , unicode_literals)
import math as sys_math
import os  # To manage paths
import time
import backtrader as bt
import our_indicators as oind
import symdata as sd


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
    params = (
        ('portfo' , 10) ,
        ('ma_period' , 89) ,
        ('RS_min' , 100) ,
        ('signal_threshold' , 5) ,
        ('RS_max_switch' , True) ,
    )

    def log(self , txt , dt=None):
        pass
        # ''' Logging function fot this strategy'''
        # dt = dt or self.datas[0].datetime.date(0)
        # print('%s, %s' % (dt.isoformat() , txt))

    def __init__(self):
        self.fs = [0] * self.params.portfo
        self.portfo = self.params.portfo
        self.position_flag = []
        self.sym_count_o = 0
        self.sym_count_e = 0
        self.RS_min = self.params.RS_min
        self.s_th = (self.params.signal_threshold / 100) + 1
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

        self.portfo_syms = []

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
        if self.passed != len(self.data):
            self.in_position += self.sym_count_o / self.portfo
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
                # self.log('BUY CREATED: %s , Price: %.2f , Size: %d' % (self.symbols[sym[0]] ,
                #                                                        self.datas[sym[0]].close[0] ,
                #                                                        size))
                self.sym_count_o += 1

        # close signals:
        for i , data in enumerate(self.position_flag):
            if data[2] and self.inds[self.datas[data[0]]]['RS'].RS[0] < self.inds[self.datas[data[0]]]['RS'].MA[0]:
                # self.log('SELL CREATED: %s , %.2f' % (self.symbols[data[0]] , self.datas[data[0]].close[0]))
                self.order = self.close(data=self.datas[data[0]])
                self.position_flag[i][2] = False
                self.sym_count_o -= 1

    def notify_order(self , order):
        if order.status in [order.Submitted , order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return
        self.order = None

    def stop(self):
        report_txt = ' portfo {} │ ma_period {} │ RS_min {} │ signal_threshold {} │ ' \
                     'RS_max_switch {} │ Ending Value {:,.0f}'
        print(report_txt.format(self.params.portfo ,
                                self.params.ma_period ,
                                self.params.RS_min ,
                                self.params.signal_threshold ,
                                self.params.RS_max_switch ,
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
                                 RS_min=range(80 , 83))

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
    params = (
        ('portfo' , 10) ,
        ('ma_period' , 89) ,
        ('RS_min' , 100) ,
        ('signal_threshold' , 0.05) ,
        ('RS_max_switch' , True) ,
    )
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
                strategy.params.portfo ,
                strategy.params.ma_period ,
                strategy.params.RS_min ,
                strategy.params.signal_threshold ,
                strategy.params.RS_max_switch ,
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
            ['portfo' ,
             'ma_period' ,
             'RS_min' ,
             'signal_threshold' ,
             'RS_max_switch' ,
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
