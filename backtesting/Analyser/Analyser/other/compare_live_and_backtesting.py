'''

live und backtesting trade history vergleichen

live_path ändern und in z.txt backtesting results rein

'''

import csv

live_path = '/home/jpbeerhold/Desktop/Trading/Day Trading/Code/Backtesting/Results n Analyser/Analyser/other/z.txt'

bt_path = '/home/jpbeerhold/Desktop/Trading/Day Trading/Code/Backtesting/Results n Analyser/Analyser/other/z2.txt'



with open(live_path) as f:
    live_data = list(csv.reader(f))

with open(bt_path) as f:
    bt_data = list(csv.reader(f))









# assert len(live_data) == len(bt_data)

to_raise = None
for i in range(len(live_data)):
    is_different = False
    pos_trade_live = live_data[i]
    pos_trade_bt = bt_data[i]

    side_live = pos_trade_live[0]
    side_bt = pos_trade_bt[0]

    entry_live = pos_trade_live[2]
    entry_bt = pos_trade_bt[2]

    sl_live = pos_trade_live[3]
    sl_bt = pos_trade_bt[3]

    size_live = pos_trade_live[4]
    size_bt = pos_trade_bt[4]


    if side_live != side_bt:
        is_different = True
    elif entry_live != entry_bt:
        is_different = True
    elif sl_live != sl_bt:
        is_different = True
    elif size_live != size_bt:
        is_different = True

    if is_different:
        print(side_live, side_bt)
        print(pos_trade_live[1], pos_trade_bt[1])
        print(entry_live, entry_bt)
        quit()


print(live_data[-1])    
print(bt_data[-1])



