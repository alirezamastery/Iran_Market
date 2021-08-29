import backtrader as bt
import backtrader.indicators as btind
from backtrader.indicators import mabase


# RS Indicator
class RS(bt.Indicator):
    lines = ('RS' , 'MA' ,)
    params = (('ma_period' , 34) ,)

    def __init__(self):
        self.lines.RS = self.datas[1].close / self.datas[0].close
        self.lines.MA = btind.MovingAverageSimple(self.lines.RS , period=self.params.ma_period)


class RS_100(bt.Indicator):
    lines = ('RS' , 'MA' ,)
    params = (('ma_period' , 34) ,)

    def __init__(self):
        # datas[1] in TEPIX_D and datas[0] is the symbol
        RS_raw = self.datas[0].close / self.datas[1].close
        ratio = self.datas[1].close[1] * 100 / self.datas[0].close[1]
        self.lines.RS = RS_raw * ratio
        self.lines.MA = btind.MovingAverageSimple(self.lines.RS , period=self.params.ma_period)


class Stoch_RSI(bt.Indicator):
    lines = ('K' , 'D')
    plotlines = dict(
            K=dict(color='blue') ,
            D=dict(color='red')
    )
    params = (
        ('RSI_Length' , 14) ,
        ('Stochastic_Length' , 14) ,
        ('K%' , 3) ,
        ('D%' , 3) ,
        ('movav' , mabase.MovAv.Smoothed) ,
        ('upperband' , 80) ,
        ('lowerband' , 20) ,
        ('lookback' , 1) ,
    )

    def _plotlabel(self):
        plabels = [self.p.RSI_Length]
        plabels += [self.p.movav] * self.p.notdefault('movav')
        plabels += [self.p.lookback] * self.p.notdefault('lookback')
        return plabels

    def _plotinit(self):
        self.plotinfo.plotyhlines = [self.p.upperband , self.p.lowerband]

    def __init__(self):
        self.RSI = btind.RSI_Safe(self.datas[0] , period=self.params.RSI_Length)

    def next(self):
        if len(self.data) < self.params.RSI_Length + self.params.Stochastic_Length:
            pass
        else:
            rsi = list()
            for i in range(self.params.Stochastic_Length):
                rsi.append(self.RSI[-i])
            # print(rsi)
            RSI_max = max(rsi)
            RSI_min = min(rsi)
            if RSI_max > RSI_min:
                self.lines.K[0] = (self.RSI - RSI_min) * 100 / (RSI_max - RSI_min)
            else:
                self.lines.K[0] = 100


class Int_Money_buy(bt.Indicator):
    lines = ('intel' , 'MA')
    params = (('vol_ma_period' , 14) ,
              ('intel_ma_period' , 5))
    plotlines = dict(intel=dict(_method='bar' , alpha=0.7 , width=0.7 , color='green'))

    def __init__(self):
        self.vol_ma = btind.MovingAverageSimple(self.datas[0].volume , period=self.params.vol_ma_period)

    def next(self):
        if len(self.data) < self.params.vol_ma_period + self.params.intel_ma_period:
            pass
        else:
            if self.datas[0].volume[0] > self.vol_ma[0]:
                self.lines.intel[0] = self.datas[0].VOL_BUY_IND[0] // self.datas[0].BUYERS_IND
            else:
                self.lines.intel[0] = 0
            value_sum = 0
            for i in range(self.params.intel_ma_period):
                value_sum += self.lines.intel[-i]
            self.lines.MA[0] = value_sum // self.params.intel_ma_period


class Int_Money_sell(bt.Indicator):
    lines = ('intel' , 'MA')
    params = (('vol_ma_period' , 14) ,
              ('intel_ma_period' , 5))
    plotlines = dict(intel=dict(_method='bar' , alpha=0.7 , width=0.7 , color='red'))

    def __init__(self):
        self.vol_ma = btind.MovingAverageSimple(self.datas[0].volume , period=self.params.vol_ma_period)

    def next(self):
        if len(self.data) < self.params.vol_ma_period + self.params.intel_ma_period:
            pass
        else:
            if self.datas[0].volume[0] > self.vol_ma[0]:
                self.lines.intel[0] = self.datas[0].VOL_SELL_IND[0] // self.datas[0].SELLERS_IND
            else:
                self.lines.intel[0] = 0
            value_sum = 0
            for i in range(self.params.intel_ma_period):
                value_sum += self.lines.intel[-i]
            self.lines.MA[0] = value_sum // self.params.intel_ma_period