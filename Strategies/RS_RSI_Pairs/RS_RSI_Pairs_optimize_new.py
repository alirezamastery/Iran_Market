import os
import sys  # To find out the script name (in argv[0])

os.chdir(os.path.dirname(sys.argv[0]))
sys.path.append(os.path.abspath('../../Modules'))

import math as sys_math
import templates


class RS_RSI_Pairs(templates.RS_base):
    optimize = True
    ispairs = True
    data_range_start = 0
    RSI = True
    add_fixincome = False

    params = (
        ('portfo' , 10) ,
        ('ma_period' , 200) ,
        ('signal_threshold' , 5) ,
        ('rsi_period' , 14) ,
        ('rsi_buy_level' , 70) ,
        ('rsi_sell_level' , 50) ,
        ('rsi_above_days' , 0) ,
    )

    def __init__(self):
        super().__init__()
        self.portfo = self.params.portfo
        self.rsi_period = self.params.rsi_period
        self.s_th = (self.params.signal_threshold / 100) + 1

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
        for i in range(self.data_range_start , self.range , 2):
            if self.inds[i]['RS'].MA[0] * self.s_th < self.inds[i]['RS'].RS[0]:
                self.prs[i]['signal'] = [i , self.datas[i]._name]
                self.prs[i]['close'] = [i + 1 , self.datas[i + 1]._name]
                self.prs[i]['donothing'] = False
            elif self.inds[i]['RS'].MA[0] > self.inds[i]['RS'].RS[0] * self.s_th:
                self.prs[i]['signal'] = [i + 1 , self.datas[i + 1]._name]
                self.prs[i]['close'] = [i , self.datas[i]._name]
                self.prs[i]['donothing'] = False
            else:
                self.prs[i]['donothing'] = True

        # open positions:
        for i in range(self.data_range_start , self.range , 2):
            if self.prs[i]['signal'] != self.prs[i]['pos'] and self.prs[i]['per'] and not self.prs[i]['donothing'] and \
                    self.inds[self.prs[i]['signal'][0]]['RSI'][0] > self.params.rsi_buy_level:
                # check how many days RSI was above by level:
                above_days = True
                for j in range(0 , self.params.rsi_above_days):
                    if self.inds[self.prs[i]['signal'][0]]['RSI'].rsi[-j] < self.params.rsi_buy_level:
                        above_days = False
                        break
                # if every condition was met add the symbol to irs:
                if above_days:
                    number = self.prs[i]['signal'][0]
                    name = self.prs[i]['signal'][1]
                    comm_adj_price = self.datas[number].close[0] * (1 + (comm * 1))
                    comm_adj_size = sizes / comm_adj_price
                    size = sys_math.floor(comm_adj_size)
                    self.order = self.buy(data=self.datas[number] , size=size)
                    self.prs[i]['pf'] = True
                    self.log_buy(data_index=number , size=size)
                    self.sym_count_o += 1
                    self.prs[i]['pos'] = [number , name]
                    self.prs[i]['per'] = False

        # close signals:
        for i in range(self.data_range_start , self.range , 2):
            if self.prs[i]['close'] == self.prs[i]['pos'] and not self.prs[i]['donothing'] and \
                    self.inds[self.prs[i]['signal'][0]]['RSI'][0] > self.params.rsi_buy_level:
                number = self.prs[i]['close'][0]
                name = self.prs[i]['close'][1]
                self.order = self.close(data=self.datas[number])
                self.log_sell(data_index=number)
                self.prs[i]['pf'] = False
                self.prs[i]['per'] = True
                self.prs[i]['pos'] = [None , None]
                self.sym_count_o -= 1


class RS_RSI_Pairs_optimize(templates.optimize):
    start = '2010-01-01'
    end = '2020-01-01'
    kwargs = {'ma_period':        range(30 , 400 , 10) ,
              # 'signal_threshold': range(0 , 5 , 2) ,
              'rsi_period':       range(5 , 50 , 2) ,
              'rsi_buy_level':    range(60 , 80 , 5) ,
              'rsi_sell_level':   range(60 , 80 , 5) ,
              'rsi_above_days':   range(0 , 2 , 1)
              }

    input_list = '../../Lists/input_data/different_industries.txt'


if __name__ == '__main__':
    test = RS_RSI_Pairs_optimize(strategy=RS_RSI_Pairs)
    test.run()
