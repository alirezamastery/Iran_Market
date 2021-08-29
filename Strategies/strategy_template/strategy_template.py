from __future__ import (absolute_import , division , print_function , unicode_literals)
import os
import sys  # To find out the script name (in argv[0])
import symdata as sd
import math as sys_math
import backtrader as bt
import backtrader.indicators as btind
import backtrader.mathsupport as math
import our_indicators as oind
import ctypes
import templates as tp

# os.chdir(os.path.dirname(sys.argv[0]))
# sys.path.append(os.path.abspath('../../Modules'))

kernel32 = ctypes.windll.kernel32
kernel32.SetConsoleMode(kernel32.GetStdHandle(-11) , 7)

FRAME = '\033[0m'
RESET = '\033[0m'
UNDERLINE = '\033[4m'


class RSI_RS(tp.RS_base):
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
            # ----------------------------------------------------------------------------------------
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
            # ----------------------------------------------------------------------------------------
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


class RS_backtest(tp.backtest):
    plot = False
    end = '2020-01-01'

    def __init__(self , strategy):
        super().__init__(strategy)


if __name__ == '__main__':
    RS_backtest(strategy=RSI_RS)
