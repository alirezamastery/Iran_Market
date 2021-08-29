import backtrader as bt


class TestStrategy(bt.Strategy):
    params = (
        ('ma_period' , 20) ,
    )

    def __init__(self):
        self.result = []
        self.inds = dict()
        for i , d in enumerate(self.datas):
            self.inds[d] = dict()
            self.inds[d]['EMA'] = bt.indicators.ExponentialMovingAverage(self.datas[i] , period=self.params.ma_period)

    def next_open(self):
        if len(self.data) == self.data.buflen():
            for i , d in enumerate(self.datas):
                if self.inds[d]['EMA'][0] < self.datas[i].close[0]:
                    self.result.append(self.datas[i]._name)

    def stop(self):
        print(self.result)

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

