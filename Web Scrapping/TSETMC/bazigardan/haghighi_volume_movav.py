import scrapper_hh as sc
import matplotlib.pyplot as plt
import numpy as np
import time
import concurrent.futures as cf
import symbols
import matplotlib.dates as mdates
import datetime


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

    buy_volume = list()
    sell_volume = list()
    date = list()
    for res in results:
        if len(res[1]) == 0:
            continue
        for row in res[1]:
            buy_volume.append(row[2][1][0])
            sell_volume.append(row[2][3][0])
            date.append(row[0])
    buy_volume.reverse()
    sell_volume.reverse()
    date.reverse()
    date = [datetime.datetime.strptime(d , "%Y-%m-%d").date() for d in date]

    movav_period = 21
    movav_buy = moving_average(buy_volume , movav_period)
    movav_sell = moving_average(sell_volume , movav_period)

    # Plot:
    fig , ax = plt.subplots()

    years = mdates.YearLocator()  # every year
    months = mdates.MonthLocator()  # every month
    years_fmt = mdates.DateFormatter('%Y')

    # round to nearest years.
    datemin = np.datetime64(date[0] , 'M')
    datemax = np.datetime64(date[-1] , 'M') + np.timedelta64(1 , 'M')

    ax.plot(date , buy_volume)
    plt.plot(date , movav_buy)

    formatter = mdates.DateFormatter("%Y-%m-%d")
    ax.xaxis.set_major_formatter(formatter)
    ax.xaxis.set_major_locator(mdates.WeekdayLocator())
    plt.xticks(rotation=45)
    plt.show()
