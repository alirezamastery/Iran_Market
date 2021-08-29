from __future__ import (absolute_import , division , print_function ,
                        unicode_literals)
import os.path  # To manage paths
import sys  # To find out the script name (in argv[0)]
import time
import numpy as np
import pandas
import symdata as sd
import datetime as dt
import matplotlib.pyplot as plt
import math as sys_math
import backtrader as bt
import backtrader.indicators as btind
import backtrader.mathsupport as math


# RS Indicator
class RSInd(bt.Indicator):
    lines = ('RS' , 'MA' ,)
    params = (('ma_period' , 34) ,)

    def __init__(self):
        self.lines.RS = self.datas[1].close / self.datas[0].close
        self.lines.MA = btind.MovingAverageSimple(self.lines.RS , period=self.params.ma_period)


class RSInd_100(bt.Indicator):
    lines = ('RS' , 'MA' ,)
    params = (('ma_period' , 34) ,)

    def __init__(self):
        # datas[1] in TEPIX_D and datas[0] is the symbol
        RS_raw = self.datas[0].close / self.datas[1].close
        ratio = self.datas[1].close[1] * 100 / self.datas[0].close[1]
        self.lines.RS = RS_raw * ratio
        self.lines.MA = btind.MovingAverageSimple(self.lines.RS , period=self.params.ma_period)



class maxRiskSizer(bt.Sizer):
    params = (('risk' , 0.9) ,)

    def __init__(self):
        if self.p.risk > 1 or self.p.risk < 0:
            raise ValueError('The risk parameter is a percentage which must be between 0 and 1')

    def _getsizing(self , comminfo , cash , data , isbuy):
        if isbuy == True:
            size = sys_math.floor((cash * self.p.risk) / data[0])
            # print('size: %s' % size)
            # print('margin: %s' % cash)

        else:
            size = sys_math.floor((cash * self.p.risk) / data[0]) * -1
        return size



# Create a Stratey
class TestStrategy(bt.Strategy):
    params = (
        ('ma_period' , 34) ,
    )

    def log(self , txt , dt=None):
        pass
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[1].datetime.date(0)
        print('%s, %s' % (dt.isoformat() , txt))

    def __init__(self):
        pass



    def next_open(self):
        pass



    def stop(self):

        self.log('(MA Period %2d) Ending Value %.2f' % (self.params.ma_period , self.broker.getvalue()))

        self.value = round(self.broker.get_value() , 2)


if __name__ == '__main__':
    cerebro = bt.Cerebro(optreturn=False , cheat_on_open=True)

    # Add sizer:
    cerebro.addsizer(maxRiskSizer)

    # load data
    sd.add_cerebro_data(cerebro , start='2010-01-01')

    # optimize a strategy
    strats = cerebro.optstrategy(TestStrategy , ma_period=range(34 , 340))

    startcash = 1000000
    cerebro.broker.setcash(startcash)

    # Add a FixedSize sizer according to the stake
    # cerebro.addsizer(bt.sizers.FixedSize , stake=10)

    # cerebro.broker.set_coo(coo=True)
    cerebro.broker.set_coc(coc=True)

    # Set the commission - 0.1% ... divide by 100 to remove the %
    cerebro.broker.setcommission(commission=0.01)

    start_time = time.time()

    # opt_runs = cerebro.run(maxcpus=1)
    opt_runs = cerebro.run(stdstats=False)

    end_time = time.time()
    print('\nElapsed time: ' + str(round(end_time - start_time , 2)) + ' seconds')


    # Generate results list
    final_results_list = []
    profit = []
    ma_period = []
    RS_min = []
    for run in opt_runs:
        for strategy in run:
            value = strategy.value
            profit.append(value)
            PnL = round(value - startcash , 2)
            period = strategy.params.ma_period
            ma_period.append(period)
            rs_min = strategy.params.RS_min
            RS_min.append(rs_min)
            final_results_list.append([period , PnL])
    #
    # Sort Results List
    by_period = sorted(final_results_list , key=lambda x: x[0])
    by_PnL = sorted(final_results_list , key=lambda x: x[1] , reverse=True)

    # Print results
    # print('Results: Ordered by period:')
    # for result in by_period:
    #     print('Period: {}, PnL: {}'.format(result[0] , result[1]))
    # print('Results: Ordered by Profit:')
    # for result in by_PnL:
    #     print('Period: {}, PnL: {}'.format(result[0] , result[1]))

    # plot optimization result:
    plt.scatter(ma_period , profit , label='profit')
    plt.margins(y=0.1)
    plt.xticks(np.arange(min(ma_period) , max(ma_period) + 1 , 10))
    plt.xlabel('period')
    plt.ylabel('result')
    plt.legend(loc='upper left')
    plt.show()
