import templates
import math as sys_math
import numpy as np


class RS_Portfo_Variance(templates.RS_base):
    ispairs = False
    RSI = False

    params = (
        ('ma_period' , 89) ,
        ('portfo' , 5) ,
        ('RS_min' , 100) ,
        ('signal_threshold' , 0.05) ,
        ('RS_max_switch' , True) ,
        ('VAR_max_switch' , False)
    )

    def __init__(self):
        super().__init__()
        self.fs = [0] * self.params.portfo
        self.portfo = self.params.portfo
        self.s_th = (self.params.signal_threshold / 100) + 1
        self.RS_min = self.params.RS_min
        self.buysig = False
        self.variance = [-1 for x in range(len(self.symbols))]
        self.inserted = [-1 , False]

    def next_open(self):
        # exposure:
        if self.passed != len(self.data):
            self.in_position += self.sym_count_e / self.portfo
            self.passed = len(self.data)

        # Check if an order is pending ... if yes, we cannot send a 2nd one:
        if self.order:
            return

        if len(self.data) == self.data.buflen():
            for i , d in enumerate(self.datas):
                self.order = self.close(data=self.datas[i])
            return

        # calculate volume for each symbol:
        sizes = -1
        if self.portfo > self.sym_count_o:
            sizes = self.broker.get_cash() // (self.portfo - self.sym_count_o)
        comm = 0.01

        # open inserted position:
        if self.inserted[1]:
            comm_adj_price = self.datas[self.inserted[0]].close[0] * (1 + (comm * 1))
            comm_adj_size = sizes / comm_adj_price
            size = sys_math.floor(comm_adj_size)
            self.order = self.buy(data=self.datas[self.inserted[0]] , size=size)
            self.log_buy(data_index=self.inserted[0] , size=size)
            self.position_flag[self.inserted[0]][2] = True
            self.inserted = [-1 , False]
            self.sym_count_o += 1

        # calculate variance of 'ma_period' candles before:
        for i , d in enumerate(self.datas):
            var_data = []
            for j in range(self.params.ma_period):
                var_data.append(d.close[-j])
            self.variance[i] = np.var(var_data)

        # check RS vs MA for each symbol:
        self.irs = []
        for i , d in enumerate(self.datas):
            if d._name == 'TEPIX':
                pass
            # if RS_max_switch == True:
            elif self.params.RS_max_switch and self.inds[d]['RS'].MA[0] * self.s_th < self.inds[d]['RS'].RS[0] and \
                    self.inds[d]['RS'].RS[0] > self.RS_min and not self.position_flag[i][2]:
                self.irs.append([i , self.inds[d]['RS'].RS[0]])
            # if RS_max_switch == False:
            elif not self.params.RS_max_switch and \
                    self.inds[d]['RS'].MA[0] * self.s_th < self.inds[d]['RS'].RS[0] < self.RS_min and \
                    not self.position_flag[i][2]:
                self.irs.append([i , self.inds[d]['RS'].RS[0]])
        # create list of signaled symbols for portfo:
        if self.params.RS_max_switch:
            self.irs.sort(key=lambda x: x[1] , reverse=True)
        if not self.params.RS_max_switch:
            self.irs.sort(key=lambda x: x[1] , reverse=False)
        self.portfo_syms = self.irs[:self.portfo]

        # open positions:
        for i , sym in enumerate(self.portfo_syms):
            if self.sym_count_o >= self.portfo or len(self.portfo_syms) < 1:
                break
            if not self.position_flag[sym[0]][2]:
                comm_adj_price = self.datas[sym[0]].close[0] * (1 + (comm * 1))
                comm_adj_size = sizes / comm_adj_price
                size = sys_math.floor(comm_adj_size)
                self.order = self.buy(data=self.datas[sym[0]] , size=size)
                self.position_flag[sym[0]][2] = True
                self.log_buy(data_index=sym[0] , size=size)
                self.sym_count_o += 1

        # check variance for new signals:
        opens = []
        vars = []
        if self.sym_count_e >= self.portfo:
            for i , d in enumerate(self.position_flag):
                if d[2]:
                    opens.append(d)
                    vars.append(self.variance[d[0]])
            # variance min:
            if self.params.VAR_max_switch and len(self.irs) > 0 and min(vars) > self.variance[self.irs[0][0]]:
                # close the min position:
                selector = self.variance.index(min(vars))
                self.order = self.close(data=self.datas[selector])
                self.position_flag[selector][2] = False
                self.sym_count_o -= 1
                self.log_sell(data_index=selector)
                # open new signal:
                self.inserted = [self.irs[0][0] , True]
            # variance max
            if not self.params.VAR_max_switch and len(self.irs) > 0 and max(vars) < self.variance[self.irs[0][0]]:
                # close the min position:
                selector = self.variance.index(min(vars))
                self.order = self.close(data=self.datas[selector])
                self.position_flag[selector][2] = False
                self.sym_count_o -= 1
                self.log_sell(data_index=selector)
                # open new signal:
                self.inserted = [self.irs[0][0] , True]

        # close signals:
        for i , data in enumerate(self.position_flag):
            if data[2] and self.inds[self.datas[data[0]]]['RS'].RS[0] < self.inds[self.datas[data[0]]]['RS'].MA[0]:
                self.log_sell(data_index=data[0])
                self.order = self.close(data=self.datas[data[0]])
                self.position_flag[i][2] = False
                self.sym_count_o -= 1


class RS_variance_backtest(templates.backtest):

    def __init__(self , strategy):
        super().__init__(strategy)


if __name__ == '__main__':
    RS_variance_backtest(RS_Portfo_Variance)
