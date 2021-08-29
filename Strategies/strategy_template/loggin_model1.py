def log(self , txt , dt=None):
    # pass
    ''' Logging function fot this strategy'''
    dt = dt or self.datas[0].datetime.date(0)
    print('%s│ %s' % (dt.isoformat() , txt))


def log_buy(self , index , size):
    self.log('{}│ {:11.11} │ Price: {:<13.2f} │ Size: {:<15} │'.format('BUY CREATED'.ljust(self.col1_width , ' ') ,
                                                                       self.symbols[index] ,
                                                                       self.datas[index].close[0] ,
                                                                       size))


def log_sell(self , index):
    self.log('{}│ {:11.11} │ Price: {:<13.2f} │ {:21} │'.format('SELL CREATED'.ljust(self.col1_width , ' ') ,
                                                                self.symbols[index] ,
                                                                self.datas[index].close[0] ,
                                                                ' '))


def notify_order(self , order):
    if order.status in [order.Submitted , order.Accepted]:
        # Buy/Sell order submitted/accepted to/by broker - Nothing to do
        return

    # Check if an order has been completed
    # Attention: broker could reject order if not enough cash
    if order.status in [order.Completed]:
        if order.isbuy():
            self.log(
                    '{}│ {:11.11} │ Price: {:<13.2f} │ Cost: {:<15.2f} │ Comm {:.2f}'.format(
                            'BUY EXECUTED'.ljust(self.col1_width , ' ') ,
                            order.data._name ,
                            order.executed.price ,
                            order.executed.value / 10 ,
                            order.executed.comm / 10))
            pos = find_in_list_of_lists(self.position_flag , order.data._name)
            self.sym_count_e += 1
            self.buyprice = order.executed.price
            self.buycomm = order.executed.comm
        else:  # Sell
            self.log('{}│ {:11.11} │ Price: {:<13.2f} │ Cost: {:<15.2f} │ Comm {:.2f}'.format(
                    'SELL EXECUTED'.ljust(self.col1_width , ' ') ,
                    order.data._name ,
                    order.executed.price ,
                    order.executed.value / 10 ,
                    order.executed.comm / 10))
            pos = find_in_list_of_lists(self.position_flag , order.data._name)
            self.sym_count_e -= 1
        self.bar_executed = len(self)

    elif order.status == order.Canceled:
        self.log('Order Problem: %s Canceled' % (order.data._name))
    elif order.status == order.Margin:
        self.log('Order Problem: %s Margin' % (order.data._name))
    elif order.status == order.Rejected:
        self.log('Order Problem: %s Rejected' % (order.data._name))

    self.order = None


def notify_trade(self , trade):
    if not trade.isclosed:
        return

    self.log(
            '{}│ {:11.11} | GROSS: {:<13,.0f} | NET:  {:<16,.0f}│'.format(
                    'TRADE PROFIT'.ljust(self.col1_width , ' ') ,
                    trade.data._name ,
                    trade.pnl / 10 ,
                    trade.pnlcomm / 10 ,
                    ' ').replace(',' , '/'))