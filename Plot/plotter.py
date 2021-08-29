import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import pandas as pd
import numpy as np

pd.options.display.max_columns = None
pd.options.display.max_rows = None
pd.set_option('display.width' , 1000)
pd.set_option('float_format' , '{:,.0f}'.format)

file_path = 'Opt_Results/RS_RSI_pairs_optimize__20-02-15__21-01.csv'
data = pd.read_csv(file_path)

print(data)
print(data.describe())

x = 'ma_period'
y = 'rsi_period'
z = 'profit'
X = data[x].tolist()
Y = data[y].tolist()
Z = data[z].tolist()
Z = [round(i / 1000000,2) for i in Z]

fig = plt.figure()
fig.tight_layout()
ax = plt.axes(projection='3d')
ax.tick_params(axis='z' , which='major' , pad=12)
plt.xticks(np.arange(min(X) , max(X) , 2))
plt.yticks(np.arange(min(Y) , max(Y) , 2))
# ax.set_zticks(np.arange(10 * 10 ^ 6 , 80000000 , 10000000))
# ax.ticklabel_format(axis="z" , style="plain")
surf = ax.plot_trisurf(X , Y , Z , cmap='RdYlGn')
ax.set_xlabel(x , color='Blue' , labelpad=10 , fontsize=18)
ax.set_ylabel(y , color='Blue' , labelpad=10 , fontsize=18)
ax.set_zlabel(z + ' (million)' , color='Blue' , labelpad=25 , fontsize=18)
fig.colorbar(surf , shrink=0.5 , aspect=5)
plt.show()
