import datetime  # For datetime objects
import os.path  # To manage paths
import sys  # To find out the script name (in argv[0])
import numpy as np
import pandas as pd
import datetime as dt
import math
import matplotlib.pyplot as plt
from matplotlib import style
import matplotlib.dates as mdates
import seaborn as sns
from pandas.plotting import register_matplotlib_converters
import symdata as sd
import inspect
from scipy.stats import linregress
from scipy.stats import zscore
import codetools as ct
from codetools import log


style.use('ggplot')
register_matplotlib_converters()
pd.options.display.max_columns = None
pd.options.display.max_rows = None
pd.set_option('display.width', 1000)

formatter = mdates.DateFormatter('%Y-%m-%d')
locator = mdates.MonthLocator()


class code_tools:

    @staticmethod
    def plots():
        plt.show()

    @staticmethod
    def axis_format(ax):
        ax.xaxis.set_major_formatter(formatter)
        ax.xaxis.set_major_locator(locator)
        return ax

    @staticmethod
    def figure_saver(figure, name, dpi=100):
        caller = inspect.stack()[1].function
        path = f'Analysis/{caller}/'
        if not os.path.exists(path):
            os.makedirs(path)
        figure.set_size_inches(19, 11)
        figure.savefig(path + name + '_' + caller + '.png', dpi=dpi)
        plt.close(figure)


class Statistics(code_tools):

    def input_type(self, name):
        if isinstance(name, str):
            symbols = [name]
        elif isinstance(name, list):
            symbols = [s for s in name]
        else:
            symbols = self.main_df.columns
        return symbols

    def __init__(self, files=None, start='2019-01-01', end='2020-10-01', jalali: bool = True,
                 back_fill: bool = False, no_index: bool = False, valid_percent: float = 0.5):
        if jalali:
            start_gregorian = ct.jalali_to_gregorian(start)
            end_gregorian = ct.jalali_to_gregorian(end)
            print(f'\nstart Date: {start}  -->  {start_gregorian}')
            print(f'  end Date: {end}  -->  {end_gregorian}')
        else:
            start_gregorian = start
            end_gregorian = end
            print(f'\nstart Date: {start_gregorian}  -->  {ct.gregorian_to_jalali(start_gregorian)}')
            print(f'  end Date: {end_gregorian}  -->  {ct.gregorian_to_jalali(end_gregorian)}')
        if start_gregorian < '2005-01-01':
            raise RuntimeError('data start date is before 2005 which is not acceptable')
        if end_gregorian < start_gregorian:
            raise RuntimeError('wrong end date')

        syms = None
        if files is None:
            raise RuntimeError('Please insert a list or path for files')
        elif isinstance(files, str):
            with open(files, 'r') as f:
                syms = f.readlines()
                syms = [x.strip() for x in syms]
        elif isinstance(files, list):
            if not no_index and 'TEPIX' not in files:
                files.insert(0, 'TEPIX')
            syms = files

        self.back_fill = back_fill
        self.main_df = pd.DataFrame()
        incomplete_data = list()
        calender_days = pd.date_range(start_gregorian, end_gregorian)
        market_days = pd.bdate_range(start=calender_days[0], end=calender_days[-1],
                                     weekmask='Sat Sun Mon Tue Wed', freq='C')

        for symbol in syms:
            if symbol in ['TEPIX', 'Dollar']:
                path = 'all/' + symbol + '_D.txt'
            else:
                path = 'all/' + symbol + '_Share_D.txt'
            df = pd.read_csv(path,
                             skiprows=1,
                             header=None,
                             parse_dates=True,
                             dayfirst=True,
                             index_col=[2])
            close = df[7].loc[start_gregorian:end_gregorian]
            feed = pd.DataFrame({symbol: close})
            df_days = pd.to_datetime(feed.index.date)
            feed = feed[df_days.isin(market_days)]

            if len(feed) / len(market_days) < valid_percent:
                incomplete_data.append(symbol)
                continue

            if back_fill:
                feed = feed.reindex(market_days, method='bfill')

            self.main_df = self.main_df.join(feed, how='outer')

        self.main_df.index.name = 'Date'
        if len(incomplete_data) > 0:
            print('\nThese symbols does not have enough data in the specified date range:')
            ct.list_printer_vertical(incomplete_data)

    def cov(self, show_plot: bool = True, save_plot: bool = False, mask: bool = False):
        cov_df = self.main_df.pct_change().multiply(100).cov()
        print('Covariance table:')
        print(cov_df)
        print()
        if show_plot or save_plot:
            data_mask = vmin = vmax = None
            if mask:
                data_mask = np.triu(np.ones_like(cov_df, dtype=bool))
                vmin = data_mask.min().min()
                vmax = data_mask.max().max()
            fig_cov, ax_cov = plt.subplots(figsize=(9, 6))
            sns.heatmap(cov_df, mask=data_mask, xticklabels=True, yticklabels=True,
                        vmin=vmin, vmax=vmax,
                        center=0,
                        annot=True, cmap='RdYlGn', linewidths=.5, cbar_kws={"shrink": .5}, ax=ax_cov)
            plt.xticks(rotation=70)
            if save_plot:
                self.figure_saver(fig_cov, 'Covariance')

        return cov_df

    def cor(self, show_plot: bool = True, save_plot: bool = False, mask: bool = False, print_head: bool = False,
            head_number: int = 5, corr_limit: float = 0):
        corr_df = self.main_df.corr()
        print('\nCorrelation table:')
        print(corr_df)
        print()
        if show_plot or save_plot:
            data_mask = None
            if mask:
                data_mask = np.triu(np.ones_like(corr_df, dtype=bool))
            log('plotting...')
            fig_cor, ax_cor = plt.subplots(figsize=(9, 6))
            sns.heatmap(corr_df, mask=data_mask,
                        xticklabels=True, yticklabels=True, vmin=-1, vmax=1,
                        annot=True, cmap='RdYlGn', linewidths=.5, cbar_kws={"shrink": .5}, ax=ax_cor)
            plt.xticks(rotation=70)
            if save_plot:
                log('saving the plot...')
                fig_cor.savefig('Analysis/' + 'Correlation.png', dpi=100)
                plt.close(fig_cor)
                log('plot saved as: cor.png')

        pairs = list()
        for i in range(1, corr_df.shape[0]):
            for j in range(i + 1, corr_df.shape[1]):
                if corr_df.iloc[i, j] < corr_limit:
                    pairs.append([corr_df.columns[i], corr_df.columns[j], round(corr_df.iloc[i, j], 2)])
        pairs.sort(key=lambda x: x[2], reverse=False)
        if print_head:
            print(pairs[:head_number])

        return pairs[:head_number], corr_df

    def cor_with(self):
        tepix_df = self.main_df['TEPIX']
        corrw_df = self.main_df.corrwith(tepix_df)
        print('\nCorrelations with TEPIX:')
        for i in corrw_df.index:
            print(f'{i:<15} | correlation: {corrw_df[i]: .2f}')

        negatives = dict()
        for i, c in enumerate(corrw_df):
            if c < 0:
                negatives[corrw_df.index[i]] = round(c, 2)
        print(f'\nNegative Correlations: {len(negatives)}')
        for key in negatives.keys():
            print(f'{key:<15} : {negatives[key]}')

        return corrw_df

    def fibo(self, symbol=None, ret: float = None, ret_time: float = None, colored: bool = True,
             save_plots: bool = False):

        if ret is None or ret_time is None:
            raise RuntimeError('please insert values for fibonacci ratios')

        if isinstance(symbol, str):
            symbols = [symbol]
        elif isinstance(symbol, list):
            symbols = [s for s in symbol]
        else:
            symbols = self.main_df.columns
        print('\nCalculating Fibonacci levels:')
        for sym in symbols:
            data = self.main_df[sym]
            pi_1 = 1
            pi_2 = pi_3 = 0
            pivots = list()
            pivots_date = list()
            retracement = list()
            search = None

            check_nan = data.isnull()
            check_count = 0
            for i, value in enumerate(check_nan):
                if not value and check_count == 0:
                    pi_2 = i
                    check_count += 1
                elif not value and check_count == 1:
                    pi_1 = i
                    break

            while True:
                if data[pi_1] > data[pi_2]:
                    search = 'peak'
                    break
                elif data[pi_1] < data[pi_2]:
                    search = 'valley'
                    break
                elif pi_1 < len(data) - 1:
                    pi_1 += 1
                else:
                    log(f'{sym} skipped due to invalid data')
                    break

            log(sym)

            for i, d in enumerate(data):
                if i <= pi_1:
                    continue

                if search == 'peak':
                    if data[i] >= data[pi_1]:
                        pi_1 = i
                        continue

                    elif (data[pi_1] - data[i]) / (data[pi_1] - data[pi_2]) >= ret and \
                            (i - pi_1) / (pi_1 - pi_2) >= ret_time:
                        pivots.append(data[pi_1])
                        pivots_date.append(data.index[pi_1])
                        if len(pivots) >= 2:
                            retrace = (data[pi_1] - data[pi_2]) / (data[pi_3] - data[pi_2])
                            retracement.append(round(retrace, 2))
                        pi_3, pi_2, pi_1 = pi_2, pi_1, i
                        search = 'valley'
                        continue

                elif search == 'valley':
                    if data[i] <= data[pi_1]:
                        pi_1 = i
                        continue

                    elif (data[i] - data[pi_1]) / (data[pi_2] - data[pi_1]) >= ret and \
                            (i - pi_1) / (pi_1 - pi_2) > ret_time:
                        pivots.append(data[pi_1])
                        pivots_date.append(data.index[pi_1])
                        if len(pivots) >= 2:
                            retrace = (data[pi_2] - data[pi_1]) / (data[pi_2] - data[pi_3])
                            retracement.append(round(retrace, 2))
                        pi_3, pi_2, pi_1 = pi_2, pi_1, i
                        search = 'peak'
                        continue

            # current wave:
            if search == 'peak' and len(pivots) > 1:
                if (max(data[pivots_date[-1]:]) - data[pi_1]) / (data[pi_2] - data[pi_1]) > ret:
                    pivots.append(max(data[pivots_date[-1]:]))
                    pivots_date.append(data[pivots_date[-1]:].idxmax())
                    retrace = (data[pi_2] - data[pi_1]) / (data[pi_2] - data[pi_3])
                    retracement.append(round(retrace, 2))
            elif search == 'valley' and len(pivots) > 1:
                if (pivots[-1] - min(data[pivots_date[-1]:])) / (pivots[-1] - pivots[-2]) > ret:
                    ret_point = min(data[pivots_date[-1]:])
                    pivots.append(ret_point)
                    pivots_date.append(data[pivots_date[-1]:].idxmin())
                    retrace = (data[pi_2] - data[pi_1]) / (data[pi_2] - data[pi_3])
                    retracement.append(round(retrace, 2))

            pivots_df = pd.DataFrame({'pivots': pivots}, index=pivots_date)

            # Plot:
            figs_fibo = dict()
            axs_fibo = dict()
            figs_fibo[sym], axs_fibo[sym] = plt.subplots(1, constrained_layout=True)
            figs_fibo[sym].set_size_inches(18, 10)
            axs_fibo[sym].plot(data.index, data.tolist(), '-', color='black', label=sym)
            axs_fibo[sym].xaxis.set_major_formatter(formatter)
            axs_fibo[sym].xaxis.set_major_locator(locator)

            if colored:
                axs_fibo[sym].scatter(pivots_df.index, pivots_df['pivots'], color='black',
                                      label=f'Pivots |  Price ratio: {ret}  |  Time ratio: {ret_time}')
                for i, d in enumerate(pivots_df['pivots']):
                    if i == 0:
                        pass
                    if pivots_df['pivots'][i] > pivots_df['pivots'][i - 1]:
                        axs_fibo[sym].plot(pivots_df.index[i - 1:i + 1], pivots_df['pivots'][i - 1:i + 1], '--',
                                           color='green', label='_')
                    else:
                        axs_fibo[sym].plot(pivots_df.index[i - 1:i + 1], pivots_df['pivots'][i - 1:i + 1], '--',
                                           color='red', label='_')
            else:
                axs_fibo[sym].plot(pivots_df.index, pivots_df['pivots'], '--o')

            # annotations:
            for i, txt in enumerate(retracement, start=1):
                if i % 2 == 0:
                    axs_fibo[sym].annotate(txt, (pivots_df.index[i], pivots_df['pivots'][i]),
                                           xytext=(-1, 5), textcoords='offset points')
                else:
                    axs_fibo[sym].annotate(txt, (pivots_df.index[i], pivots_df['pivots'][i]),
                                           xytext=(1, -15), textcoords='offset points')

            axs_fibo[sym].legend(loc='upper left')
            plt.xticks(rotation=45)
            if save_plots:
                self.figure_saver(figs_fibo[sym], sym)

    def zigzag(self, symbol=None, InpDepth: int = 12, InpDeviation: int = 5, InpBackstep: int = 3,
               colored: bool = True, save_plots: bool = False):
        if self.back_fill:
            raise RuntimeError('ZigZag does not work with back_fill enabled')

        ret_average = None
        symbols = self.input_type(symbol)

        print('\nZigZag lines:')
        for sym in symbols:
            data = self.main_df[sym]
            data.dropna(inplace=True)
            if len(data) < 100:
                log(f'not enough candles in {sym}')
                continue
            log(f'{sym}')

            i = 0
            limit = extreme_counter = extreme_search = 0
            shift = back = last_high_pos = last_low_pos = 0
            val = res = 0
            curlow = curhigh = last_high = last_low = 0

            _Point = 0

            ZigZagBuffer = [0 for _ in range(len(data))]
            HighMapBuffer = [0 for _ in range(len(data))]
            LowMapBuffer = [0 for _ in range(len(data))]

            limit = InpDepth

            for shift in range(limit, len(data) - 1):
                # low:
                val = min(data[shift - InpDepth:shift + 1])
                if val == last_low:
                    val = 0
                else:
                    last_low = val
                    if data[shift] - val > InpDeviation * _Point:
                        val = 0
                    else:
                        for back in range(1, InpBackstep + 1):
                            res = LowMapBuffer[shift - back]
                            if res != 0 and res > val:
                                LowMapBuffer[shift - back] = 0

                if data[shift] == val:
                    LowMapBuffer[shift] = val
                else:
                    LowMapBuffer[shift] = 0

                # high:
                val = max(data[shift - InpDepth:shift + 1])
                if val == last_high:
                    val = 0
                else:
                    last_high = val
                    if (val - data[shift]) > InpDeviation * _Point:
                        val = 0
                    else:
                        for back in range(1, InpBackstep + 1):
                            res = HighMapBuffer[shift - back]
                            if res != 0 and res < val:
                                HighMapBuffer[shift - back] = 0

                if data[shift] == val:
                    HighMapBuffer[shift] = val
                else:
                    HighMapBuffer[shift] = 0

            if extreme_search == 0:
                last_low = 0
                last_high = 0
            else:
                last_low = curlow
                last_high = curhigh

            for shift in range(limit, len(data) - 1):
                res = 0
                if extreme_search == 0:
                    if last_low == 0 and last_high == 0:
                        if HighMapBuffer[shift] != 0:
                            last_high = data[shift]
                            last_high_pos = shift
                            extreme_search = 'Bottom'
                            ZigZagBuffer[shift] = last_high
                            res = 1
                        if LowMapBuffer[shift] != 0:
                            last_low = data[shift]
                            last_low_pos = shift
                            extreme_search = 'Peak'
                            ZigZagBuffer[shift] = last_low
                            res = 1
                    continue
                elif extreme_search == 'Peak':
                    if LowMapBuffer[shift] != 0 and LowMapBuffer[shift] < last_low and HighMapBuffer[shift] == 0:
                        ZigZagBuffer[last_low_pos] = 0
                        last_low_pos = shift
                        last_low = LowMapBuffer[shift]
                        ZigZagBuffer[shift] = last_low
                        res = 1
                    if HighMapBuffer[shift] != 0 and LowMapBuffer[shift] == 0:
                        last_high = HighMapBuffer[shift]
                        last_high_pos = shift
                        ZigZagBuffer[shift] = last_high
                        extreme_search = 'Bottom'
                        res = 1
                    continue
                elif extreme_search == 'Bottom':
                    if HighMapBuffer[shift] != 0 and HighMapBuffer[shift] > last_high and LowMapBuffer[shift] == 0:
                        ZigZagBuffer[last_high_pos] = 0
                        last_high_pos = shift
                        last_high = HighMapBuffer[shift]
                        ZigZagBuffer[shift] = last_high
                    if LowMapBuffer[shift] != 0 and HighMapBuffer[shift] == 0:
                        last_low = LowMapBuffer[shift]
                        last_low_pos = shift
                        ZigZagBuffer[shift] = last_low
                        extreme_search = 'Peak'
                    continue

            pivots_date = list()
            pivots = list()
            retraces = list()
            for i, d in enumerate(ZigZagBuffer):
                if d != 0:
                    pivots.append(d)
                    pivots_date.append(data.index[i])

            if len(pivots) > 2:
                for i, d in enumerate(pivots):
                    if i < 2:
                        continue
                    retrace = 'NaN'
                    try:
                        if pivots[i] > pivots[i - 1]:
                            retrace = (pivots[i] - pivots[i - 1]) / (pivots[i - 2] - pivots[i - 1])
                        elif pivots[i] < pivots[i - 1]:
                            retrace = (pivots[i - 1] - pivots[i]) / (pivots[i - 1] - pivots[i - 2])
                        retraces.append(round(retrace, 2))
                    except:
                        print(f'unexpected condition of pivot positions in {sym}')
                        retraces.append('NaN')

                if len(retraces) > 1 and isinstance(ret_average, list):
                    if pivots[-1] < pivots[-2] and retraces[-1] < retraces[-2]:  # if it is a downward retrace
                        ret_average.append(retraces[-1])
            else:
                log(f'not enough pivots in {sym} to calculate retracements')

            pivots_df = pd.DataFrame({'pivots': pivots}, index=pivots_date)
            print(pivots_df)

            # Plot:
            figs_zigzag = dict()
            axs_zigzag = dict()
            figs_zigzag[sym], axs_zigzag[sym] = plt.subplots(1, constrained_layout=True)
            axs_zigzag[sym].plot(data.index, data.tolist(), '-', color='black', label=sym)
            axs_zigzag[sym].xaxis.set_major_formatter(formatter)
            axs_zigzag[sym].xaxis.set_major_locator(locator)

            if colored:
                axs_zigzag[sym].scatter(pivots_df.index, pivots_df['pivots'], color='black', label=f'Pivots')
                for i, d in enumerate(pivots_df['pivots']):
                    if i == 0:
                        pass
                    if pivots_df['pivots'][i] > pivots_df['pivots'][i - 1]:
                        axs_zigzag[sym].plot(pivots_df.index[i - 1:i + 1], pivots_df['pivots'][i - 1:i + 1], '--',
                                             color='green', label='_')
                    else:
                        axs_zigzag[sym].plot(pivots_df.index[i - 1:i + 1], pivots_df['pivots'][i - 1:i + 1], '--',
                                             color='red', label='_')
            else:
                axs_zigzag[sym].plot(pivots_df.index, pivots_df['pivots'], '--o')

            # annotations:
            for i, txt in enumerate(retraces, start=2):
                if i % 2 == 0:
                    axs_zigzag[sym].annotate(txt, (pivots_df.index[i], pivots_df['pivots'][i]),
                                             xytext=(1, -15), textcoords='offset points')
                else:
                    axs_zigzag[sym].annotate(txt, (pivots_df.index[i], pivots_df['pivots'][i]),
                                             xytext=(-1, 5), textcoords='offset points')

            axs_zigzag[sym].legend(loc='upper left')
            plt.xticks(rotation=45)
            if save_plots:
                self.figure_saver(figs_zigzag[sym], sym)

        if isinstance(ret_average, list):
            ret_av = sum(ret_average) / len(ret_average)
            log(f'Average of last retracements are: {round(ret_av, 2)}', blank_lines=1)

    def RS(self, numerator, denominator, ma_period: int = 21, save_plot: bool = False):
        intersection = pd.merge(self.main_df[numerator], self.main_df[denominator], how='inner', left_index=True,
                                right_index=True)
        intersection.dropna(inplace=True)

        intersection['RS'] = intersection[numerator] / intersection[denominator]
        intersection['MA'] = intersection['RS'].rolling(window=ma_period).mean()

        fig_rs, ax_rs = plt.subplots(constrained_layout=True)
        ax_rs = self.axis_format(ax_rs)
        ax_rs.plot(intersection.index, intersection['RS'], color='black', label=f'RS  {numerator} / {denominator}')
        ax_rs.plot(intersection.index, intersection['MA'], color='red', label=f'MA {ma_period}')
        ax_rs.legend(loc='upper left')
        plt.xticks(rotation=45)
        if save_plot:
            self.figure_saver(fig_rs, f'numerator-denominator')

    def Beta(self, symbol=None, show_plot: bool = False, save_plot: bool = False):
        names = self.input_type(symbol)
        betas = list()
        tepix_df = self.main_df['TEPIX']
        num_indent = len(str(len(names)))

        print('\nBeta Coefficient:')
        for index, name in enumerate(names):
            if name == 'TEPIX':
                continue
            symbol_df = self.main_df[name]
            intersection = pd.merge(tepix_df, symbol_df, how='inner', left_index=True, right_index=True)
            r_df = pd.DataFrame()

            # .iloc[1:] for removing 0 index which is nan
            r_df['sr'] = intersection[name].pct_change().iloc[1:].multiply(100)
            r_df['tr'] = intersection['TEPIX'].pct_change().iloc[1:].multiply(100)
            r_df.dropna(inplace=True)

            # remove outlier data:
            z_scores = zscore(r_df)
            abs_z_scores = np.abs(z_scores)
            drops = list()
            for i, di in enumerate(abs_z_scores):
                for j, dj in enumerate(di):
                    if dj > 3:
                        drops.append(i)
            r_df = r_df.drop(index=r_df.index[drops])

            # calculate beta:
            # covar = np.cov(r_df['sr'] , r_df['tr'] , ddof=1)[0][1]
            # TEPIX_var = r_df['tr'].var()
            # beta = covar / TEPIX_var

            (beta_coeff, intercept, rvalue, pvalue, stderr) = linregress(r_df['tr'], r_df['sr'])
            log(f'{index:<{num_indent}}.{name:<15} | beta_coeff: {beta_coeff:< 10,.2f} | rvalue: {rvalue:< 15,.2f}')

            betas.append([name, round(beta_coeff, 2), round(rvalue, 2)])

            if show_plot or save_plot:
                X = np.linspace(r_df['sr'].min(), r_df['sr'].max(), 100)
                Y = X * beta_coeff
                multiplier = 2
                Z = X * beta_coeff * multiplier
                fig_beta, ax_beta = plt.subplots(1, 1, constrained_layout=True)
                # ax_beta.scatter(r_df['tr'] , r_df['sr'] , alpha=0.3 , label='_' , color='#1f77b4')
                ax_beta.plot(r_df['tr'], r_df['sr'], '.', alpha=0.3, label='_', color='#1f77b4')
                ax_beta.plot(X, Y, color='red', label='Beta')
                ax_beta.plot(X, Z, color='green', label=f'Beta * {multiplier}')
                plt.xlabel('tepix_return')
                plt.ylabel('symbol_return')
                # ax_beta.set_xlim(left=-10 , right=10)
                # ax_beta.set_ylim(bottom=-10 , top=10)
                ax_beta.set_aspect('equal', adjustable='box')
                plt.legend(loc='upper left')
                if save_plot:
                    self.figure_saver(fig_beta, name)

        return betas


if __name__ == '__main__':
    START = '1398-03-01'
    END = '1399-06-05'
    names = ['TEPIX', 'Dollar', 'VABESADER', 'VATEJARAT', 'VAPASAR', 'SHBEHRAN', 'KHODRO', 'BAREKAT',
             'DETOLID', 'DESOBHAN', 'SITA', 'SEFARS', 'SIDKO', 'TEMELLAT']
    all_files = sd.all_files_dropbox()

    analyze = Statistics(files=names, start=START, end=END, jalali=True, back_fill=False, valid_percent=0.2)
    # analyze.fibo(ret=0.38 , ret_time=0.23 , save_plots=True)
    # analyze.zigzag(InpDepth=20 , InpDeviation=5 , InpBackstep=5 , save_plots=True)
    # analyze.cov()
    # analyze.cor(plot=True , save_plot=True)
    # analyze.cor_with()
    # analyze.RS('TEPIX' , 'Dollar' , ma_period=54)
    betas = analyze.Beta(symbol='DESOBHAN', save_plot=False, show_plot=True)
    analyze.plots()
    # betas.sort(key=lambda x: x[2] , reverse=True)
    # for b in betas:
    #     print(f'{b[0]:<15} {b[2]}')
