# from __future__ import (absolute_import , division , print_function , unicode_literals)
import os
import sys  # To find out the script name (in argv[0])
import pathlib
import csv
import pandas as pd
import symdata as sd
import time
import backtrader as bt
import backtrader.mathsupport as math
import our_indicators as oind
import ctypes
import re

# make script path the working directory so relative paths work:
os.chdir(os.path.dirname(sys.argv[0]))
sys.path.append(os.path.abspath(''))
# settings for console so it can show ANSI escape:
kernel32 = ctypes.windll.kernel32
kernel32.SetConsoleMode(kernel32.GetStdHandle(-11) , 7)
# identify ANSI escape so it won't be saved to log file:
ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
# some ANSI escape characters:
RESET = '\033[0m'
UNDERLINE = '\033[4m'
RED = '\033[31m'
GREEN = '\033[38;5;40m'
FRAME = '\033[38;5;196'

report_column_width = 15


def find_in_list_of_lists(mylist , char):
    for sub_list in mylist:
        if char in sub_list:
            return mylist.index(sub_list)
    raise ValueError("'{char}' is not in list".format(char=char))


def save_log(function):
    def wrapper(*args):
        text = function(*args)
        out_text = ansi_escape.sub('' , text)
        with open('../Strategies/RS_RSI_Pairs_FIX20/log.txt' , 'a' , encoding='utf-8') as log_file:
            log_file.write(out_text + '\n')

    return wrapper


@save_log
def print_custom(*args):
    out = []
    for s in args:
        out.append(s)
    out = ' '.join(out)
    print(out)
    return out


# Base Strategy class:
class RS_base(bt.Strategy):
    optimize = False
    ispairs = False
    RSI = False
    commission = 0.01
    add_fixincome = False
    fix_income_commission = 0.0001
    data_range_start = 3
    num_of_runs = 0
    show_time = False
    # log layout settings:
    col1_width = 14
    col2_width = 10
    col3_width = 9
    col4_width = 16
    col5_width = 15
    delimiter = '│'
    table_row = False
    table_wall = True
    row_line_format = '{}' + '─' * 10 + '{}' + \
                      '─' * (col1_width + 1) + '{}' + \
                      '─' * (col2_width + 2) + '{}' + \
                      '─' * (col3_width + 9) + '{}' + \
                      '─' * (col4_width + 7) + '{}' + \
                      '─' * (col5_width + 7) + '{}'
    row_separator = row_line_format.format('├' , '┼' , '┼' , '┼' , '┼' , '┼' , '┤')
    row_start = row_line_format.format('┌' , '┬' , '┬' , '┬' , '┬' , '┬' , '┐')
    row_end = row_line_format.format('└' , '┴' , '┴' , '┴' , '┴' , '┴' , '┘')

    def __init__(self):
        self.time_start = time.time()
        self.time_end = -1

        RS_base.num_of_runs += 1

        self.portfo = self.params.portfo
        self.s_th = (self.params.signal_threshold / 100) + 1
        self.commission = 0.01
        self.position_flag = []
        self.sym_count_o = 0
        self.sym_count_e = 0
        self.sizes = -1
        self.symbols = self.getdatanames()

        # call RS indicator and data names:
        self.inds = dict()
        self.conditions = dict()
        # 1) if we have pairs:
        if self.ispairs:

            # start and range of symbols:
            self.range = self.data_range_start + self.portfo * 2

            if self.data_range_start % 2 == 0:
                even = True
            else:
                even = False
            # add indicators:
            for i in range(self.data_range_start , self.range):
                self.inds[i] = dict()
                self.conditions[i] = dict()
                # add RS indicator:
                if even and i % 2 == 0:
                    plotname = self.datas[i]._name + ' / ' + self.datas[i + 1]._name
                    self.inds[i]['RS'] = oind.RS_100(self.datas[i] , self.datas[i + 1] ,
                                                     ma_period=self.params.ma_period ,
                                                     plotname=plotname ,
                                                     plotyticks=[50 , 100 , 150] ,
                                                     plothlines=[50 , 100 , 150] ,
                                                     )
                elif not even and i % 2 != 0:
                    plotname = self.datas[i]._name + ' / ' + self.datas[i + 1]._name
                    self.inds[i]['RS'] = oind.RS_100(self.datas[i] , self.datas[i + 1] ,
                                                     ma_period=self.params.ma_period ,
                                                     plotname=plotname ,
                                                     plotyticks=[50 , 100 , 150] ,
                                                     plothlines=[50 , 100 , 150] ,
                                                     )
                # add RSI indicator:
                if self.RSI:
                    self.inds[i]['RSI'] = bt.indicators.RSI_Safe(self.datas[i] , period=self.params.rsi_period)
                # add RS indicator based on 20% fix income:
                if self.add_fixincome:
                    plotname = self.datas[i]._name + ' / ' + self.datas[0]._name
                    self.inds[i]['RS_fix20'] = oind.RS_100(self.datas[i] , self.datas[0] ,
                                                           ma_period=self.params.fix_ma_period ,
                                                           plotname=plotname ,
                                                           plotyticks=[50 , 100 , 150] ,
                                                           plothlines=[50 , 100 , 150])

            self.prs = dict()
            for i in range(self.data_range_start , self.range , 2):
                self.prs[i] = dict()
                self.prs[i]['signal'] = [None , None]
                self.prs[i]['new_signal'] = False
                self.prs[i]['position'] = [None , None]
                self.prs[i]['pos'] = [None , None]
                self.prs[i]['permission'] = True
                self.prs[i]['per'] = True
                self.prs[i]['donothing'] = False
                self.prs[i]['fix_income'] = False
                self.prs[i]['size'] = -1
                self.prs[i]['condition'] = None
                self.prs[i]['close'] = None

        # 2) if TEPIX is base:
        else:
            self.irs = []
            self.portfo_syms = []
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
                    # add RSI indicator:
                    if self.RSI:
                        self.inds[d]['RSI'] = bt.indicators.RSI_Safe(self.datas[i] , period=self.params.rsi_period)

        self.sizes = -1
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
        # table form printing:
        self.table_width = 41 + self.col1_width + self.col2_width + \
                           self.col3_width + self.col4_width + self.col5_width
        if not self.optimize:
            print_custom(self.row_start)
            self.first_row = True

    def on_open(self):
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
        'Logging function fot this strategy'
        if not self.optimize:
            dt = dt or self.datas[0].datetime.date(0)
            # if you want full table structure:
            if self.table_row:
                if not self.first_row:
                    print_custom(self.row_separator)
                line = f'{self.delimiter}{dt.isoformat()}{self.delimiter} {txt}{self.delimiter}' + RESET
                print_custom(line)
                self.first_row = False
            # if you want partial table structure
            else:
                line = f'{self.delimiter}{dt.isoformat()}{self.delimiter} {txt}{self.delimiter}' + RESET
                print_custom(line)
        else:
            return

    def log_buy(self , data_index , size):
        if not self.optimize:
            self.log('{}{} {:{}.{}} {} Price: {:>{}.2f} {} Size:{:>{},} {} {:{}} '.format(
                    'BUY CREATED'.ljust(self.col1_width , ' ') , self.delimiter ,
                    self.symbols[data_index] , self.col2_width , self.col2_width , self.delimiter ,
                    self.datas[data_index].close[0] , self.col3_width , self.delimiter ,
                    int(size) , self.col4_width , self.delimiter ,
                    ' ' , self.col5_width + 5).replace(',' , '/')
                     )
        else:
            return

    def log_sell(self , data_index):
        if not self.optimize:
            self.log('{}{} {:{}.{}} {} Price: {:>{}.2f} {} {:{}} {} {:{}} '.format(
                    'SELL CREATED'.ljust(self.col1_width , ' ') , self.delimiter ,
                    self.symbols[data_index] , self.col2_width , self.col2_width , self.delimiter ,
                    self.datas[data_index].close[0] , self.col3_width , self.delimiter ,
                    ' ' , self.col4_width + 5 , self.delimiter ,
                    ' ' , self.col5_width + 5)
            )
        else:
            return

    def notify_order(self , order):
        if order.status in [order.Submitted , order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        if not self.optimize:
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
                    # pos = find_in_list_of_lists(self.position_flag , order.data._name)
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
                    # pos = find_in_list_of_lists(self.position_flag , order.data._name)
                    self.sym_count_e -= 1
                self.bar_executed = len(self)

            elif order.status == order.Canceled:
                self.log('{:{}}{} {:{}.{}} {} {:^{}} {} {:{}} {} {:{}} '.format(
                        'ORDER PROBLEM' , self.col1_width , self.delimiter ,
                        order.data._name , self.col2_width , self.col2_width , self.delimiter ,
                        'CANCELED' , self.col3_width + 7 , self.delimiter ,
                        ' ' , self.col4_width + 5 , self.delimiter ,
                        ' ' , self.col5_width + 5))
            elif order.status == order.Margin:
                self.log('{:{}}{} {:{}.{}} {} {:^{}} {} free:{:>{},.0f} {} {:{}} '.format(
                        'ORDER PROBLEM' , self.col1_width , self.delimiter ,
                        order.data._name , self.col2_width , self.col2_width , self.delimiter ,
                        'MARGIN' , self.col3_width + 7 , self.delimiter ,
                        self.broker.get_cash() , self.col4_width , self.delimiter ,
                        ' ' , self.col5_width + 5))
            elif order.status == order.Rejected:
                self.log('{:{}}{} {:{}.{}} {} {:^{}} {} {:{}} {} {:{}} '.format(
                        'ORDER PROBLEM' , self.col1_width , self.delimiter ,
                        order.data._name , self.col2_width , self.col2_width , self.delimiter ,
                        'REJECTED' , self.col3_width + 7 , self.delimiter ,
                        ' ' , self.col4_width + 5 , self.delimiter ,
                        ' ' , self.col5_width + 5))

        self.order = None

    def notify_trade(self , trade):
        if self.optimize:
            return
        else:
            if not trade.isclosed:
                return

            if trade.pnlcomm >= 0:
                NETCOLOR = GREEN
            else:
                NETCOLOR = RED
            self.log(
                    '{}{} {:{}.{}} {} {} {} GROSS:{:>{},.0f} {} NET:{}{:>{},.0f}{} '.format(
                            'TRADE PROFIT'.ljust(self.col1_width , ' ') , self.delimiter ,
                            trade.data._name , self.col2_width , self.col2_width , self.delimiter ,
                            ' '.ljust(self.col3_width + 7) , self.delimiter ,
                            trade.pnl / 10 , self.col4_width - 1 , self.delimiter ,
                            NETCOLOR , trade.pnlcomm / 10 , self.col5_width + 1 , RESET ,
                    ).replace(',' , '/'))

    def save_result(self):
        fields = [int(self.final_balance / 10) , round(self.exposure , 2)]
        for param in self.params.__dict__:
            fields.append(self.params.__dict__[param])
        with open('../Strategies/RS_Pairs_FIX20/opt_result_temp.csv' , 'a' , newline='') as temp:
            writer = csv.writer(temp)
            writer.writerow(fields)

    def backtest_report(self):
        print_custom(self.row_end)

        print_custom('Strategy Settings:')
        width = 0
        for param in self.params.__dict__:
            if width < len(param):
                width = len(param)

        for param in self.params.__dict__:
            if param == 'signal_threshold':
                sign = ' %'
            else:
                sign = ''
            print_custom('{}{:<{}} = {}'.format(' ' * 15 , param , width , self.params.__dict__[param]) + sign)

        if self.show_time:
            print_custom(f'\nbacktest run time: {(self.time_end - self.time_start):.2f} seconds')

    def optimize_report(self , time_end):
        self.save_result()  # save variables to a temporary file
        # print the final balance for the given settings:
        txt = []
        for param in self.params.__dict__:
            txt.append('{} {:<{}} │ '.format(param , self.params.__dict__[param] , 3))
        txt.append('Final Balance: {:<12,.0f}'.format(self.broker.get_cash() / 10))
        if self.show_time:
            txt.append(f' time: {(self.time_end - self.time_start):.2f} s')
        print(''.join(txt).replace(',' , '/'))

    def stop(self):
        self.final_balance = round(self.broker.get_value() , 2)
        self.exposure = self.in_position / self.data.buflen() * 100
        self.time_end = time.time()

        if not self.optimize:
            self.backtest_report()
        else:
            self.optimize_report()


class backtest:
    balance = 1000000  # in Tomans
    input_list = '../../Lists/input_data/pairs.txt'
    data_path = '../Data/'
    start = '2010-01-01'
    end = '2020-01-01'
    show = []
    plot = True
    stdstats = True
    kwargs = {}

    def __init__(self , strategy):
        self.strategy = strategy
        self.cerebro = bt.Cerebro(cheat_on_open=True , stdstats=self.stdstats)
        # Add a strategy:
        self.cerebro.addstrategy(strategy)

        # load data:
        sd.add_cerebro_data(self.cerebro ,
                            input_list=self.input_list , data_path=self.data_path ,
                            start=self.start , end=self.end ,
                            add_fixincome=strategy.add_fixincome ,
                            show=self.show)

        self.cerebro.broker.setcash(self.balance * 10)
        self.cerebro.broker.set_checksubmit(checksubmit=False)
        self.cerebro.broker.set_coc(coc=True)

        # Add the new commissions scheme:
        self.cerebro.broker.setcommission(strategy.commission)
        if strategy.add_fixincome:
            self.cerebro.broker.setcommission(strategy.fix_income_commission , name='FIX_20%')

        previous_report = pathlib.Path('log.txt')
        if previous_report.is_file():
            os.remove('../Strategies/RS_RSI_Pairs_FIX20/log.txt')

        print_custom(
                '\nStarting Portfolio Value: {:,.0f}\n'.format(self.cerebro.broker.getvalue() / 10).replace("," , "/"))

        # Add the analyzers we are interested in:
        self.cerebro.addanalyzer(bt.analyzers.TradeAnalyzer , _name="ta")
        self.cerebro.addanalyzer(bt.analyzers.DrawDown , _name="dd")
        self.cerebro.addanalyzer(bt.analyzers.AnnualReturn , _name="ar")
        self.cerebro.addanalyzer(bt.analyzers.SharpeRatio , _name="shr")

        # Add the Observers we are interested in:
        self.cerebro.addobserver(bt.observers.DrawDown)

        # Add writer to save result in a csv file:
        # cerebro.addwriter(bt.WriterFile, csv=True, out='results.csv')

    def run(self):
        # Run over everything
        time1 = time.time()
        strategies = self.cerebro.run()
        firstStrat = strategies[0]
        time2 = time.time()
        if self.strategy.show_time:
            print_custom(f'\nCerebro run time: {time2 - time1:.2f} seconds')

        # print the analyzers
        TradeAnalysis(firstStrat.analyzers.ta.get_analysis() , firstStrat.analyzers.shr.get_analysis() , firstStrat)
        DrawDownAnalysis(firstStrat.analyzers.dd.get_analysis())
        annual_return_analysis(firstStrat.analyzers.ar.get_analysis())

        print_custom('\nFinal Portfolio Value: {:,.0f}'.format(self.cerebro.broker.getvalue() / 10).replace("," , "/"))

        # Plot the result
        if self.plot:
            self.cerebro.plot(style='candlestick' , rowsmajor=2 , rowsminor=1 , barup='#26a69a' , bardown='Orange' ,
                              volup='#c3e7d5' , voldown='#f8c1c6' , voltrans=1)


class optimize():
    balance = 1000000  # in Tomans
    input_list = '../../Lists/input_data/pairs.txt'
    data_path = '../Data/'
    start = '2010-01-01'
    end = '2020-01-01'
    kwargs = {}

    def __init__(self , strategy):

        self.cerebro = bt.Cerebro(cheat_on_open=True , maxcpus=None)

        # Add a strategy:
        self.cerebro.optstrategy(strategy , **self.kwargs)

        # load data:
        print('Loading Data into Cerebro...')
        t1 = time.time()
        sd.add_cerebro_data(self.cerebro ,
                            input_list=self.input_list , data_path=self.data_path ,
                            start=self.start , end=self.end ,
                            add_fixincome=strategy.add_fixincome)
        t2 = time.time()
        print(f'Data Loaded in {(t2 - t1):.2f} seconds')

        self.cerebro.broker.setcash(self.balance * 10)
        self.cerebro.broker.set_checksubmit(checksubmit=False)
        self.cerebro.broker.set_coc(coc=True)

        # Add the new commissions scheme:
        self.cerebro.broker.setcommission(strategy.commission)
        if strategy.add_fixincome:
            self.cerebro.broker.setcommission(strategy.fix_income_commission , name='FIX_20%')

        # Add the analyzers we are interested in
        self.cerebro.addanalyzer(bt.analyzers.TradeAnalyzer , _name="ta")
        self.cerebro.addanalyzer(bt.analyzers.DrawDown , _name="dd")
        self.current_name = self._get_name()

    def run(self):
        previous_report = pathlib.Path('opt_result_temp.csv')
        if previous_report.is_file():
            os.remove('../Strategies/RS_Pairs_FIX20/opt_result_temp.csv')

        print('\nStarting Portfolio Value: {:,.0f}\n'.format(self.cerebro.broker.getvalue() / 10).replace("," , "/"))

        # Run over everything:
        start_time = time.time()
        opt_runs = self.cerebro.run(stdstats=False , optreturn=True , optdatas=True)
        end_time = time.time()

        # Generate results list:
        df_file = pd.read_csv('../Strategies/RS_Pairs_FIX20/opt_result_temp.csv' , header=None)
        df_file = df_file.values.tolist()
        result = []
        save_count = 0
        for run in opt_runs:
            for strategy in run:
                # final_balance = int(strategy.final_balance / 10)
                # profit = int(final_balance - (self.balance / 10))
                # final_to_start = round(final_balance / self.balance , 2)
                # exposure = round(strategy.exposure , 2)
                drawdown = round(strategy.analyzers.dd.get_analysis().max.drawdown , 2)
                drawdown_length = strategy.analyzers.dd.get_analysis().max.len
                total_positions = round(strategy.analyzers.ta.get_analysis().total.closed , 2)
                total_won = strategy.analyzers.ta.get_analysis().won.total
                total_lost = strategy.analyzers.ta.get_analysis().lost.total
                win_rate = round((total_won / total_positions) * 100 , 2)
                win_streak = strategy.analyzers.ta.get_analysis().streak.won.longest
                lose_streak = strategy.analyzers.ta.get_analysis().streak.lost.longest

                params = []
                for param in strategy.params.__dict__:
                    params.append(strategy.params.__dict__[param])

                from_temp = [-1 , -1]
                for i , row in enumerate(df_file):
                    if row[2:] == params:
                        from_temp = row[0:2]
                        del df_file[i]

                final_balance = from_temp[0]
                profit = int(final_balance - (self.balance / 10))
                final_to_start = round(final_balance / self.balance , 2)
                exposure = round(from_temp[1] , 2)

                result.append([
                                  final_to_start ,
                                  profit ,
                                  final_balance ,
                                  exposure ,
                                  drawdown ,
                                  drawdown_length ,
                                  total_positions ,
                                  total_won ,
                                  total_lost ,
                                  win_rate ,
                                  win_streak ,
                                  lose_streak
                              ] + params)
            save_count += 1

        print(f'\nnumber of conditions: {save_count}')
        print('Elapsed time: ' + str(round(end_time - start_time , 2)) + ' seconds')

        # save result to a csv file:
        header = []
        for param in opt_runs[0][0].params.__dict__:
            header.append(param)
        header = [
                     'Final/Start' ,
                     'Profit' ,
                     'Final_Balance' ,
                     'Exposure' ,
                     'Max_Drawdown' ,
                     'Max_Drawdown_Length' ,
                     'Total_Positions' ,
                     'Total_Won' ,
                     'Total_Lost' ,
                     'Win_Rate' ,
                     'Win_Streak' ,
                     'Lose_Streak'
                 ] + header
        sd.csvw(file_name=self.current_name , data=result , header=header)
        os.remove('../Strategies/RS_Pairs_FIX20/opt_result_temp.csv')

    def _get_name(self):
        return self.__class__.__name__


# +---------------------------------------------------------------------------+
# | Analyzers:                                                                |
# +---------------------------------------------------------------------------+
def TradeAnalysis(trade_analyzer , sharp_ratio , strategy):
    '''
    Function to print the Technical Analysis results in a nice format.
    '''
    # Get the results we are interested in
    total_open = trade_analyzer.total.open
    total_closed = trade_analyzer.total.closed
    total_won = trade_analyzer.won.total
    total_lost = trade_analyzer.lost.total
    win_streak = trade_analyzer.streak.won.longest
    lose_streak = trade_analyzer.streak.lost.longest
    pnl_net = int(trade_analyzer.pnl.net.total / 10)
    strike_rate = round((total_won / total_closed) * 100 , 2)
    exposure = round(strategy.exposure , 2)
    shr = round(sharp_ratio['sharperatio'] , 2)

    # Designate the rows
    h1 = ['Total Open' , 'Total Closed' , 'Total Won' , 'Total Lost']
    h2 = ['Win Rate(%)' , 'Win Streak' , 'Losing Streak' , 'PnL Net']
    h3 = ['Exposure(%)' , 'Sharp Ratio' , '' , '']
    r1 = [total_open , total_closed , total_won , total_lost]
    r2 = [strike_rate , win_streak , lose_streak , pnl_net]
    r3 = [exposure , shr]

    # Print the rows
    print_list = [h1 , r1 , h2 , r2 , h3 , r3]
    print_custom('\nTrade Analysis:')
    for i , row in enumerate(print_list):
        if i % 2 == 0:
            row_format = '{:<15}' * (len(row) + 1)
            print_custom(row_format.format('' , *row))
        else:
            row_format = '{:<15,}' * len(row)
            print_custom(' ' * 15 + row_format.format(*row).replace(',' , '/'))
            if i != len(print_list) - 1:
                print_custom()


def DrawDownAnalysis(analyzer):
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
    # h1 = ['Drawdown' , 'Moneydown' , 'Length']
    h2 = ['Max DD(%)' , 'Max DD value' , 'Max DD length']
    r1 = [drawdown , moneydown , length]
    r2 = [max_dd , max_md , max_len]
    print_list = [h2 , r2]
    print_custom('\nDrawdown Analysis:')
    for i , row in enumerate(print_list):
        if i % 2 == 0:
            row_format = '{:<15}' * (len(row) + 1)
            print_custom(row_format.format('' , *row))
        else:
            row_format = '{:<15,}' * len(row)
            print_custom(' ' * 15 + row_format.format(*row).replace(',' , '/'))


def annual_return_analysis(analyzer):
    print_custom('\nAnnual Returns:')
    for year , ret in analyzer.items():
        print_custom(' ' * 15 + f'{year}: {ret * 100:+.2f} %')
