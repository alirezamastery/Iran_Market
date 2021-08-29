from tkinter import *
from tkinter import ttk
import tkinter.messagebox
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import sys
import os
import math
import time
import pandas as pd
import datetime as dt
import dropbox


# with open('200_sherkat.txt' , 'r') as file:
#     symbols = file.readlines()
#     symbols = [x.strip() for x in symbols]
#
# for i,sym in enumerate(symbols):
#     for j in range(i+1 , len(symbols)):
#         if sym == symbols[j]:
#             print(sym,j,i)


def refresh_data(file_name='200.txt'):
    # read symbol names in the file:
    with open(file_name , 'r') as file:
        symbols = file.readlines()
    symbols = [x.strip() for x in symbols]
    # get the list of files in target dropbox folder:
    ACCESS_TOKEN = 'dPdfl4gIvmAAAAAAAAAAHKdNE3BWJ0v9ngpeZwqOrXv4ks3x_1XT6erwPecaK5GW'
    dbx = dropbox.Dropbox(ACCESS_TOKEN)
    dbx.users_get_current_account()
    response = dbx.files_list_folder(path='/Data Rahavard/Rahavard/Eslahi/')
    source_files = []
    for file in response.entries:
        source_files.append(file.name.replace('.txt' , ''))
    if response.has_more:
        s2 = dbx.files_list_folder_continue(response.cursor)
        while s2.has_more:
            for file in s2.entries:
                source_files.append(file.name.replace('.txt' , ''))
            s2 = dbx.files_list_folder_continue(s2.cursor)
        else:
            m_final = dbx.files_list_folder_continue(s2.cursor)
            for file in m_final.entries:
                source_files.append(file.name.replace('.txt' , ''))

    source_files = sorted(source_files)
    for i,d in enumerate(source_files):
        print(d)
    print(len(source_files))
    print('-' * 20)
    print('these files are not in the Folder:')
    # check if file names are in dropbox folder:
    for i , sym in enumerate(symbols):
        if sym not in source_files:
            print(sym)
            symbols.pop(i)



refresh_data()
