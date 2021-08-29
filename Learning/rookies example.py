
import backtrader as bt
import pandas
from datetime import datetime

class firstStrategy(bt.Strategy):
    params = (
        ('period',21),
        )

    def __init__(self):
        self.startcash = self.broker.getvalue()
        self.rsi = bt.indicators.RSI_SMA(self.data.close, period=self.params.period)

    def next(self):
        if not self.position:
            if self.rsi < 30:
                self.buy(size=100)
        else:
            if self.rsi > 70:
                self.sell(size=100)

if __name__ == '__main__':
    #Variable for our starting cash
    startcash = 10000

    #Create an instance of cerebro
    cerebro = bt.Cerebro(optreturn=False)

    #Add our strategy
    cerebro.optstrategy(firstStrategy, period=range(14,21))

    datalist = [
        ('Data/TEPIX_D.txt' , 'TEPIX') ,  # [0] = Data file, [1] = Data name
        ('Data/REMAPNA_Share_D.txt' , 'REMAPNA') ,
        # ('Data/AKHABER_Share_D.txt', 'AKHABER'),
    ]

    # print(datalist[0][0])

    for i in range(len(datalist)):
        datapath = datalist[i][0]
        df = pandas.read_csv(datapath ,
                             skiprows=1 ,
                             header=None ,
                             parse_dates=True ,
                             dayfirst=True ,
                             index_col=[2])
        open = df[4]
        high = df[5]
        low = df[6]
        close = df[7]
        volume = df[8]
        datafeed = pandas.DataFrame({'open': open , 'high': high , 'low': low , 'close': close , 'volume': volume})

        datafeed = datafeed.tail(300)

        # get a certain slice of data:
        # datafeed = datafeed.loc['2019-02-01':'2019-05-01']

        # fill the blank dates:
        # start = '2019-01-01'
        # end = '2020-01-01'
        # date_index = pandas.date_range(start , end)
        # datafeed = datafeed.reindex(date_index , method='bfill')
        # print(datafeed)

        # Pass it to the backtrader datafeed and add it to the cerebro
        data = bt.feeds.PandasData(dataname=datafeed , name=datalist[i][1] , openinterest=None)
        cerebro.adddata(data)

    # Set our desired cash start
    cerebro.broker.setcash(startcash)

    # Run over everything
    opt_runs = cerebro.run()

    # Generate results list
    final_results_list = []
    for run in opt_runs:
        for strategy in run:
            value = round(strategy.broker.get_value(),2)
            PnL = round(value - startcash,2)
            period = strategy.params.period
            final_results_list.append([period,PnL])

    #Sort Results List
    by_period = sorted(final_results_list, key=lambda x: x[0])
    by_PnL = sorted(final_results_list, key=lambda x: x[1], reverse=True)

    #Print results
    print('Results: Ordered by period:')
    for result in by_period:
        print('Period: {}, PnL: {}'.format(result[0], result[1]))
    print('Results: Ordered by Profit:')
    for result in by_PnL:
        print('Period: {}, PnL: {}'.format(result[0], result[1]))