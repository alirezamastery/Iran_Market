import os
import sys  # To find out the script name (in argv[0])

os.chdir(os.path.dirname(sys.argv[0]))
sys.path.append(os.path.abspath('../../Modules'))

import templates
import backtrader as bt


class RS_ichi(templates.RS_base):
    optimize = False
    ispairs = True
    RSI = True
    add_fixincome = True
    data_range_start = 0

    params = (
        ('portfo' , 10) ,
        ('ma_period' , 55) ,
        ('signal_threshold' , 2) ,
        ('fix_ma_period' , 34) ,
        ('rsi_period' , 14) ,
        ('rsi_buy_level' , 70) ,
        ('rsi_sell_level' , 70) ,
        ('rsi_above_days' , 0) ,
    )

    def __init__(self):
        super().__init__()
        for i in range(self.data_range_start , self.range):
            self.inds[i]['ichi'] = bt.indicators.Ichimoku()

    def next_open(self):
        if not self.on_open():
            return

        # conditions:
        for i in range(self.data_range_start , self.range , 2):
            # check numerator:
            self.conditions[i]['numerator'] = \
                self.inds[i]['RS'].MA[0] * self.s_th < self.inds[i]['RS'].RS[0] and \
                self.inds[i]['RSI'] > self.params.rsi_buy_level and \
                self.inds[i]['RS_fix20'].RS[0] > self.inds[i]['RS_fix20'].MA[0] * self.s_th and \
                self.inds[i]['ichi'].tenkan_sen[0] > self.inds[i]['ichi'].kijun_sen[0]
            # check how many days RSI was above by level:
            above_days_num = True
            for j in range(0 , self.params.rsi_above_days + 1):
                if self.inds[i]['RSI'].rsi[-j] < self.params.rsi_buy_level:
                    above_days_num = False
                    break
            self.conditions[i]['numerator'] &= above_days_num

            # check denominator:
            self.conditions[i]['denominator'] = \
                self.inds[i]['RS'].MA[0] > self.inds[i]['RS'].RS[0] * self.s_th and \
                self.inds[i + 1]['RSI'] > self.params.rsi_buy_level and \
                self.inds[i + 1]['RS_fix20'].RS[0] > self.inds[i + 1]['RS_fix20'].MA[0] * self.s_th and \
                self.inds[i + 1]['ichi'].tenkan_sen[0] > self.inds[i + 1]['ichi'].kijun_sen[0]
            above_days_denom = True
            for j in range(0 , self.params.rsi_above_days + 1):
                if self.inds[i + 1]['RSI'].rsi[-j] < self.params.rsi_buy_level:
                    above_days_denom = False
                    break
            self.conditions[i]['denominator'] &= above_days_denom

            # if neither numerator nor denominator then fix income:
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

                elif self.conditions[i]['fix_income']:
                    self.prs[i]['signal'] = [0 , self.datas[0]._name]
                    self.prs[i]['new_signal'] = True
                    self.prs[i]['condition'] = 'fix_income'
                else:
                    raise RuntimeError(f'none of the conditions was true. pair: '
                                       f'{self.datas[i]._name} and {self.datas[i + 1]._name} ')

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


class RS_ichi_backtest(templates.backtest):
    # show = ['FIX_20%' , 'FEOLAD' , 'REMAPNA']
    input_list = '../../Lists/input_data/different_industries.txt'


if __name__ == '__main__':
    test = RS_ichi_backtest(strategy=RS_ichi)
    test.run()
