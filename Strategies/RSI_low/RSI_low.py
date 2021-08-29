import os
import sys  # To find out the script name (in argv[0])

os.chdir(os.path.dirname(sys.argv[0]))
sys.path.append(os.path.abspath('../../Modules'))

import backtrader as bt
import our_indicators as oind
import templates
import math as sys_math


class RSI_RS(templates.RS_base):
    RSI = True
    add_fixincome = False

    params = (
        ('portfo' , 5) ,
        ('ma_period' , 200) ,
        ('RS_min' , 100) ,
        ('signal_threshold' , 1) ,
        ('RS_max_switch' , True) ,
        ('rsi_period' , 14) ,
        ('rsi_buy_level' , 40) ,
        ('rsi_sell_level' , 70) ,
        ('rsi_above_days' , 1) ,
    )

    def __init__(self):
        super().__init__()
        self.portfo = self.params.portfo
        self.RS_min = self.params.RS_min
        self.rsi_period = self.params.rsi_period
        self.s_th = (self.params.signal_threshold / 100) + 1

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
        # check conditions:
        self.irs = []
        for i , d in enumerate(self.datas):
            if d._name == 'TEPIX':
                pass
            # ----------------------------------------------------------------------------------------
            # if RS_max_switch == True:
            elif self.params.RS_max_switch and self.inds[d]['RS'].MA[0] * self.s_th < self.inds[d]['RS'].RS[0] and \
                    self.inds[d]['RSI'].rsi[0] > self.params.rsi_buy_level >= self.inds[d]['RSI'].rsi[-1] and \
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
                self.log_buy(data_index=sym[0] , size=size)
                self.sym_count_o += 1

        # close signals:
        for i , data in enumerate(self.position_flag):
            if data[2] and self.inds[self.datas[data[0]]]['RSI'].rsi[0] < self.params.rsi_sell_level < \
                    self.inds[self.datas[data[0]]]['RSI'].rsi[-1]:
                self.log_sell(data_index=data[0])
                self.order = self.close(data=self.datas[data[0]])
                self.position_flag[i][2] = False
                self.sym_count_o -= 1


class RS_backtest(templates.backtest):
    plot = True
    end = '2020-04-20'
    show = ['TEPIX']
    input_list = '../../Lists/input_data/pairs.txt'


if __name__ == '__main__':
    test = RS_backtest(strategy=RSI_RS)
    test.run()
