import scrapper_hh as sc
import matplotlib.pyplot as plt
import numpy as np
import time
import concurrent.futures as cf
import symbols


def moving_average(a , n=8):
    ret = np.cumsum(a , dtype=float)
    ret[n:] = ret[n:] - ret[:-n]
    result = list(ret[n - 1:] / n)
    for i in range(n - 1):
        result.insert(0 , None)
    return result


if __name__ == '__main__':
    symbols = symbols.symbols_dropbox_test
    start = time.perf_counter()

    with cf.ThreadPoolExecutor(max_workers=4) as executor:
        results = executor.map(sc.scrapper_hh_current_year , symbols)

    finish = time.perf_counter()
    print(f'\nFinished in {round((finish - start) / 60 , 1)} minutes')

    buy_percent = list()
    sell_percent = list()
    for res in results:
        if len(res[1]) == 0:
            continue
        for row in res[1]:
            buy_percent.append(row[2][1][1])
            sell_percent.append(row[2][3][1])

    movav_period = 8
    movav_buy = moving_average(buy_percent , movav_period)
    movav_sell = moving_average(sell_percent , movav_period)

    plt.plot(buy_percent)
    plt.plot(movav_buy)
    plt.show()
