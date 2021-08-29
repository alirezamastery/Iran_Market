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
import time


# HH data keys:
# DATE_JALALI
# BUYERS_IND
# BUYERS_CORP
# SELLERS_IND
# SELLERS_CORP
# VOL_BUY_IND
# VOL_BUY_IND_%
# VOL_BUY_CORP
# VOL_BUY_CORP_%
# VOL_SELL_IND
# VOL_SELL_IND_%
# VOL_SELL_CORP
# VOL_SELL_CORP_%
# VALUE_BUY_IND
# VALUE_BUY_CORP
# VALUE_SELL_IND
# VALUE_SELL_CORP
# AVRG_PRICE_BUY_IND
# AVRG_PRICE_BUY_CORP
# AVRG_PRICE_SELL_IND
# AVRG_PRICE_SELL_CORP
# CORP_TO_IND

class comb_test(templates.Generic_Template):
    combined_data = True
    optimize = False
    fill_blanks = False
    data_range_start = 0
    analyze_SharpeRatio = True
    analyze_AnnualReturn = True
    commission = 0.01
    params = (
        ('portfo' , 1) ,
        ('signal_threshold' , 2) ,
        ('movav_tse' , 34) ,
        ('intel_ma_period' , 34) ,
        ('RSI_Length_open' , 23) ,
        ('RSI_Length_close' , 34) ,
        ('Stochastic_Length_open' , 23) ,
        ('Stochastic_Length_close' , 34) ,
    )

    def __init__(self):
        super().__init__()
        self.portfo = self.params.portfo
        self.s_th = (self.params.signal_threshold / 100) + 1

        self.range = self.data_range_start + self.portfo
        self.portfo_flag = [False for _ in range(len(self.datas))]
        self.irs = list()
        self.inds = dict()
        self.ordered = False

        for i in range(self.data_range_start , self.range):
            self.inds[i] = dict()
            # self.inds[i]['VOL_BUY_IND'] = btind.MovingAverageSimple(self.datas[i].VOL_BUY_IND , period=1 ,
            #                                                         subplot=True ,
            #                                                         plotname='VOL_BUY_IND')
            # self.inds[i]['VOLUME'] = btind.MovingAverageSimple(self.datas[i].volume , period=1 ,
            #                                                    _method='bar',
            #                                                    subplot=True ,
            #                                                    plotname='VOLUME')
            self.inds[i]['stoch_rsi_open'] = oind.Stoch_RSI(self.datas[i] ,
                                                            RSI_Length=self.params.RSI_Length_open ,
                                                            Stochastic_Length=self.params.Stochastic_Length_open ,
                                                            plotname='stoch_rsi_open',
                                                            plot=True)
            self.inds[i]['stoch_rsi_close'] = oind.Stoch_RSI(self.datas[i] ,
                                                             RSI_Length=self.params.RSI_Length_close ,
                                                             Stochastic_Length=self.params.Stochastic_Length_close ,
                                                             plotname='stoch_rsi_close',
                                                             plot=False)
            self.inds[i]['int_money_buy'] = oind.Int_Money_buy(self.datas[i] ,
                                                               vol_ma_period=14 ,
                                                               intel_ma_period=self.params.intel_ma_period ,
                                                               subplot=True ,
                                                               plotname='intelligent money buy')
        self.opened = False

    def next_open(self):
        # super().next_open()

        # if not self.opened:
        #     comm_adj_price = self.datas[0].close[0] * (1 + self.commission)
        #     comm_adj_size = self.sizes / comm_adj_price
        #     size = sys_math.floor(comm_adj_size)
        #     self.order = self.buy(data=self.datas[0] , size=size)
        #     self.log_buy(data_index=0 , size=size)
        #     self.opened = True

        # check conditions:
        for i in range(self.data_range_start , self.range):
            # open:
            if self.inds[i]['stoch_rsi_open'].K[0] > 20 >= self.inds[i]['stoch_rsi_open'].K[-1] \
                    and not self.portfo_flag[i]:
                # print(self.inds[i]['int_money_buy'].intel[0],self.inds[i]['stoch_rsi_open'].K[0])
                self.portfo_flag[i] = True
                comm_adj_price = self.datas[i].close[0] * (1 + self.commission)
                comm_adj_size = self.sizes / comm_adj_price
                size = sys_math.floor(comm_adj_size)
                self.order = self.buy(data=self.datas[i] , size=size)
                self.log_buy(data_index=i , size=size)
            # close:
            if self.inds[i]['stoch_rsi_open'].K[0] < 80 <= self.inds[i]['stoch_rsi_open'].K[-1] \
                    and self.portfo_flag[i]:
                self.portfo_flag[i] = False
                self.order = self.close(data=self.datas[i])
                self.log_sell(data_index=i)


class tester(templates.backtest):
    plot = True
    stdstats = False
    start = '2019-09-16'
    end = '2020-09-16'
    show = ['FEMELI']
    input_list = '../../Lists/input_data/combined_test.txt'
    # data_path = '../../Data/all/'


class optimizer(templates.optimize):
    kwargs = {'RSI_Length_open': range(10 , 200 , 5) ,
              # 'fix_ma_period': range(1 , 300 , 10) ,
              # 'rsi_period':    range(5 , 50 , 2) ,
              }
    input_list = '../../Lists/input_data/combined_test.txt'
    data_path = '../../Data/selected/'


if __name__ == '__main__':
    print(comb_test.__mro__)
    if comb_test.optimize:
        test = optimizer(strategy=comb_test)
        test.run()
    else:
        test = tester(strategy=comb_test)
        test.run()
