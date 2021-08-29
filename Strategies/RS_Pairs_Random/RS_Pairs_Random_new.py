import os
import sys  # To find out the script name (in argv[0])
import math

os.chdir(os.path.dirname(sys.argv[0]))
sys.path.append(os.path.abspath('../../Modules'))

import templates


class RS_Pairs_Random(templates.RS_base):
    optimize = False
    ispairs = True
    RSI = False
    add_fixincome = False
    data_range_start = 0

    params = (
        ('portfo' , 1) ,
        ('ma_period' , 350) ,
        ('signal_threshold' , 8)
    )

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
        self.sizes = -1
        if self.portfo > self.sym_count_o:
            self.sizes = self.broker.get_cash() // (self.portfo - self.sym_count_o)
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
            if self.prs[i]['signal'] != self.prs[i]['pos'] and self.prs[i]['per'] and not self.prs[i]['donothing']:
                number = self.prs[i]['signal'][0]
                name = self.prs[i]['signal'][1]
                comm_adj_price = self.datas[number].close[0] * (1 + (comm * 1))
                comm_adj_size = self.sizes / comm_adj_price
                size = math.floor(comm_adj_size)
                self.order = self.buy(data=self.datas[number] , size=size)
                self.prs[i]['pf'] = True
                self.log_buy(data_index=number , size=size)
                self.sym_count_o += 1
                self.prs[i]['pos'] = [number , name]
                self.prs[i]['per'] = False

        # close signals:
        for i in range(self.data_range_start , self.range , 2):
            if self.prs[i]['close'] == self.prs[i]['pos'] and not self.prs[i]['donothing']:
                number = self.prs[i]['close'][0]
                name = self.prs[i]['close'][1]
                self.order = self.close(data=self.datas[number])
                self.log_sell(data_index=number)
                self.prs[i]['pf'] = False
                self.prs[i]['per'] = True
                self.prs[i]['pos'] = [None , None]
                self.sym_count_o -= 1


class RS_Pairs_Random_backtest(templates.backtest):
    show = ['FEOLAD' , 'REMAPNA']
    input_list = '../../Lists/input_data/different_industries.txt'


if __name__ == '__main__':
    test = RS_Pairs_Random_backtest(strategy=RS_Pairs_Random)
    test.run()
