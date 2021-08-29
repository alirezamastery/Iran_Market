import sys
import os
from tkinter import *
from tkinter import ttk
import tkinter.messagebox
from tkinter import filedialog
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from stat import S_ISREG , ST_CTIME , ST_MODE

os.chdir(os.path.dirname(sys.argv[0]))

class plotter():
    def __init__(self , parent):
        self.root = parent
        self.file_list = []
        self.headers = []
        self.data = []
        # field labels:
        self.label_0 = Label(root , text='File Name :')
        self.label_1 = Label(root , text='X :')
        self.label_2 = Label(root , text='Y :')
        self.label_3 = Label(root , text='Z :')
        self.label_0.grid(row=0 , sticky=E)
        self.label_1.grid(row=1 , sticky=E)
        self.label_2.grid(row=2 , sticky=E)
        self.label_3.grid(row=3 , sticky=E)

        self.label_4 = ttk.Label(self.root , width=50)
        self.label_4.grid(row=0 , column=1)

        self.button_1 = ttk.Button(self.root , text="Insert File" , command=self.open_file)
        self.button_1.grid(row=0 , column=2)
        self.button_2 = ttk.Button(self.root , text="Plot" , command=self.choose_plot)
        self.button_2.grid(row=4 , column=1)

        # axes select:
        self.x = StringVar()
        self.y = StringVar()
        self.z = StringVar()
        self.menu_1 = ttk.OptionMenu(self.root , self.x , *self.headers)
        self.menu_2 = ttk.OptionMenu(self.root , self.y , *self.headers)
        self.menu_3 = ttk.OptionMenu(self.root , self.z , *self.headers)
        self.menu_1.grid(row=1 , column=1 , sticky=W)
        self.menu_2.grid(row=2 , column=1 , sticky=W)
        self.menu_3.grid(row=3 , column=1 , sticky=W)
        # 3D select:
        self.threeD = BooleanVar()
        self.threeD.set(TRUE)
        self.threeD_check = ttk.Checkbutton(self.root , text='3D Plot' , variable=self.threeD ,
                                            command=self.get_threeD_check)
        self.threeD_check.grid(row=3 , column=2)

    def get_threeD_check(self):
        if self.threeD.get():
            self.label_3.config(state=NORMAL)
            self.menu_3.config(state=NORMAL)
        else:
            self.label_3.config(state=DISABLED)
            self.menu_3.config(state=DISABLED)

    def open_file(self):
        directory = os.path.abspath('../Strategies')
        self.root.filename = filedialog.askopenfilename(
                initialdir=directory ,
                title='Select CSV File' ,
                filetypes=(('csv files' , '*.csv') , ('all files' , '*.*')))
        self.label_4.config(text=os.path.basename(self.root.filename))
        self.insert()

    def insert(self):
        file_path = self.root.filename
        self.data = pd.read_csv(file_path)
        headers = self.data.columns.values
        self.update_menu(headers)

    def update_menu(self , header):
        self.headers = header
        # x:
        menu = self.menu_1['menu']
        menu.delete(0 , 'end')
        for string in self.headers:
            menu.add_command(label=string , command=lambda value=string: self.x.set(value))
        self.x.set(self.headers[-2])
        # y:
        menu2 = self.menu_2['menu']
        menu2.delete(0 , 'end')
        for string in self.headers:
            menu2.add_command(label=string , command=lambda value=string: self.y.set(value))
        self.y.set(self.headers[-1])
        # z:
        menu3 = self.menu_3['menu']
        menu3.delete(0 , 'end')
        for string in self.headers:
            menu3.add_command(label=string , command=lambda value=string: self.z.set(value))
        self.z.set(self.headers[0])

    def choose_plot(self):
        if self.threeD.get():
            self.threeD_plot()
        else:
            self.twoD_plot()

    def twoD_plot(self):
        if self.x.get() == self.y.get():
            tkinter.messagebox.showerror('Error' , 'متغیر های غیر یکسان برای محورها انتخاب کنید')
            return
        X = self.data[self.x.get()].tolist()
        Y = self.data[self.y.get()].tolist()
        fig = plt.figure()
        fig.tight_layout()
        # plt.xticks(np.arange(min(X) , max(X) , 2))
        # plt.yticks(np.arange(min(Y) , max(Y) , 2))
        try:
            plt.scatter(X , Y , cmap='RdYlGn')
        except:
            tkinter.messagebox.showerror('Error' , 'متغیرهای دارای تغییرات انتخاب کنید')
            raise ValueError('could not plot with selected variables')
        plt.xlabel(self.x.get() , color='Blue' , labelpad=10 , fontsize=18)
        plt.ylabel(self.y.get() , color='Blue' , labelpad=10 , fontsize=18)
        plt.grid(True)
        plt.show()

    def threeD_plot(self):
        if self.x.get() == self.y.get() or self.x.get() == self.z.get():
            tkinter.messagebox.showerror('Error' , 'متغیر های غیر یکسان برای محورها انتخاب کنید')
            return
        X = self.data[self.x.get()].tolist()
        Y = self.data[self.y.get()].tolist()
        Z = self.data[self.z.get()].tolist()
        fig = plt.figure()
        fig.tight_layout()
        ax = plt.axes(projection='3d')
        ax.tick_params(axis='z' , which='major' , pad=12)
        # plt.xticks(np.arange(min(X) , max(X) , 2))
        # plt.yticks(np.arange(min(Y) , max(Y) , 2))
        # ax.set_zticks(np.arange(10 * 10 ^ 6 , 80000000 , 10000000))
        # ax.ticklabel_format(axis="z" , style="plain")
        try:
            surf = ax.plot_trisurf(X , Y , Z , cmap='RdYlGn')
        except:
            tkinter.messagebox.showerror('Error' , 'متغیرهای دارای تغییرات انتخاب کنید')
            raise ValueError('could not plot with selected variables')
        ax.set_xlabel(self.x.get() , color='Blue' , labelpad=10 , fontsize=18)
        ax.set_ylabel(self.y.get() , color='Blue' , labelpad=10 , fontsize=18)
        ax.set_zlabel(self.z.get() , color='Blue' , labelpad=25 , fontsize=18)
        fig.colorbar(surf , shrink=0.5 , aspect=5)
        fig.tight_layout()
        plt.show()


root = Tk()

plotter(root)

col_count , row_count = root.grid_size()
for col in range(col_count):
    root.grid_columnconfigure(col , minsize=20)
for row in range(row_count):
    root.grid_rowconfigure(row , minsize=25)

mainloop()
