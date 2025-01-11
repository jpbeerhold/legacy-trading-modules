
'''
use this on PC
'''



import csv

basic_path = '/home/jpbeerhold/Desktop/Trading/Day Trading/Code/Backtesting/Results n Analyser/Results/'
# basic_path = ''

# strategy path
basic_path += 'Down Settling BR/Bybit BTCUSDT Perp/OHLC + Trading/'

# folder path
basic_path += '70335-162495/'



input_file = basic_path+'results_overview_Jan2021-Apr2023.txt'
# input_file = basic_path+'results_overview_Jan-Jul2022.txt'

output_file = basic_path+'filter_Jan2021-Apr2023.txt'
# output_file = basic_path+'filter_Jan-Jul2022.txt'




with open(input_file) as f:
    results_data = list(csv.reader(f))

with open(output_file, 'w') as f:
    for x in range(3):
        for i in range(len(results_data[x])):
            f.write(results_data[x][i])
            if i != len(results_data[x])-1:
                f.write(',')
        f.write('\n')

del results_data[0:3]

print(len(results_data))


# from os import walk
# mypath = '/home/jpbeerhold/Downloads/von bots ablage/from filezilla/inspect/'

# filenames = next(walk(mypath), (None, None, []))[2]





# Filter

for i in range(len(results_data)-1, -1, -1):

    if 'no trades' in results_data[i] or 'nan' in results_data[i]:
        del results_data[i]
        continue



    perf = float(results_data[i][3])
    num_pos_tra = float(results_data[i][4])
    risk_value_ticks = float(results_data[i][5])
    r_squared = float(results_data[i][-1])
    abs_win_quote = float(results_data[i][1])


    # if not abs_win_quote > 30:
    #     del results_data[i]
    #     continue

    # if not num_pos_tra > 200:
    #     del results_data[i]
    #     continue

    # if not perf > 0:
    #     del results_data[i]
    #     continue

    # if not r_squared > 0.95:
    #     del results_data[i]
    #     continue










# Sortierung

# results_data.sort(key=lambda x: float(x[-1]), reverse=True)

results_data.sort(key=lambda x: float(x[3]), reverse=True)

# results_data.sort(key=lambda x: float(x[1]), reverse=True)







with open(output_file, 'a') as f:
    for row in results_data:
        for i in range(len(row)):
            f.write(row[i])
            if i != len(row)-1:
                f.write(',')
        f.write('\n')


