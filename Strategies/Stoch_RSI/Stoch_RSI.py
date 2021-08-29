import os
import sys  # To find out the script name (in argv[0])

os.chdir(os.path.dirname(sys.argv[0]))
sys.path.append(os.path.abspath('../../Modules'))
import math as sys_math
import backtrader as bt
import backtrader.indicators as btind
import backtrader.mathsupport as math
import our_indicators as oind
import ctypes
import templates


class Stoch_RSI(templates.Generic_Template):
    optimize = True
    fill_blanks = True
    data_range_start = 0
    params = (
        ('portfo' , 24) ,
        ('signal_threshold' , 2) ,
        ('RSI_Length' , 22) ,
        ('Stochastic_Length' , 24) ,
        ('upperband' , 80) ,
        ('lowerband' , 20) ,
    )

    def __init__(self):
        super().__init__()
        self.portfo = self.params.portfo
        self.s_th = (self.params.signal_threshold / 100) + 1

        self.range = self.data_range_start + self.portfo
        self.portfo_flag = [False for _ in range(len(self.datas))]
        self.irs = list()
        self.inds = dict()
        for i in range(self.data_range_start , self.range):
            self.inds[i] = dict()
            self.inds[i]['stoch_rsi'] = oind.Stoch_RSI(self.datas[i] ,
                                                       RSI_Length=self.params.RSI_Length ,
                                                       Stochastic_Length=self.params.Stochastic_Length)
            self.inds[i]['RSI'] = btind.RSI_Safe(self.datas[i] , period=self.params.RSI_Length)

    def next_open(self):

        # check conditions:
        self.irs = []
        for i in range(self.data_range_start , self.range):
            # open:
            if not self.portfo_flag[i] and self.inds[i]['stoch_rsi'].K[0] > 20 >= self.inds[i]['stoch_rsi'].K[-1] \
                    and self.inds[i]['stoch_rsi'].K[-2] < 20 and self.inds[i]['stoch_rsi'].K[-3] < 20:
                self.portfo_flag[i] = True
                comm_adj_price = self.datas[i].close[0] * (1 + self.commission)
                size = self.sizes // comm_adj_price
                self.order = self.buy(data=self.datas[i] , size=size)
                self.log_buy(data_index=i , size=size)
            # close:
            if self.portfo_flag[i] and self.inds[i]['stoch_rsi'].K[0] < 80 <= self.inds[i]['stoch_rsi'].K[-1]:
                self.portfo_flag[i] = False
                self.order = self.close(data=self.datas[i])
                self.log_sell(data_index=i)


START = '2018-01-01'
END = '2020-10-01'


class Stoch_RSI_backtest(templates.backtest):
    plot = True
    start = START
    end = END
    show = ['FEMELI']
    input_list = '../../Lists/input_data/stoch_rsi.txt'
    data_path = '../../Data/all/'
    balance = 1_000_000
    stdstats = True


class optimizer(templates.optimize):
    start = START
    end = END
    kwargs = {'Stochastic_Length': range(10 , 30 , 1) ,
              'RSI_Length':        range(10 , 30 , 1) ,
              # 'rsi_period':    range(5 , 50 , 2) ,
              }
    input_list = '../../Lists/input_data/stoch_rsi.txt'
    data_path = '../../Data/all/'


if __name__ == '__main__':
    if Stoch_RSI.optimize:
        test = optimizer(strategy=Stoch_RSI)
        test.run()
    else:
        test = Stoch_RSI_backtest(strategy=Stoch_RSI)
        test.run()
