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


class Stoch_RSI_double(templates.Generic_Template):
    optimize = True
    fill_blanks = True
    data_range_start = 0
    params = (
        ('portfo' , 10) ,
        ('signal_threshold' , 2) ,
        ('RSI_Length_open' , 34) ,
        ('RSI_Length_close' , 90) ,
        ('Stochastic_Length_open' , 34) ,
        ('Stochastic_Length_close' , 200) ,
        ('upperband_open' , 80) ,
        ('lowerband_open' , 20) ,
        ('upperband_close' , 80) ,
        ('lowerband_close' , 20) ,
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
            self.inds[i]['stoch_rsi_open'] = oind.Stoch_RSI(self.datas[i] ,
                                                            RSI_Length=self.params.RSI_Length_open ,
                                                            Stochastic_Length=self.params.Stochastic_Length_open ,
                                                            plotname='stoch_rsi_open')
            self.inds[i]['stoch_rsi_close'] = oind.Stoch_RSI(self.datas[i] ,
                                                             RSI_Length=self.params.RSI_Length_close ,
                                                             Stochastic_Length=self.params.Stochastic_Length_close ,
                                                             plotname='stoch_rsi_close')
            # self.inds[i]['RSI'] = btind.RSI_Safe(self.datas[i] , period=self.params.RSI_Length)

    def next_open(self):

        # check conditions:
        for i in range(self.data_range_start , self.range):
            # open:
            if self.inds[i]['stoch_rsi_open'].K[0] > 20 >= self.inds[i]['stoch_rsi_open'].K[-1] \
                    and not self.portfo_flag[i] \
                    and self.inds[i]['stoch_rsi_open'].K[-2] < 20 and self.inds[i]['stoch_rsi_open'].K[-3] < 20:
                self.portfo_flag[i] = True
                comm_adj_price = self.datas[i].close[0] * (1 + (self.commission * 1))
                comm_adj_size = self.sizes / comm_adj_price
                size = sys_math.floor(comm_adj_size)
                self.order = self.buy(data=self.datas[i] , size=size)
                self.log_buy(data_index=i , size=size)
            # close:
            if self.inds[i]['stoch_rsi_close'].K[0] < 80 <= self.inds[i]['stoch_rsi_close'].K[-1] \
                    and self.portfo_flag[i]:
                self.portfo_flag[i] = False
                self.order = self.close(data=self.datas[i])
                self.log_sell(data_index=i)


class Stoch_RSI_backtest(templates.backtest):
    plot = True
    start = '2018-01-01'
    end = '2020-06-01'
    show = ['DEY']
    input_list = '../../Lists/input_data/stoch_rsi.txt'
    # data_path = '../../Data/all/'


class optimizer(templates.optimize):
    kwargs = {'RSI_Length_open': range(10 , 200 , 5) ,
              'RSI_Length_close': range(1 , 300 , 10) ,
              # 'rsi_period':    range(5 , 50 , 2) ,
              }
    input_list = '../../Lists/input_data/stoch_rsi.txt'
    data_path = '../../Data/all/'
    maxcpus = 15


if __name__ == '__main__':
    if Stoch_RSI_double.optimize:
        test = optimizer(strategy=Stoch_RSI_double)
        test.run()
    else:
        test = Stoch_RSI_backtest(strategy=Stoch_RSI_double)
        test.run()
