'''

vergleichen welche Strategie wie performt hat mit Rücksicht auf

mögliche risk per trade anhand von losses (abs win quote & drawdowns) um nach losses immer noch
gewollte risk kreieren zu können


inputs sind result files

Veränderbar:
check_if_risk_and_leverage_doable() -> bool double_risk_on_half
get_required_money_stats() -> using mean, median or max
get_drawdowns_stats() -> using mean, median, mode or max
& Variablen

'''

import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '../'))

# PC
# import _share_files.analyse_functions as afunc
# from _share_files.analyse_functions import Decistr

# Instance
import analyse_functions as afunc
from analyse_functions import Decistr


import csv, time
from os import walk



# # # CHANGE # # #
path_to_result_files = '/home/run/bt/bt_results/'




initial_money = "1000" # in $
max_leverage = "100"
maintenance_margin_rate_percent = "0.5" # in %
min_distance_liq_sl = "100" # in ticks

entry_fee = "0.01" # in %
exit_fee = "0.01" # in %

double_risk = False
required_money_use = 'max' # 'mean', 'median', 'max'
drawdown_use = 'max' # 'mean', 'median', 'mode', 'max'

sell_stop_loss_slippage = "5" # in %, sell is the exit side on a stop loss hit
buy_stop_loss_slippage = "2" # in %, buy is the exit side on a stop loss hit
# used on every stop loss, this is what is being lost additionally
# in % relative to risk value ticks





def get_max_possible_fixed_risk(initial_money: str, drawdown: str, min_distance_liq_sl: str, leverage: str, maintenance_margin_rate_percent: str):

    max = 0
    initial_money = Decistr(initial_money)

    for fixed_risk in range(1, int(initial_money)): # einfach nur eine hohe zahl, int wenn stellen nach komma hat

        required_stats = afunc.get_required_money_stats(required_money_use, fixed_risk, min_distance_liq_sl, leverage, maintenance_margin_rate_percent)

        drawdown_scope = (Decistr(drawdown)*Decistr(fixed_risk))+Decistr(required_stats)

        if drawdown_scope <= initial_money:
            if fixed_risk > max:
                max = fixed_risk

    return max








def get_money_performance_results(start_timestamp: int, end_timestamp: int, time_range: int, increment: int):

    counter = 0
    for tp in range(start_timestamp, end_timestamp, increment):
        counter += 1


        CATT = tp
        CBTT = CATT+time_range



        with open(f'money_performance_results_{counter}.txt', 'w') as f:
            f.write(f'CATT: {CATT}\n')
            f.write(f'CBTT: {CBTT}\n')
            f.write(f'initial_money: {initial_money}\n')
            f.write(f'max_leverage: {max_leverage}\n')
            f.write(f'maintenance_margin_rate_percent: {maintenance_margin_rate_percent}\n')
            f.write(f'min_distance_liq_sl: {min_distance_liq_sl}\n')
            f.write(f'entry_fee: {entry_fee}\n')
            f.write(f'exit_fee: {exit_fee}\n')
            f.write(f'double_risk_on_half: {double_risk}\n')
            f.write(f'required_money_use: {required_money_use}\n')
            f.write(f'drawdown_use: {drawdown_use}\n')
            f.write('\n')




        # bereits analyse_results_overview.py angewendet
        # und nur bestimme untersuchen, zB nur mit positive performance & genug trades
        # # # CHANGE # # #
        with open('results_overview.txt') as f:
            filter_data = list(csv.reader(f))
        del filter_data[0:3]

        filenames = [item[0] for item in filter_data if float(item[3]) > 0]
        # auf r_squared zu beschränken macht keinen sinn!


        # using result files in _share_files folder
        # filenames = next(walk(path_to_result_files), (None, None, []))[2]
        # filenames = [item for item in filenames if '.txt' in item]



        temp_results_save = []

        for file in filenames:
            # print(file)

            if '.txt' not in file or 'plot' in file or 'money' in file:
                continue


            if afunc.load_trade_history_file(path_to_result_files+file, CATT, CBTT) == 'empty':
                continue

            drawdown = afunc.get_drawdowns_stats(drawdown_use)
            if drawdown == 'empty':
                continue
            else:
                drawdown = drawdown[drawdown_use]



            max_fixed_risk = get_max_possible_fixed_risk(initial_money, drawdown, min_distance_liq_sl, max_leverage, maintenance_margin_rate_percent)
            # print(file, max_fixed_risk)



            for _ in range(int(initial_money)):
                check_if_doable = afunc.check_if_risk_and_leverage_doable(initial_money, max_fixed_risk, max_leverage, maintenance_margin_rate_percent, min_distance_liq_sl,
                                                                          entry_fee, exit_fee, sell_stop_loss_slippage, buy_stop_loss_slippage, double_risk_on_half=double_risk)

                if check_if_doable == 'no money':
                    max_fixed_risk -= 1
                else:
                    profit = round(Decistr(check_if_doable[0]))
                    number_changed = check_if_doable[1]

                    if max_fixed_risk == 0:
                        break
                    elif profit < 0:
                        max_fixed_risk -= 1
                    else:
                        break

            # print('done')
            temp_results_save.append( (file, profit, max_fixed_risk, drawdown, number_changed) )



        temp_results_save.sort(key=lambda x : x[1], reverse=True)


        with open(f'money_performance_results_{counter}.txt', 'a') as f:
            for item in temp_results_save:
                for i in range(len(item)):
                    f.write(str(item[i]))
                    if i != len(item)-1:
                        f.write(',')
                f.write('\n')




# # # CHANGE # # #
get_money_performance_results(
    start_timestamp=1640995200,
    end_timestamp=1672531200,
    time_range=86400*30*6, # 6 Monate untersuchen
    increment=86400*30*3 # alle drei Monate
)





# get_money_performance_results(
#     start_timestamp=1672527600,
#     end_timestamp=1672527600+(12*30*86400),
#     time_range=86400*30*12, # 6 Monate untersuchen
#     increment=86400*30*12 # alle drei Monate
# )