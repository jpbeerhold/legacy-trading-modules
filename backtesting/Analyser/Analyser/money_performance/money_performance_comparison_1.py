'''

kann hier einzelne manuell testen und prüfen ob alles richtig ist

kalkulationen sind ziemlich genau an der realität

fees: reduzieren money performance, können nicht money performance ins minus ziehen da es begrenzt ist
slippage: reduzieren money performance, zu viel können money performance extrems verzerren und schnell ins minus führen da slippage variabel ist
-> deshalb extrem gute slippage sind notwendig für das funktionieren einer strategie

fees & slippage:
sind beides zusätzliche loss bzw reduzieren money performance
beide verhindern einen linearen verlauf
vor allem bei überwiegend loss in einem Zeitraum sorgt es für mehr verlust und neigt somit vom linearen verlauf ab

'''

import sys, os, csv, statistics, pandas
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

import matplotlib.pyplot as plt

import _share_files.analyse_functions as afunc
import _share_files.afunc_private as aprivate
from _share_files.analyse_functions import Decistr

ohlc_data_file_path = '/home/jpbeerhold/Desktop/approved data/Bybit/BTCUSDT_PERP/btcusdt_perp_ohlc_1m.txt'

CATT = 1627776000 # 1640995200 Jan2022 # 1627776000 Aug2021 # 1609459200 Jan2021
CBTT = None # 1640995200+(365*86400)

# print(CATT, CBTT)

# file = '_share_files/'
base_path = '/home/jpbeerhold/Downloads/von bots ablage/from filezilla/DoSe/tp mit guaranteed/'
# file = '/home/jpbeerhold/Desktop/Trading/Day Trading/Code/Backtesting/Results n Analyser/Results/Down Settling BR/Bybit BTCUSDT Perp/OHLC + Trading/retests/result files bybit data/'

file = base_path
# file += '52625.txt'
# file += '2082.txt'
# file += '68685.txt'
file += '4582.txt'
# file += '162573.txt'
# file += '16205718.txt'

n = None


afunc.afunc_setup_and_load_trade_history_file(
    '0.1', 1, 1, ohlc_data_file_path,
    file, CATT, CBTT)

while n != None and len(afunc.trade_history) != n:
    del afunc.trade_history[0]

# initial_money = "1000"
# fixed_risk = "60" # größere risk erhöht initial margin # diese hier ändern
max_leverage: int = 100 # größere leverage zieht liq price enger # wird von selbst angepasst wenn liq price nicht passt
maintenance_margin_rate_percent = "0.5" # in %, bei max leverage notwendiges geld von positionsgröße damit position nicht liquidiert wird
min_distance_liq_sl = "200" # in ticks

entry_fee = "0.0" # in %, fees reduzieren bis zu 35% der performance
exit_fee = "0.0" # in %

required_money_use = 'max' # 'mean', 'median', 'max'
drawdown_use = 'max' # 'mean', 'median', 'mode', 'max'

sell_stop_loss_slippage = "3.5" # in %, sell is the exit side on a stop loss hit
buy_stop_loss_slippage = "3.5" # in %, buy is the exit side on a stop loss hit
# used on every stop loss, % of fixed risk of what is being lost additionally, 5-7% for both is recommended use

number_decimals_calc_position_size: int = 3





def test_max_possible_fixed_risk_per_trade(initial_money:str, fixed_risk: str, plot_it = False):

    check = afunc.check_if_risk_and_leverage_doable_single(
        initial_money, fixed_risk, max_leverage, min_distance_liq_sl,
        maintenance_margin_rate_percent, entry_fee, exit_fee,
        sell_stop_loss_slippage, buy_stop_loss_slippage,
        number_decimals_calc_position_size, plot_it)

    return check[0]


# test_max_possible_fixed_risk_per_trade(True)






def show_max_fixed_risk_tests(initial_money: str):
    for i in range(1, int(float(initial_money))):

        fixed_risk = str(i)

        required_stats = afunc.get_order_cost_stats(fixed_risk, max_leverage, maintenance_margin_rate_percent, number_decimals_calc_position_size)

        drawdown = afunc.get_drawdowns_stats(drawdown_use)[drawdown_use]

        drawdown_scope = (Decistr(drawdown)*Decistr(fixed_risk))+Decistr(required_stats['mean'])

        if drawdown_scope <= Decistr(initial_money):
            # print(fixed_risk, drawdown, required_stats, drawdown_scope)
            pass
        else:
            break
    
    return fixed_risk

# show_max_fixed_risk_tests()


# quit()



def get_total_performance():

    start_money = "1000"

    with open('/home/jpbeerhold/Downloads/von bots ablage/from filezilla/DoSe/tp mit guaranteed/'+"check_log_raw.txt") as file:
        data = list(csv.reader(file))

    # filenames = [row[0] for row in data if row[0] in ['2142.txt', '2182.txt', '2185.txt', '2186.txt', '2262.txt', '4123.txt', '4143.txt', '4163.txt', '4582.txt', '4602.txt', '52369.txt', '52625.txt']]
    filenames = [row[0] for row in data]

    all_profits = []

    for file in filenames:
        print(file)
        f = file
        file = '/home/jpbeerhold/Downloads/von bots ablage/from filezilla/DoSe/tp mit guaranteed/'+file

        CATT = 1627776000 # 1640995200 Jan2022 # 1627776000 Aug2021 # 1609459200 Jan2021
        CBTT = None # 1640995200+(365*86400)

        afunc.afunc_setup_and_load_trade_history_file(
        None, None, None, None,
        file, CATT, CBTT)

        r = show_max_fixed_risk_tests(start_money)
        r = Decistr(r)
        r /= 2
        print(r)

        profit = test_max_possible_fixed_risk_per_trade(start_money, r)
        # print(profit)
        profit = Decistr(profit)

        all_profits.append((f, profit))

    # print(all_profits)
    print("profit", sum([i[1] for i in all_profits]))



# get_total_performance()







def plot_total_performance():

    with open('/home/jpbeerhold/Downloads/von bots ablage/from filezilla/DoSe/tp mit guaranteed/'+"check_log_raw.txt") as file:
        data = list(csv.reader(file))

    # filenames = [row[0] for row in data if row[0] in ['2142.txt', '2182.txt', '2185.txt', '2186.txt', '2262.txt', '4123.txt', '4143.txt', '4163.txt', '4582.txt', '4602.txt', '52369.txt', '52625.txt']]
    filenames = [row[0] for row in data]

    start_capital = Decistr("1000")/len(filenames)

    CATT = 1627776000 # 1640995200 Jan2022 # 1627776000 Aug2021 # 1609459200 Jan2021
    CBTT = None # 1640995200+(365*86400)

    all_paths_with_risks = []

    for i in range(len(filenames)):
        file = '/home/jpbeerhold/Downloads/von bots ablage/from filezilla/DoSe/tp mit guaranteed/'+filenames[i]

        afunc.afunc_setup_and_load_trade_history_file(
        None, None, None, None,
        file, CATT, CBTT)

        # if filenames[i] == '4582.txt':
        #     continue
        # if filenames[i] == '2182.txt':
        #     continue

        r = show_max_fixed_risk_tests(start_capital)
        r = Decistr(r)
        r /= 2
        
        all_paths_with_risks.append((file, r))

    profit_course = afunc.get_profit_course_with_multiple(
        start_capital, all_paths_with_risks, CATT, CBTT,
        max_leverage, min_distance_liq_sl, maintenance_margin_rate_percent, entry_fee, exit_fee,
        sell_stop_loss_slippage, buy_stop_loss_slippage, number_decimals_calc_position_size)[3]


    performance_in_risk_values_list = []
    datetime_list = []
    p = 0

    for date_profit in profit_course:
        p += date_profit[1]
        performance_in_risk_values_list.append(p)
        datetime_list.append(aprivate.get_timestamp_to_datetime(date_profit[0]))

    print("last:", p)

    dataframe = pandas.DataFrame() # nur als tool für conversion & plotting
    dataframe["Perf"] = performance_in_risk_values_list
    dataframe["Dates"] = datetime_list

    # convert object to datetime64[ns]
    dataframe["Dates"] = pandas.to_datetime(dataframe["Dates"])

    dates = dataframe["Dates"]
    perf = dataframe["Perf"]
    
    # plt.figure(figure_number)
    plt.plot(dates, perf, label='Performance')

    # plt.title(title)
    plt.xlabel("Time")
    plt.ylabel("Performance")
    plt.legend()
    plt.xticks(rotation=45)
    plt.show()


# plot_total_performance()







def get_total_volume_each_month():

    with open(base_path+"check_log_raw.txt") as file:
        data = list(csv.reader(file))

    filenames = [row[0] for row in data]
    # filenames = [row[0] for row in data if row[0] in ['2142.txt', '2182.txt', '2185.txt', '2186.txt', '2262.txt', '4123.txt', '4143.txt', '4163.txt', '4582.txt', '4602.txt', '52369.txt', '52625.txt']]

    start_money = Decistr("70000")/len(filenames)

    CATT = 1627776000 # 1640995200 Jan2022 # 1627776000 Aug2021 # 1609459200 Jan2021
    CBTT = None # 1640995200+(365*86400)

    total_per_month = []

    for file in filenames:

        file = base_path+file

        afunc.afunc_setup_and_load_trade_history_file(
        '0.5', 1, 1, ohlc_data_file_path,
        file, CATT, CBTT)

        r = show_max_fixed_risk_tests(start_money)
        r = Decistr(r)
        r /= 2
        print(r)

        current_volume_per_month = afunc.get_trading_volume_per_month(
        start_money, r, max_leverage,
        min_distance_liq_sl, maintenance_margin_rate_percent,
        sell_stop_loss_slippage, buy_stop_loss_slippage,
        number_decimals_calc_position_size)

        # print(file)
        # print(current_volume_per_month)
        # quit()

        if len(total_per_month) == 0:
            for item in current_volume_per_month:
                total_per_month.append([item[0], Decistr(item[1])])
        else:
            found = False
            for item in current_volume_per_month:
                for m in total_per_month:
                    if m[0] == item[0]:
                        m[1] += Decistr(item[1])
                        found = True
                        break
                if found == False:
                    print(item)
                    raise

    print(total_per_month)


# get_total_volume_each_month()





def show_avg_perf_per_year():
    start_capital = "1000"

    with open('/home/jpbeerhold/Downloads/von bots ablage/from filezilla/DoSe/tp mit guaranteed/'+"check_log_raw.txt") as file:
        data = list(csv.reader(file))

    filenames = [row[0] for row in data]

    CATT = 1627776000 # 1640995200 Jan2022 # 1627776000 Aug2021 # 1609459200 Jan2021
    CBTT = None # 1640995200+(365*86400)

    all_per_year = []

    for i in range(len(filenames)):

        # if filenames[i] != "2082.txt":
        #     continue

        file = '/home/jpbeerhold/Downloads/von bots ablage/from filezilla/DoSe/tp mit guaranteed/'+filenames[i]

        afunc.afunc_setup_and_load_trade_history_file(
        None, None, None, None,
        file, CATT, CBTT)

        fixed_risk = show_max_fixed_risk_tests(start_capital)
        fixed_risk = Decistr(fixed_risk)
        fixed_risk /= 2
        print(fixed_risk)

        stats = afunc.get_risk_and_reward_value_ticks_of_last_two_months()
        fixed_win = fixed_risk*Decistr(stats["REWARD"]["size"])

        stats = afunc.get_number_win_loss_breakeven()

        abs_win_quote = Decistr(stats["abs win quote %"])/100

        trades_per_month = Decistr(stats["position trades"]) / 24 # Anzahl Monate hier anpassen

        number_wins = abs_win_quote*trades_per_month
        number_losses = (1-abs_win_quote)*trades_per_month        

        money_per_month = (number_wins*fixed_win)-(number_losses*fixed_risk)
        all_per_year.append((filenames[i], money_per_month*12))
    
    print(all_per_year)


# show_avg_perf_per_year()




