import scrapper_hh as sc
import symbols
import time
import concurrent.futures as cf
import datetime as dt


DATA_PATH = '../../../Data/TSETMC_DATA/HH_History/'


if __name__ == '__main__':
    symbols = symbols.symbols_dropbox
    start = time.perf_counter()

    with cf.ThreadPoolExecutor(max_workers=4) as executor:
        results = executor.map(sc.scrapper_hh_history , symbols)

    finish = time.perf_counter()
    print(f'\nFinished in {round((finish - start) / 60 , 1)} minutes')

    # for result in results:
    #     if len(result[1]) == 0:
    #         continue
    #     file_name = DATA_PATH + result[0] + '__HH_History__until_' + result[1][0][0][0] + '.csv'
    #     with open(file_name , 'w') as file:
    #         # Header:
    #         file.write('DATE_JALALI,DATE_GREGORIAN,BUYERS_IND,BUYERS_CORP,SELLERS_IND,'
    #                    'SELLERS_CORP,VOL_BUY_IND,VOL_BUY_IND_%,VOL_BUY_CORP,'
    #                    'VOL_BUY_CORP_%,VOL_SELL_IND,VOL_SELL_IND_%,VOL_SELL_CORP,'
    #                    'VOL_SELL_CORP_%,VALUE_BUY_IND,VALUE_BUY_CORP,VALUE_SELL_IND,'
    #                    'VALUE_SELL_CORP,AVRG_PRICE_BUY_IND,AVRG_PRICE_BUY_CORP,'
    #                    'AVRG_PRICE_SELL_IND,AVRG_PRICE_SELL_CORP,CORP_TO_IND')
    #         file.write('\n')
    #         # Data:
    #         for day in result[1]:
    #             file.write(f'{day[0][0]},{day[0][1]},{day[1][0]},{day[1][1]},{day[1][2]},{day[1][3]},{day[2][0][0]},'
    #                        f'{day[2][0][1]},{day[2][1][0]},{day[2][1][1]},{day[2][2][0]},{day[2][2][1]},{day[2][3][0]},'
    #                        f'{day[2][3][1]},{day[3][0]},{day[3][1]},{day[3][2]},{day[3][3]},{day[4][0]},{day[4][1]},'
    #                        f'{day[4][2]},{day[4][3]},{day[5][0]}')
    #             file.write('\n')