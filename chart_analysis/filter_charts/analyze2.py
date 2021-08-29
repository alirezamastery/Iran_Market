import backtrader as bt


class TestStrategy(bt.Strategy):
    params = (
        ('ma_period' , 20) ,
    )

    def __init__(self):
        self.inds = dict()
        for i , d in enumerate(self.datas):
            self.inds[d] = dict()
            self.inds[d]['EMA'] = bt.indicators.ExponentialMovingAverage(self.datas[i] , period=self.params.ma_period)


class analyze:

    def __init__(self , strategy):
        self.strategy = strategy
        self.cerebro = bt.Cerebro(stdstats=False)

        # Add a strategy:
        self.cerebro.addstrategy(strategy)

        # load data:
        # (function to load data)

        self.cerebro.run()


if __name__ == '__main__':
    test = analyze(strategy=TestStrategy)