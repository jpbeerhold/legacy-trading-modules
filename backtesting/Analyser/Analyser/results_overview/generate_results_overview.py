
from os import walk
import analyse_functions as afunc
import time

'''
use this on instance

generiert overview von allen files im angegebene path

nötwendige Angaben:
path_to_all_files
count_after_this_timestamp
'''




path_to_all_files = '/home/run/bt/bt_results/'

### since Jan 2021
CATT = 1609459200

### since Aug 2021
# CATT = 1627776000

### since Jan 2022
# CATT = 1640995200




# CBTT = CATT+(86400*30*6)
CBTT = int(time.time())












final_list = []
filenames = iter(next(walk(path_to_all_files), (None, None, []))[2])

for file_name in filenames:
    file = path_to_all_files + file_name

    if afunc.load_trade_history_file(file, CATT, CBTT) == None:

        data_count = afunc.get_win_loss_breakeven()
        abs_win_quote = data_count['abs win quote %']
        reward_size = afunc.get_reward_size()
        num_pos_tra = data_count['position trades']

        perf = afunc.get_sum_of_performance_in_risk_values()
        # reg_func = bda.get_regression_function()
        # correlation = get_correlation()
        r_squared = afunc.get_r_squared()

        if r_squared != 'no trades':
            r_squared = round(r_squared, 2)

        value_ticks = afunc.get_RISK_and_REWARD_value_ticks_of_last_two_months()
        risk_value_ticks = value_ticks['RISK']['mean']
        reward_value_ticks = value_ticks['REWARD']['mean']

        if risk_value_ticks != 'no trades':
            risk_value_ticks = risk_value_ticks
        if reward_value_ticks != 'no trades':
            reward_value_ticks = reward_value_ticks

        final_list.append( (file_name, abs_win_quote, reward_size, perf, num_pos_tra, risk_value_ticks, reward_value_ticks, r_squared) )


with open('results_overview.txt', 'w') as f:
    f.write('CATT: '+str(CATT)+'\n')
    f.write('CBTT: '+str(CBTT)+'\n')
    f.write('file_name,abs_win_quote,reward_size,perf,num_pos_tra,risk_value_ticks,reward_value_ticks,r_squared\n')

with open('results_overview.txt', 'a') as f:
    for row in final_list:
        for i in range(len(row)):
            f.write(str(row[i]))
            if i != len(row)-1:
                f.write(',')
        f.write('\n')


print('done')








