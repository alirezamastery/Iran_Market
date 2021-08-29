import pandas as pd
import os
import numpy as np
import time
from scipy.stats import linregress
from scipy.stats import zscore
import matplotlib.pyplot as plt

plt.style.use('ggplot')
pd.options.display.max_columns = None
pd.set_option('display.width' , 1000)
pd.options.display.max_rows = None


def mycov(a , b):
    if len(a) != len(b):
        return

    a_mean = np.mean(a)
    b_mean = np.mean(b)

    sum = 0

    for i in range(0 , len(a)):
        sum += ((a[i] - a_mean) * (b[i] - b_mean))

    return sum / (len(a) - 1)


def Beta(show_plot: bool = False , save_plot: bool = False):
    START = '2015-09-16'
    END = '2020-09-16'
    path = '../Data/all/'
    files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path , f))]

    betas = list()

    tepix_df = pd.read_csv('../Data/all/TEPIX_D.txt' , usecols=[x for x in range(10)] ,
                           skiprows=1 , header=None , parse_dates=True , index_col=[2])
    tepix_df = tepix_df.rename(columns={4: 'tepix_open' , 7: 'tepix_close'})
    tepix_df = tepix_df[{'tepix_open' , 'tepix_close'}]
    tepix_df = tepix_df.loc[START:END]

    files = ['KHODRO_Share_D.txt']
    for file in files:
        symbol_df = pd.read_csv(path + file , usecols=[x for x in range(10)] ,
                                skiprows=1 , header=None , parse_dates=True , index_col=[2])
        symbol_df = symbol_df.rename(columns={4: 'symbol_open' , 7: 'symbol_close'})
        symbol_df = symbol_df[{'symbol_open' , 'symbol_close'}]
        symbol_df = symbol_df.loc[START:END]
        if len(symbol_df) < 10:
            continue

        intersection = pd.merge(tepix_df , symbol_df , how='inner' , left_index=True , right_index=True)

        r_df = pd.DataFrame()

        # .iloc[1:] for removing 0 index which is nan
        r_df['sr'] = intersection['symbol_close'].pct_change().iloc[1:].multiply(100)
        r_df['tr'] = intersection['tepix_close'].pct_change().iloc[1:].multiply(100)

        # remove outlier data:
        z_scores = zscore(r_df)
        abs_z_scores = np.abs(z_scores)
        drops = list()
        for i , di in enumerate(abs_z_scores):
            for j , dj in enumerate(di):
                if dj > 3:
                    drops.append(i)
        r_df = r_df.drop(index=r_df.index[drops])

        # calculate beta:
        covar = np.cov(r_df['sr'] , r_df['tr'] , ddof=1)[0][1]
        TEPIX_var = r_df['tr'].var()
        beta = covar / TEPIX_var

        (beta_coeff , intercept , rvalue , pvalue , stderr) = linregress(r_df['tr'] , r_df['sr'])
        print(f'{file[:-4]:<20} | beta_coeff: {beta_coeff:< 15,.7f} | rvalue: {rvalue:< 15,.07f}')

        betas.append([file[:-4] , round(beta , 2)])

        X = np.linspace(r_df['sr'].min() , r_df['sr'].max() , 100)
        Y = X * beta_coeff
        multiplier = 2
        Z = X * beta_coeff * multiplier
        fig , ax = plt.subplots(1 , 1 , constrained_layout=True)
        # ax.scatter(r_df['tr'] , r_df['sr'] , alpha=0.3 , label='_' , color='#1f77b4')
        ax.plot(r_df['tr'] , r_df['sr'] , '.', alpha=0.3 , label='_' , color='#1f77b4')
        ax.plot(X , Y , color='red' , label='Beta')
        ax.plot(X , Z , color='green' , label=f'Beta * {multiplier}')
        plt.xlabel('tepix_return')
        plt.ylabel('symbol_return')
        # ax.set_xlim(left=-10 , right=10)
        # ax.set_ylim(bottom=-10 , top=10)
        ax.set_aspect('equal' , adjustable='box')
        plt.legend(loc='upper left')
        if save_plot:
            fig.set_size_inches(19 , 11)
            fig.savefig('beta figs/' + file[:-4] + '.png' , dpi=100)
            plt.close(fig)
        if show_plot:
            plt.show()

    return betas


if __name__ == '__main__':
    betas = Beta(show_plot=True , save_plot=False)
    for b in betas:
        print(f'{b[0]:<20} : {b[1]: }')
    print('\nbeta > 1 :')
    for b in betas:
        if b[1] > 1:
            print(f'{b[0]:<20} : {b[1]: }')
