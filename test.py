import os
import numpy as np
import pandas as pd
import time
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import re
import random

DELIMITER = '│'
pd.options.display.max_columns = None
# pd.options.display.max_rows = None
pd.set_option('display.width' , 1000)


def interest(percent , days , amount):
    x = amount
    for i in range(days):
        x = x + x * percent
    return int(x)


s = 'bbbgr.csv'
gr = re.search(r'^[^.]+(?=.)' , s)

path = './'
files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path , f))]
for f in files:
    regs = re.search(r'Part-\d' , f)
    if regs:
        print(regs[0])
