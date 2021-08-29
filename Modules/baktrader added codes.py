# add in cerebro.py
def processPlots(self , cerebro , filename , numfigs=1 , iplot=True , start=None , end=None ,
                 width=16 , height=9 , dpi=300 , tight=True , use=None , **kwargs):
    # if self._exactbars > 0:
    #     return

    from backtrader import plot

    if cerebro.p.oldsync:
        plotter = plot.Plot_OldSync(**kwargs)
    else:
        plotter = plot.Plot(**kwargs)

    figs = []
    for stratlist in cerebro.runstrats:
        for si , strat in enumerate(stratlist):
            rfig = plotter.plot(strat , figid=si * 100 ,
                                numfigs=numfigs , iplot=iplot ,
                                start=start , end=end , use=use)
            for i , f in enumerate(rfig):
                plotter.savefig(f , filename=filename)
            figs.append(rfig)

        # this blocks code execution
        # plotter.show()

    return figs


# hack to wrap next_open method in all strategies:     #added
@staticmethod
def wrap(next_open):
    def outer(self):
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
        self.sizes = -1
        if self.portfo > self.sym_count_o:
            self.sizes = self.broker.get_cash() // (self.portfo - self.sym_count_o)

        next_open(self)

    return outer
