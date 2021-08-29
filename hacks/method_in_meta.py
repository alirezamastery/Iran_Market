class StrategyBase:  # just to have StrategyBase class and prevent IDE error check
    pass


class MetaStrategy(StrategyBase.__class__):
    _indcol = dict()

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
                for i, d in enumerate(self.datas):
                    self.order = self.close(data=self.datas[i])
                return

            # calculate volume for each symbol:
            self.sizes = -1
            if self.portfo > self.sym_count_o:
                self.sizes = self.broker.get_cash() // (self.portfo - self.sym_count_o)

            next_open(self)

        return outer

    def __new__(meta, name, bases, dct):
        # Hack to support original method name for notify_order
        if 'notify' in dct:
            # rename 'notify' to 'notify_order'
            dct['notify_order'] = dct.pop('notify')
        if 'notify_operation' in dct:
            # rename 'notify' to 'notify_order'
            dct['notify_trade'] = dct.pop('notify_operation')

        if 'next_open' in dct:  # <------ added this so our method will be injected in the class
            dct['next_open'] = meta.wrap(dct['next_open'])

        return super(MetaStrategy, meta).__new__(meta, name, bases, dct)
