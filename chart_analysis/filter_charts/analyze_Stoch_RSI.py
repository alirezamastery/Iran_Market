import os
import sys  # To find out the script name (in argv[0])

os.chdir(os.path.dirname(sys.argv[0]))
sys.path.append(os.path.abspath('../../Modules'))

import templates
import pandas as pd
from datetime import datetime
import backtrader as bt
import symdata as sd
import our_indicators as oind


class analyze(bt.Strategy):
    params = (
        ('RSI_Length' , 25) ,
        ('Stochastic_Length' , 25) ,
        ('rsi_period' , 14) ,
    )

    def __init__(self):
        # Symbols that we have positions on right now:
        self.InPosition = []
        for sym in self.InPosition:
            if '_Share_D' not in sym:
                sym += '_Share_D'

        self.buy_signal = list()
        self.sell_signal = list()
        self.final_symbols = list()
        self.inds = dict()
        for i , d in enumerate(self.datas):
            self.inds[d] = dict()
            # plotname = self.datas[i]._name.replace('_Share_D' , '') + ' / ' + self.datas[0]._name.replace('_D' , '')
            # add RS indicator:
            self.inds[d]['stoch_rsi'] = oind.Stoch_RSI(self.datas[i] ,
                                                       RSI_Length=self.params.RSI_Length ,
                                                       Stochastic_Length=self.params.Stochastic_Length)
            self.inds[d]['RSI'] = bt.indicators.RSI_Safe(self.datas[i] , period=self.params.rsi_period)

    def next(self):
        if len(self.data) == self.data.buflen():
            for i , d in enumerate(self.datas):
                # check for sell signals:
                sell_condition = self.inds[d]['stoch_rsi'].K[0] < 80 <= self.inds[d]['stoch_rsi'].K[-1]
                if self.datas[i]._name in self.InPosition and sell_condition:
                    self.sell_signal.append([self.datas[d]._name ,
                                             round(self.inds[d]['stoch_rsi'].K[0] , 2) ,
                                             round(self.inds[d]['RSI'].rsi[0] , 2)])
                # check for buy signals:
                buy_condition = self.inds[d]['stoch_rsi'].K[0] > 20 >= self.inds[d]['stoch_rsi'].K[-1] \
                                and self.inds[d]['stoch_rsi'].K[-2] < 20 and self.inds[d]['stoch_rsi'].K[-3] < 20
                if buy_condition:
                    self.buy_signal.append([self.datas[i]._name ,
                                            round(self.inds[d]['stoch_rsi'].K[0] , 2) ,
                                            round(self.inds[d]['RSI'].rsi[0] , 2)])

    def stop(self):

        with open('analyze_log.txt', 'w' , encoding='utf-8') as log_file:
            line = 'Sell Signals:' + '\n'
            log_file.write(line)
            print(line)
            for i , d in enumerate(self.sell_signal):
                self.final_symbols.append(d[0])
                d[0] = d[0].replace('_Share_D' , '')
                out_text = f'{d[0]:15.15} │ Stoch RSI: {d[1]:<5} │ RSI: {d[2]:<6}'
                log_file.write(out_text + '\n')
                print(out_text)

            line = '\n' + 'buy Signals:' + '\n'
            log_file.write(line)
            print(line)
            for i , d in enumerate(self.buy_signal):
                self.final_symbols.append(d[0])
                d[0] = d[0].replace('_Share_D' , '')
                out_text = f'{d[0]:15.15} │ Stoch RSI: {d[1]:<5} │ RSI: {d[2]:<6}'
                log_file.write(out_text + '\n')
                print(out_text)


class analyzing:
    plot = True
    show = ['REMAPNA_Share_D']
    # start = '2019-06-01'
    start = '2020-01-01'
    data_path = '../../Data/all/'
    end = ''
    input_list = '../Lists/input_data/portfo.txt'

    def __init__(self , strategy):
        self.cerebro = bt.Cerebro(stdstats=False)

        # add the strategy:
        self.cerebro.addstrategy(strategy)

        # find last candle date:
        df = pd.read_csv(self.data_path + 'TEPIX_D.txt' ,
                         skiprows=1 ,
                         header=None ,
                         parse_dates=True ,
                         dayfirst=True ,
                         index_col=[2])
        self.end = df.index[-1].strftime('%Y-%m-%d')
        print('Latest Candle Date:' , self.end)
        # load data:
        sd.add_cerebro_data(self.cerebro ,
                            input_list=self.input_list , data_path=self.data_path ,
                            start=self.start , end=self.end ,
                            add_fixincome=False ,
                            show=self.show)

    def run(self):
        # run over everything
        result = self.cerebro.run()

        # Plot the result
        if self.plot:
            print('\nSaving charts...')
            directory = 'Analyze Charts/' + self.end
            if not os.path.exists(directory):
                os.makedirs(directory)

            for res in result[0].final_symbols:
                for data in self.cerebro.datas:
                    if data._name == res:
                        data.plotinfo.plot = True
                    else:
                        data.plotinfo.plot = False
                filename = directory + '/' + res.replace('_Share_D' , '') + '__' + self.end + '.png'

                self.cerebro.processPlots(self.cerebro ,
                                          filename=filename ,
                                          style='candlestick' , rowsmajor=2 , rowsminor=1 ,
                                          barup='#26a69a' , bardown='#d75442' ,
                                          volup='#c3e7d5' , voldown='#f8c1c6' , voltrans=1 ,
                                          width=16 , height=9 ,
                                          tight=True)
            print('Saving charts completed')


if __name__ == '__main__':
    test = analyzing(strategy=analyze)
    test.run()
