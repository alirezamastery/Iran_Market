from __future__ import (absolute_import , division , print_function , unicode_literals)
import datetime  # For datetime objects
import os.path  # To manage paths
import sys  # To find out the script name (in argv[0])
import pandas
import datetime as dt
import symdata as sd
import math as sys_math
import backtrader as bt
import backtrader.indicators as btind
import backtrader.mathsupport as math


def ourdata(start='2010-01-01' , end='2020-01-01' , show=[]):
    if start < '2005-01-01':
        raise RuntimeError('data start date is before 2005 which is not acceptable')
    global open
    fl = open('symbols.txt' , 'r')
    symbols = fl.readlines()
    symbols = [x.strip() for x in symbols]
    for i , sym in enumerate(symbols):
        print('%d- %s' % (i + 1 , sym))

    datalist = []
    syms = []
    for sym in symbols:
        path = 'Data/' + sym + '.txt'
        datalist.append([path , sym])
        syms.append(sym)
    # print(datalist[19][0])

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

        # get a certain slice of data:
        # datafeed = datafeed.loc['2019-02-01':'2019-05-01']

        # fill the blank dates:
        date_index = pandas.date_range(start , end)
        datafeed = datafeed.reindex(date_index , method='bfill')
        df_days = pandas.to_datetime(datafeed.index.date)
        bdays = pandas.bdate_range(start=datafeed.index[0].date() ,
                                   end=datafeed.index[-1].date() ,
                                   weekmask='Sat Sun Mon Tue Wed' ,
                                   freq='C')
        datafeed = datafeed[df_days.isin(bdays)]
        # print(len(datafeed))
        # print(datafeed)

        # Pass it to the backtrader datafeed and add it to the cerebro
        data = bt.feeds.PandasData(dataname=datafeed , name=datalist[i][1] , openinterest=None)
        if not datalist[i][1] in show:
            data.plotinfo.threeD_plot = False
        cerebro.adddata(data)

    return syms


def printTradeAnalysis(analyzer):
    '''
    Function to print the Technical Analysis results in a nice format.
    '''
    # Get the results we are interested in
    total_open = analyzer.total.open
    total_closed = analyzer.total.closed
    total_won = analyzer.won.total
    total_lost = analyzer.lost.total
    win_streak = analyzer.streak.won.longest
    lose_streak = analyzer.streak.lost.longest
    pnl_net = round(analyzer.pnl.net.total , 2)
    strike_rate = round((total_won / total_closed) * 100 , 2)
    # Designate the rows
    h1 = ['Total Open' , 'Total Closed' , 'Total Won' , 'Total Lost']
    h2 = ['Strike Rate' , 'Win Streak' , 'Losing Streak' , 'PnL Net']
    r1 = [total_open , total_closed , total_won , total_lost]
    r2 = [strike_rate , win_streak , lose_streak , pnl_net]
    # Check which set of headers is the longest.
    if len(h1) > len(h2):
        header_length = len(h1)
    else:
        header_length = len(h2)
    # Print the rows
    print_list = [h1 , r1 , h2 , r2]
    row_format = "{:<15}" * (header_length + 1)
    print("Trade Analysis Results:")
    for row in print_list:
        print(row_format.format('' , *row))


def printDrawDownAnalysis(analyzer):
    '''
    Function to print the Technical Analysis results in a nice format.
    '''
    # Get the results we are interested in
    drawdown = round(analyzer.drawdown , 2)
    moneydown = round(analyzer.moneydown , 2)
    length = analyzer.len
    max_dd = round(analyzer.max.drawdown , 2)
    max_md = round(analyzer.max.moneydown , 2)
    max_len = analyzer.max.len

    # Designate the rows
    h1 = ['Drawdown' , 'Moneydown' , 'Length']
    h2 = ['Max drawdown' , 'Max moneydown' , 'Max len']
    r1 = [drawdown , moneydown , length]
    r2 = [max_dd , max_md , max_len]
    # Check which set of headers is the longest.
    if len(h1) > len(h2):
        header_length = len(h1)
    else:
        header_length = len(h2)
    # Print the rows
    print_list = [h1 , r1 , h2 , r2]
    row_format = "{:<15}" * (header_length + 1)
    print("Drawdown Analysis Results:")
    for row in print_list:
        print(row_format.format('' , *row))


class Broker(bt.Observer):
    alias = ('CashValue' ,)
    lines = ('cash' , 'value')

    plotinfo = dict(plot=True , subplot=True)

    def next(self):
        self.lines.cash[0] = self._owner.broker.getcash()
        self.lines.value[0] = value = self._owner.broker.getvalue()


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
        # print('in the ind: ' , self.datas[0].close[1] * 100 / self.datas[1].close[1] )
        # self.addminperiod(self.params.period)

    # def __next__(self):
    #     value = self.datas[1].close[0] / self.datas[0].close[0]
    # #     # datasum = bt.math.fsum(self.lines.RS(size=self.params.period))
    #     self.lines.MA[0] = 0.02


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
        ('ma_period' , 339) ,
    )

    def log(self , txt , dt=None):
        pass
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[1].datetime.date(0)
        print('%s, %s' % (dt.isoformat() , txt))

    def __init__(self):
        # for i, d in enumerate(self.datas):
        #     print(i,d.open[0],d.high[-1])
        self.final_symbol = -1
        self.RS_min = 100
        self.signal_threshold = 1.05
        self.buysig = False
        # self.o = dict()  # orders per data (main, stop, limit, manual-close)
        self.holding = dict()  # holding periods per data

        # call RS indicator
        self.inds = dict()
        for i , d in enumerate(self.datas):
            if i == 0:
                pass
            else:
                self.inds[d] = dict()
                self.inds[d]['RS'] = RSInd_100(self.datas[i] , self.datas[0] ,
                                               ma_period=self.params.ma_period ,
                                               plotname=symbols[i] + '/' + symbols[0] ,
                                               plotyticks=[50 , 100 , 150] ,
                                               plothlines=[50 , 100 , 150] ,
                                               )
                # self.inds[d]['RS'].plotinfo.plotmaster = self.inds[self.datas[1]]['RS']
                print(self.inds[d])

            # if i > 0:  # Check we are not on the first loop of data feed:
            #      d.plotinfo.plotmaster = self.datas[1]

        print(self.inds)

        # self.rs = RSInd_100(self.datas[0] , self.datas[1] , ma_period=self.params.ma_period)
        # RSInd(self.datas[0] , self.datas[2])
        # self.datas[0].plotinfo.plotmaster = self.datas[1]

        # # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[1].close

        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None
        self.in_position = 0
        self.exposure = -1

        # Add a MovingAverageSimple indicator
        # self.sma = bt.indicators.SimpleMovingAverage(
        #     self.datas[0], period=self.params.maperiod)

        # Indicators for the plotting show
        # bt.indicators.ExponentialMovingAverage(self.datas[1], period=25)
        # bt.indicators.StochasticSlow(self.datas[2])
        # bt.indicators.MACDHisto(self.datas[0])
        # rsi = bt.indicators.RSI(self.datas[0])
        # bt.indicators.SmoothedMovingAverage(rsi, period=10)
        # bt.indicators.ATR(self.datas[0], plot=False)

    def next_open(self):
        # Simply log the closing price of the series from the reference
        # self.log('Close, %.2f' % self.dataclose[0])

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        if len(self.data) == self.data.buflen():
            for i , d in enumerate(self.datas):
                self.order = self.close(data=self.datas[i])
            return

        if self.final_symbol > 0 and self.getposition(data=self.datas[self.final_symbol]).size:

            self.in_position += 1
            if self.inds[self.datas[self.final_symbol]]['RS'].RS[0] < self.inds[self.datas[
                self.final_symbol]]['RS'].MA[0]:
                self.buysig = False
                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log('SELL CREATE: %s , %.2f' % (symbols[self.final_symbol] , self.datas[
                    self.final_symbol].close[0]))

                # Keep track of the created order to avoid a 2nd order
                self.order = self.close(data=self.datas[self.final_symbol])


        else:

            self.RS_min = 10
            for i , d in enumerate(self.datas):
                if i == 0:
                    pass
                else:
                    # dt , dn = self.datetime.date() , d._name
                    pos = self.getposition(d).size
                    # print('{} {} Position {}'.format(dt , dn , pos))

                    if not pos:
                        if self.inds[d]['RS'].RS[0] > (self.inds[d]['RS'].MA[0]) * self.signal_threshold and \
                                self.inds[d]['RS'].RS[0] > self.RS_min:
                            self.buysig = True
                            self.RS_min = self.inds[d]['RS'].RS[0]
                            self.final_symbol = i

            if self.final_symbol > 0 and self.buysig:
                # BUY, BUY, BUY!!! (with all possible default parameters)
                self.log('BUY CREATE: %s, %.2f' % (symbols[self.final_symbol] , self.datas[self.final_symbol].close[0]))

                # Keep track of the created order to avoid a 2nd order
                self.order = self.buy(data=self.datas[self.final_symbol])

        # # Check if we are in the market
        # if not self.getposition(data=self.datas[1]):
        #
        #     # Not yet ... we MIGHT BUY if ...
        #     if self.rs.lines.RS[0] > self.rs.lines.MA[0]:
        #         # BUY, BUY, BUY!!! (with all possible default parameters)
        #         self.log('BUY CREATE, %.2f' % self.dataclose[0])
        #
        #         # Keep track of the created order to avoid a 2nd order
        #         self.order = self.buy(data=self.datas[1])
        #
        # else:
        #     self.in_position += 1
        #     print('in position:' , self.in_position)
        #     if self.rs.lines.RS[0] < self.rs.lines.MA[0]:
        #         # SELL, SELL, SELL!!! (with all possible default parameters)
        #         self.log('SELL CREATE, %.2f' % self.dataclose[0])
        #
        #         # Keep track of the created order to avoid a 2nd order
        #         self.order = self.close(data=self.datas[1])

    def notify_order(self , order):
        if order.status in [order.Submitted , order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                        'BUY EXECUTED: %s , Price: %.2f, Cost: %.2f, Comm %.2f' %
                        (symbols[self.final_symbol] ,
                         order.executed.price ,
                         order.executed.value ,
                         order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log('SELL EXECUTED: %s , Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (symbols[self.final_symbol] ,
                          order.executed.price ,
                          order.executed.value ,
                          order.executed.comm))

            self.bar_executed = len(self)

        elif order.status == order.Canceled:
            self.log('Order Problem: Canceled')
        elif order.status == order.Margin:
            self.log('Order Problem: Margin')
            print(self.order)
        elif order.status == order.Rejected:
            self.log('Order Problem: Rejected')

        self.order = None

    def notify_trade(self , trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' % (trade.pnl , trade.pnlcomm))

    def stop(self):
        self.exposure = self.in_position / self.data.buflen() * 100
        print('Exposure:' , round(self.exposure , 2) , '%')


if __name__ == '__main__':
    cerebro = bt.Cerebro(cheat_on_open=True ,
                         # stdstats=False
                         )

    # Add a strategy
    cerebro.addstrategy(TestStrategy)

    # Add sizer:
    cerebro.addsizer(maxRiskSizer)
    # Add a FixedSize sizer according to the stake
    # cerebro.addsizer(bt.sizers.FixedSize , stake=10)

    # load data:
    symbols = sd.add_cerebro_data(cerebro , start='2010-01-01' , show=[])

    cerebro.broker.setcash(1000000.0)


    cerebro.broker.set_coo(coo=True)
    cerebro.broker.set_coc(coc=True)

    # Set the commission - 0.1% ... divide by 100 to remove the %
    cerebro.broker.setcommission(commission=0.01)

    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Add the analyzers we are interested in
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer , _name="ta")
    cerebro.addanalyzer(bt.analyzers.DrawDown , _name="dd")
    cerebro.addanalyzer(bt.analyzers.AnnualReturn , _name="ar")

    # Add the Observers we are interested in
    # cerebro.addobserver(bt.observers.DrawDown)
    # cerebro.addobserver(bt.observers.TimeReturn)
    # cerebro.addobserver(bt.observers.Benchmark , data=cerebro.datas[0])

    # Add writer to save result in a csv file
    cerebro.addwriter(bt.WriterFile , csv=True , out='results.csv')

    # Run over everything
    strategies = cerebro.run()
    firstStrat = strategies[0]

    # print the analyzers
    printTradeAnalysis(firstStrat.analyzers.ta.get_analysis())
    printDrawDownAnalysis(firstStrat.analyzers.dd.get_analysis())
    print(firstStrat.analyzers.ar.get_analysis())

    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
    # print(firstStrat.analyzers.dd.get_analysis())

    # Plot the result
    cerebro.plot(style='candlestick' , rowsmajor=1 , rowsminor=1 , barup='#26a69a' , bardown='#ef5350' ,
                 volup='#c3e7d5' , voldown='#f8c1c6' , voltrans=1)

# pyfoilio:
# pyfoliozer = first_strat.analyzers.getbyname('pyfolio')
# returns , positions , transactions , gross_lev = pyfoliozer.get_pf_items()
# print('-- RETURNS')
# print(returns)
# print('-- POSITIONS')
# print(positions)
# print('-- TRANSACTIONS')
# print(transactions)
# print('-- GROSS LEVERAGE')
# print(gross_lev)
