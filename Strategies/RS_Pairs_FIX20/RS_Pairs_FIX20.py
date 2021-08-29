import os
import sys  # To find out the script name (in argv[0])

os.chdir(os.path.dirname(sys.argv[0]))
sys.path.append(os.path.abspath('../../Modules'))

import templates
import our_indicators as oind



class RS_Pairs_FIX20(templates.RS_base):
    optimize = False
    ispairs = True
    commission = 0.01
    fix_income_commission = 0.0001
    add_fixincome = True
    data_range_start = 1
    RSI = False

    params = (
        ('portfo' , 5) ,
        ('ma_period' , 280) ,
        ('signal_threshold' , 3) ,
        ('fix_ma_period' , 61) ,
    )

    def next_open(self):
        if self.sym_count_o > self.portfo:
            print('*' * 50)
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

        # conditions:
        for i in range(self.data_range_start , self.range , 2):
            self.conditions[i]['numerator'] = self.inds[i]['RS'].MA[0] * self.s_th < self.inds[i]['RS'].RS[0] and \
                                              self.inds[i]['RS_fix20'].RS[0] > self.inds[i]['RS_fix20'].MA[
                                                  0] * self.s_th
            self.conditions[i]['denominator'] = self.inds[i]['RS'].MA[0] > self.inds[i]['RS'].RS[0] * self.s_th and \
                                                self.inds[i + 1]['RS_fix20'].RS[0] > self.inds[i + 1]['RS_fix20'].MA[
                                                    0] * self.s_th
            self.conditions[i]['fix_income'] = not self.conditions[i]['numerator'] and \
                                               not self.conditions[i]['denominator']

        # check conditions for each symbol:
        for i in range(self.data_range_start , self.range , 2):
            if self.prs[i]['permission']:

                if self.conditions[i]['numerator']:
                    self.prs[i]['signal'] = [i , self.datas[i]._name]
                    self.prs[i]['new_signal'] = True
                    self.prs[i]['condition'] = 'numerator'

                elif self.conditions[i]['denominator']:
                    self.prs[i]['signal'] = [i + 1 , self.datas[i + 1]._name]
                    self.prs[i]['new_signal'] = True
                    self.prs[i]['condition'] = 'denominator'

                else:
                    self.prs[i]['signal'] = [0 , self.datas[0]._name]
                    self.prs[i]['new_signal'] = True
                    self.prs[i]['condition'] = 'fix_income'

        # open positions:
        for i in range(self.data_range_start , self.range , 2):
            if self.prs[i]['permission'] and self.prs[i]['signal'] != self.prs[i]['pos']:
                number = self.prs[i]['signal'][0]
                name = self.prs[i]['signal'][1]
                if number == 0:
                    comm = self.fix_income_commission
                else:
                    comm = self.commission
                comm_adj_price = self.datas[number].close[0] * (1 + (comm * 1))
                self.prs[i]['size'] = self.sizes // comm_adj_price
                self.order = self.buy(data=self.datas[number] , size=self.prs[i]['size'])
                self.prs[i]['position'] = [number , name]
                self.prs[i]['permission'] = False
                self.prs[i]['new_signal'] = False
                self.sym_count_o += 1
                self.log_buy(data_index=number , size=self.prs[i]['size'])

        # close signals:
        for i in range(self.data_range_start , self.range , 2):
            if not self.conditions[i][self.prs[i]['condition']]:
                number = self.prs[i]['position'][0]
                name = self.prs[i]['position'][1]
                self.order = self.sell(data=self.datas[number] , size=self.prs[i]['size'])
                self.prs[i]['permission'] = True
                self.prs[i]['position'] = [None , None]
                self.sym_count_o -= 1
                self.log_sell(data_index=number)


class RS_Pairs_FIX20_backtest(templates.backtest):
    plot = True
    show = ['FIX_20%']
    start = '2010-01-01'
    end = '2020-01-01'
    input_list = '../../Lists/input_data/different_industries.txt'


if __name__ == '__main__':
    test = RS_Pairs_FIX20_backtest(strategy=RS_Pairs_FIX20)
    test.run()
