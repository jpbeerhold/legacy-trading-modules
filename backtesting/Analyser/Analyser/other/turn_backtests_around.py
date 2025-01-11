'''

use this if you want to turn result files the other way around
-> entry stays same
-> stop loss becomes take profit
-> take profit becomes stop loss

!!! does not work for trailing stop loss

this is not a backtest, but reading file & turning around

rundungen round() selber anpassen
'''

import csv, math
from os import walk
from decimal import Decimal

def Decistr(n):
    return Decimal(str(n))



# all files in this folder
input_path = '/home/run/results collection/bt_results ohlc + trading/46145-64577/'

# put into this folder
output_path = '/home/run/results collection/bt_results ohlc + trading/46145-64577_turned/'


print("Using input_path", input_path)
print("Using output_path", output_path)




filenames = next(walk(input_path), (None, None, []))[2]



for file_name in filenames:

    with open(input_path+file_name) as f:
        f_data = list(csv.reader(f))
    
    for row in f_data:

        if math.isnan(float(row[8])):
            continue

        entry_side = row[0]
        entry = Decistr(row[2])
        sl = Decistr(row[3])
        exit_price = Decistr(row[6])
        tp = Decistr(row[10])
        result = row[9]

        new_sl = tp
        new_tp = sl

        new_risk_value_ticks = abs(entry-new_sl)


        if entry_side == 'long':
            entry_side = 'short'
            new_performance = (entry-exit_price)/new_risk_value_ticks
        else:
            entry_side = 'long'
            new_performance = (exit_price-entry)/new_risk_value_ticks


        if new_performance > 0:
            new_result = 'win'
        elif new_performance < 0:
            new_result = 'loss'
        else:
            new_result = 'breakeven'



        new_performance = round(new_performance, 3)     # <<<<



        row[0] = entry_side
        row[3] = str(new_sl)
        row[4] = str(new_risk_value_ticks)
        row[8] = str(new_performance)
        row[9] = str(new_result)
        row[10] = str(new_tp)

    tstr = file_name.replace('.txt', '_turned.txt')

    with open(output_path+tstr, 'w') as f:
        f.write("")

    with open(output_path+tstr, 'a') as f:
        for row in f_data:
            for i in range(len(row)):
                f.write(row[i])
                if i != len(row)-1:
                    f.write(',')
            f.write('\n')





