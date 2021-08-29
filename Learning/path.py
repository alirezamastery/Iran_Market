import os
# import symdata

cur_path = os.path.dirname(__file__)
print('cur_path',cur_path)

new_path = os.path.relpath(cur_path , '../Opt_Results/RS_pairs_negative_corr_optimize__20-02-16__13-40.csv' )
print('new_path',new_path)

# path = '..\\Opt_Results\\RS_pairs_negative_corr_optimize__20-02-16__13-40.csv'
with open(new_path , 'r') as file:
    symbols = file.readlines()
# for i in symbols:
#     print(i)
# print(new_path)