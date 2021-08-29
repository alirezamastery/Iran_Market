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
        ('portfo' , 5) ,
        ('ma_period' , 300) ,
        ('signal_threshold' , 10)
    )

    def log(self , txt , dt=None):
        pass
        # ''' Logging function fot this strategy'''
        # dt = dt or self.datas[0].datetime.date(0)
        # print('%s, %s' % (dt.isoformat() , txt))

    def __init__(self):
        self.portfo = self.params.portfo
        self.s_th = (self.params.signal_threshold / 100) + 1
        self.position_flag = []
        self.sym_count_o = 0
        self.sym_count_e = 0

        self.range = self.portfo * 2
        self.range_start = 2

        self.symbols = self.getdatanames()
        self.symbol_key = dict()

        # call RS indicator and data names:
        self.inds = dict()
        for i in range(self.range_start , self.range , 2):
            # self.symbol_key[self.datas[i]] = self.symbols[i]
            self.position_flag.append([i , self.datas[i]._name , False])
            self.position_flag.append([i + 1 , self.datas[i + 1]._name , False])
            self.inds[i] = dict()
            plotname = self.datas[i]._name + ' / ' + self.datas[i + 1]._name
            self.inds[i]['RS'] = oind.RS_100(self.datas[i] , self.datas[i + 1] ,
                                             ma_period=self.params.ma_period ,
                                             plotname=plotname ,
                                             plotyticks=[50 , 100 , 150] ,
                                             plothlines=[50 , 100 , 150] ,
                                             )
            self.prs = dict()

        for i in range(self.range_start , self.range , 2):
            self.prs[i] = dict()
            self.prs[i]['signal'] = [None , None]
            self.prs[i]['close'] = [None , -1]
            self.prs[i]['pos'] = [None , None]
            self.prs[i]['per'] = True
            self.prs[i]['donothing'] = False

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
        for i in range(self.range_start , self.range , 2):
            if self.inds[i]['RS'].MA[0] * self.s_th < self.inds[i]['RS'].RS[0]:
                self.prs[i]['signal'] = [i , self.datas[i]._name]
                self.prs[i]['close'] = [i + 1 , self.datas[i + 1]._name]
                self.prs[i]['donothing'] = False
                # print(self.prs[i])
            elif self.inds[i]['RS'].MA[0] > self.inds[i]['RS'].RS[0] * self.s_th:
                self.prs[i]['signal'] = [i + 1 , self.datas[i + 1]._name]
                self.prs[i]['close'] = [i , self.datas[i]._name]
                self.prs[i]['donothing'] = False
                # print(self.prs[i])
            else:
                self.prs[i]['donothing'] = True
        # self.log(self.prs[2])

        # open positions:
        for i in range(self.range_start , self.range , 2):
            if self.prs[i]['signal'] != self.prs[i]['pos'] and self.prs[i]['per'] and not self.prs[i]['donothing']:
                number = self.prs[i]['signal'][0]
                name = self.prs[i]['signal'][1]
                comm_adj_price = self.datas[number].close[0] * (1 + (comm * 1))
                comm_adj_size = sizes / comm_adj_price
                size = sys_math.floor(comm_adj_size)
                self.order = self.buy(data=self.datas[number] , size=size)
                self.prs[i]['pf'] = True
                self.log('BUY CREATED: %s , Price: %.2f , Size: %d' % (name ,
                                                                       self.datas[number].close[0] ,
                                                                       size))
                self.sym_count_o += 1
                self.prs[i]['pos'] = [number , name]
                self.prs[i]['per'] = False

        # close signals:
        for i in range(self.range_start , self.range , 2):
            if self.prs[i]['close'] == self.prs[i]['pos'] and not self.prs[i]['donothing']:
                number = self.prs[i]['close'][0]
                name = self.prs[i]['close'][1]
                self.order = self.close(data=self.datas[number])
                self.log('SELL CREATED: %s , %.2f' % (name , self.datas[number].close[0]))
                self.prs[i]['pf'] = False
                self.prs[i]['per'] = True
                self.prs[i]['pos'] = [None , None]
                self.sym_count_o -= 1

    def notify_order(self , order):
        if order.status in [order.Submitted , order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return
        self.order = None

    def stop(self):
        report_txt = 'portfo {} │ ma_period {} │ signal_threshold {} │ Ending Value {:,.0f}'
        print(report_txt.format(self.params.portfo ,
                                self.params.ma_period ,
                                self.params.signal_threshold ,
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
                                 portfo=range(5 , 8))

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
                strategy.params.portfo ,
                strategy.params.ma_period ,
                strategy.params.signal_threshold ,
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
             'signal_threshold' ,
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
