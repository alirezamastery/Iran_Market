import os
import sys  # To find out the script name (in argv[0])

os.chdir(os.path.dirname(sys.argv[0]))
sys.path.append(os.path.abspath('../../Modules'))

import templates
import our_indicators as oind
import tracemalloc
from RS_Pairs_FIX20 import RS_Pairs_FIX20

class RS_Pairs_FIX20_opt(RS_Pairs_FIX20):
    optimize = True
    ispairs = True
    commission = 0.01
    fix_income_commission = 0.0001
    add_fixincome = True
    data_range_start = 1
    RSI = False

    params = (
        ('portfo' , 5) ,
        ('ma_period' , 300) ,
        ('signal_threshold' , 1) ,
        ('fix_ma_period' , 200) ,
    )


class RS_Pairs_FIX20_optimizer(templates.optimize):
    start = '2010-01-01'
    end = '2020-01-01'
    kwargs = {'ma_period':        range(30 , 400 , 10) ,
              'fix_ma_period':    range(1 , 300 , 10) ,
              'signal_threshold': range(0 , 6 , 1) ,
              }
    input_list = '../../Lists/input_data/different_industries.txt'


if __name__ == '__main__':
    # tracemalloc.start()

    opt = RS_Pairs_FIX20_optimizer(strategy=RS_Pairs_FIX20_opt)
    opt.run()

    # snapshot = tracemalloc.take_snapshot()
    # top_stats = snapshot.statistics('lineno')
    #
    # print("[ Top 10 ]")
    # for stat in top_stats[:10]:
    #     print(stat)
