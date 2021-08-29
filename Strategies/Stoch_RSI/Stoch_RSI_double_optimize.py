import os
import sys  # To find out the script name (in argv[0])

os.chdir(os.path.dirname(sys.argv[0]))
sys.path.append(os.path.abspath('../../Modules'))

import templates
import Stoch_RSI_double


class RS_RSI_Pairs_FIX20_opt(RS_RSI_Pairs_FIX20):
    optimize = True

    params = (
        ('portfo' , 10) ,
        ('ma_period' , 300) ,
        ('signal_threshold' , 2) ,
        ('fix_ma_period' , 55) ,
        ('rsi_period' , 14) ,
        ('rsi_buy_level' , 70) ,
        ('rsi_sell_level' , 70) ,
        ('rsi_above_days' , 0) ,
    )


class optimizer(templates.optimize):
    kwargs = {'ma_period': range(30 , 200 , 10) ,
              # 'fix_ma_period': range(1 , 300 , 10) ,
              # 'rsi_period':    range(5 , 50 , 2) ,
              }
    input_list = '../../Lists/input_data/different_industries.txt'


if __name__ == '__main__':
    opt = optimizer(strategy=RS_RSI_Pairs_FIX20_opt)
    opt.run()
