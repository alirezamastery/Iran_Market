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


class maxRiskSizerComms(bt.Sizer):
    '''
    Returns the number of shares rounded down that can be purchased for the
    max risk tolerance
    '''
    params = (('risk' , 0.99) ,
              ('debug' , True))

    def _getsizing(self , comminfo , cash , data , isbuy):
        size = 0

        # Work out the maximum size assuming all cash can be used.
        max_risk = sys_math.floor(cash * self.p.risk)

        comm = comminfo.p.commission

        if comminfo.stocklike:  # We are using a percentage based commissions

            # Apply the commission to the price. We can then divide our risk
            # by this value
            com_adj_price = data[0] * (1 + (comm * 2))  # *2 for round trip
            comm_adj_max_risk = "N/A"

            if isbuy == True:
                comm_adj_size = max_risk / com_adj_price
                if comm_adj_size < 0:  # Avoid accidentally going short
                    comm_adj_size = 0
            else:
                comm_adj_size = max_risk / com_adj_price * -1

        else:  # Else is fixed size
            # Dedecut commission from available cash to invest
            comm_adj_max_risk = max_risk - (comm * 2)  # Round trip
            com_adj_price = "N/A"

            if comm_adj_max_risk < 0:  # Not enough cash
                return 0

            if isbuy == True:
                comm_adj_size = comm_adj_max_risk / data[0]
            else:
                comm_adj_size = comm_adj_max_risk / data[0] * -1

        # Finally make sure we round down to the nearest unit.
        comm_adj_size = sys_math.floor(comm_adj_size)

        if self.p.debug:
            if isbuy:
                buysell = 'Buying'
            else:
                buysell = 'Selling'
            print("------------- Sizer Debug --------------")
            print("Action: {}".format(buysell))
            print("Price: {}".format(data[0]))
            print("Cash: {}".format(cash))
            print("Max Risk %: {}".format(self.p.risk * 100))
            print("Max Risk $: {}".format(max_risk))
            print("Commission Adjusted Max Risk: {}".format(comm_adj_max_risk))
            print("Current Price: {}".format(data[0]))
            print("Commission %: {}".format(comm * 100))
            print("Commission Adj Price (Round Trip): {}".format(com_adj_price))
            print("Size: {}".format(comm_adj_size))
            print("----------------------------------------")
        return comm_adj_size


class FixedCommisionScheme(bt.CommInfoBase):
    '''
    This is a simple fixed commission scheme
    '''
    params = (
        ('commission' , 5) ,
        ('stocklike' , False) ,
    )

    def _getcommission(self , size , price , pseudoexec):
        return self.p.commission


def ourdata(start='2010-01-01' , end='2020-01-01' , show=[]):
    if start < '2005-01-01':
        raise RuntimeError('data start date is before 2005 which is not acceptable')
    global open
    fl = open('data_input_list.txt' , 'r')
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
        cerebro.adddata(data , name=syms[i])

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
    pnl_net = int(analyzer.pnl.net.total)
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
    # row_format = "{:<15}" * (header_length + 1)
    print("Trade Analysis Results:")
    for i , row in enumerate(print_list):
        if i % 2 == 0:
            row_format = "{:<15}" * (header_length + 1)
            print(row_format.format('' , *row))
        else:
            row_format = "{:<15,}" * header_length
            print(' ' * 15 + row_format.format(*row).replace(',' , '/'))


def printDrawDownAnalysis(analyzer):
    '''
    Function to print the Technical Analysis results in a nice format.
    '''
    # Get the results we are interested in
    drawdown = round(analyzer.drawdown , 2)
    moneydown = int(analyzer.moneydown)
    length = analyzer.len
    max_dd = round(analyzer.max.drawdown , 2)
    max_md = int(analyzer.max.moneydown)
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
    # row_format = "{:<15}" * (header_length + 1)
    print("Drawdown Analysis Results:")
    for i , row in enumerate(print_list):
        if i % 2 == 0:
            row_format = "{:<15}" * (header_length + 1)
            print(row_format.format('' , *row))
        else:
            row_format = "{:<15,}" * header_length
            print(' ' * 15 + row_format.format(*row).replace(',' , '/'))


# class Broker(bt.Observer):
#     alias = ('CashValue',)
#     lines = ('cash', 'value')
#
#     plotinfo = dict(plot=True, subplot=True)
#
#     def next(self):
#         self.lines.cash[0] = self._owner.broker.getcash()
#         self.lines.value[0] = value = self._owner.broker.getvalue()


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
    params = (('risk' , 0.18) ,)

    def __init__(self):
        if self.p.risk > 1 or self.p.risk < 0:
            raise ValueError('The risk parameter is a percentage which must be between 0 and 1')

    def _getsizing(self , comminfo , cash , data , isbuy):
        if isbuy == True:
            print('cash:' , cash)
            size = sys_math.floor((cash * self.p.risk) / data[0])
            # print('size: %s' % size)
            # print('margin: %s' % cash)

        else:
            size = sys_math.floor((cash * self.p.risk) / data[0]) * -1
        return size


# Create a Stratey
class TestStrategy(bt.Strategy):
    params = (
        ('ma_period' , 51) ,
        ('portfo' , 5) ,
        ('RS_min' , 82) ,
        ('signal_threshold' , 0.05)
    )

    def log(self , txt , dt=None):
        # pass
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat() , txt))

    def __init__(self):
        # for i, d in enumerate(self.datas):
        #     print(i,d.open[0],d.high[-1])

        self.fs = [0] * self.params.portfo
        self.position_flag = []
        self.sym_count = 0
        self.RS_min = 100
        self.s_th = self.params.signal_threshold + 1
        self.buysig = False
        # self.o = dict()  # orders per data (main, stop, limit, manual-close)
        self.holding = dict()  # holding periods per data

        self.symbols = self.getdatanames()
        self.symbol_key = dict()
        # call RS indicator and data names
        self.inds = dict()
        for i , d in enumerate(self.datas):
            if i == 0:
                self.symbol_key[d] = self.symbols[i]
                self.position_flag.append(False)
            else:
                self.symbol_key[d] = self.symbols[i]
                self.inds[d] = dict()
                plotname = self.symbol_key[self.datas[i]] + ' / ' + self.symbol_key[self.datas[0]]
                self.inds[d]['RS'] = RSInd_100(self.datas[i] , self.datas[0] ,
                                               ma_period=self.params.ma_period ,
                                               plotname=plotname ,
                                               plotyticks=[50 , 100 , 150] ,
                                               plothlines=[50 , 100 , 150] ,
                                               )
                self.position_flag.append(False)
                # self.inds[d]['RS'].plotinfo.plotmaster = self.inds[self.datas[1]]['RS']
                # print(self.inds[d])

            # if i > 0:  # Check we are not on the first loop of data feed:
            #      d.plotinfo.plotmaster = self.datas[1]

        # print(self.inds)

        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None
        self.in_position = 0
        self.exposure = -1

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

        # calculate volume for each symbol:
        sizes = -1
        if self.params.portfo > self.sym_count:
            sizes = sys_math.floor(1 * self.broker.get_cash() / (self.params.portfo - self.sym_count))
        comm = 0.01

        # open positions:
        while self.sym_count < self.params.portfo:

            self.RS_min = self.params.RS_min

            for i , d in enumerate(self.datas):
                if i == 0:
                    pass
                elif not self.position_flag[i]:
                    if self.inds[d]['RS'].RS[0] > (self.inds[d]['RS'].MA[0]) * self.s_th and \
                            self.inds[d]['RS'].RS[0] > self.RS_min:
                        self.RS_min = self.inds[d]['RS'].RS[0]
                        self.fs[self.sym_count] = i

            if self.RS_min <= self.params.RS_min:
                break

            self.position_flag[self.fs[self.sym_count]] = True

            comm_adj_price = self.datas[self.fs[self.sym_count]].close[0] * (1 + (comm * 1))
            comm_adj_size = sizes / comm_adj_price
            size = sys_math.floor(comm_adj_size)

            self.order = self.buy(data=self.datas[self.fs[self.sym_count]] , size=size)
            self.log('BUY CREATED: %s , Price: %.2f , Size: %d' % (self.symbols[self.fs[self.sym_count]] ,
                                                                   self.datas[self.fs[self.sym_count]].close[0] ,
                                                                   size))

            self.sym_count += 1

        # close signals:
        for sym in range(self.params.portfo):
            if self.fs[sym] > 0 and self.inds[self.datas[self.fs[sym]]]['RS'].RS[0] < \
                    self.inds[self.datas[self.fs[sym]]]['RS'].MA[0]:
                self.log('SELL CREATED: %s , %.2f' % (self.symbols[self.fs[sym]] , self.datas[
                    self.fs[sym]].close[0]))
                self.order = self.close(data=self.datas[self.fs[sym]])
                self.position_flag[self.fs[sym]] = False
                self.fs[sym] = -1
                self.sym_count -= 1

        self.fs.sort(reverse=True)

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
                        (order.data._name ,
                         order.executed.price ,
                         order.executed.value ,
                         order.executed.comm))
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log('SELL EXECUTED: %s , Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.data._name ,
                          order.executed.price ,
                          order.executed.value ,
                          order.executed.comm))

            self.bar_executed = len(self)

        elif order.status == order.Canceled:
            self.log('Order Problem: Canceled , Symbol: %s' % (order.data._name))
        elif order.status == order.Margin:
            self.log('Order Problem: Margin , Symbol: %s' % (order.data._name))
            print('cash:' , self.broker.get_cash())
            # print(self.order)
        elif order.status == order.Rejected:
            self.log('Order Problem: Rejected , Symbol: %s' % (order.data._name))

        self.order = None

    def notify_trade(self , trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT:  GROSS: {:<10,.0f} | NET: {:<10,.0f}'.format(trade.pnl ,
                                                                                 trade.pnlcomm).replace(',' , '/'))

    def stop(self):
        self.exposure = self.in_position / self.data.buflen() * 100
        print('Exposure:' , round(self.exposure , 2) , '%')

        # self.log('Final Balance: %.0f' % self.broker.get_value())


if __name__ == '__main__':
    cerebro = bt.Cerebro(cheat_on_open=True ,
                         # stdstats=False
                         )

    # Add a strategy
    cerebro.addstrategy(TestStrategy)

    # load data:
    sd.add_cerebro_data(cerebro , start='2010-01-01' , show=['Bank'])

    cerebro.broker.setcash(1000000)
    cerebro.broker.set_checksubmit(checksubmit=False)
    # cerebro.broker.set_coo(coo=True)
    cerebro.broker.set_coc(coc=True)

    # Add the new commissions scheme
    cerebro.broker.setcommission(commission=0.01)
    # comminfo = FixedCommisionScheme(commission=0.01)
    # cerebro.broker.addcommissioninfo(comminfo)

    print('Starting Portfolio Value: {:,.0f}'.format(cerebro.broker.getvalue()).replace("," , "/"))

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
    # printTradeAnalysis(firstStrat.analyzers.ta.get_analysis())
    # printDrawDownAnalysis(firstStrat.analyzers.dd.get_analysis())

    anu_ret = firstStrat.analyzers.ar.get_analysis()
    # print(firstStrat.analyzers.ar.get_analysis())

    print('Final Portfolio Value: {:,.0f}'.format(cerebro.broker.getvalue()).replace("," , "/"))
    # print(firstStrat.analyzers.dd.get_analysis())

    # Plot the result
    cerebro.plot(style='candlestick' , rowsmajor=1 , rowsminor=1 , barup='#26a69a' , bardown='#ef5350' ,
                 volup='#c3e7d5' , voldown='#f8c1c6' , voltrans=1)
