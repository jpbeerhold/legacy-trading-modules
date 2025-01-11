import csv, statistics
from os import walk
from decimal import Decimal


path = '/home/jpbeerhold/Desktop/LIVE SERVER/live bots results/ByBit/Down Settling/2185/'


folders = next(walk(path), (None, None, []))[1]


all_stop_loss_fills_data = []


for current_folder in folders:
    files = next(walk(path+current_folder), (None, None, []))[2]
    if 'stop_loss_fills.txt' in files:
        with open(path+current_folder+'/stop_loss_fills.txt') as f:
            data = list(csv.reader(f))
            all_stop_loss_fills_data.extend(data)




# print(all_stop_loss_fills_data[0])




sell_exit_slippage_percent = []
buy_exit_slippage_percent = []
all_durations = []

for row in all_stop_loss_fills_data:
    exit_side = row[2]
    slippage = Decimal(row[6])
    risk_value_ticks = Decimal(row[8])
    all_durations.append(Decimal(row[10]))

    # bei Sell ist negative Slippage schlecht
    if exit_side == 'Sell':
        sell_exit_slippage_percent.append( (slippage/risk_value_ticks) *100)

    # bei Buy ist positive Slippage schlecht
    elif exit_side == 'Buy':
        buy_exit_slippage_percent.append( (slippage/risk_value_ticks) *100)









print(len(all_stop_loss_fills_data))


print()


print('schlechteste')
print('Sell', round( min(sell_exit_slippage_percent), 2), '%')
print('Buy', round( max(buy_exit_slippage_percent), 2), '%' )


print()


print('beste')
print('Sell', round( max(sell_exit_slippage_percent), 2), '%' )
print('Buy', round( min(buy_exit_slippage_percent), 2), '%' )


print()


print('average')
print('Sell', round( statistics.mean(sell_exit_slippage_percent), 2), '%' )
print('Buy', round( statistics.mean(buy_exit_slippage_percent), 2), '%' )


print()


print('duration time in seconds')
print('average', round( statistics.mean(all_durations), 3) )
print('max', round( max(all_durations), 3) )
print('min', round( min(all_durations), 3) )
