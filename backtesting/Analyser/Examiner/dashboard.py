
import sys, os, csv
sys.path.append(os.path.join(os.path.dirname(__file__), '../'))

import matplotlib.pyplot as plt

from os import walk
from decimal import Decimal
import _share_files.analyse_functions as afunc

"""

es gibt einen festen Anteil (reduction) weniger an performance durch fees (& slippage, je nach dem wie gut/schlecht)
(feste zahl bzw differenz zwischen raw & actual performance, diese differenz ist die summe aller cost barriers)

dieser ist unterschiedlich je nach result

man kann nichts dagegen machen außer weniger fees zu erhalten

dennoch, erhöhte performance, also mehr performance nach cost barrier, sorgt für mehr actual performance
und somit wird dieser feste Anteil (reduction) immer kleiner relativ zur performance
ebenso wird der verlauf sehr linear bzw losses sind schwächer

"""










def plot_single() -> None:

     ohlc_data_file_path = '/home/jpbeerhold/Desktop/Market Data/Bybit/BTCUSDT_PERP/btcusdt_perp_ohlc_1m.txt'

     # path = '/home/jpbeerhold/Desktop/Trading/Day Trading/Code/Backtesting/Results n Analyser/Results/Down Settling BR/Bybit BTCUSDT Perp/OHLC + Trading/retests/result files bybit data/'
     path = '/home/jpbeerhold/Downloads/von bots ablage/from filezilla/DoSe/tp mit guaranteed/'

     with open(path+"check_log_raw.txt") as f:
          data = list(csv.reader(f))

     filenames = [row[0] for row in data]
     # filenames = [row[0] for row in data if row[0] == '2082.txt']

     change_win_performance = None
     # change_win_performance = Decimal("0.5")

     # filenames = next(walk(path), (None, None, []))[2]
     # filenames = [(item, None) for item in filenames if '15834' in item]
     # print(filenames)


     for file in filenames:

          title = file
          # title = file[0]
          
          # n = file[1]
          n = None

          tick_value = '0.5'
          time_frame = 1

          print('File:')
          print(title)

          # 1640995200 Jan2022 # 1627776000 Aug2021 # 1609459200 Jan2021
          import time
          CATT = int(time.time())-(86400*6*30) # 1627776000 # 1640995200 # 1672527600
          CBTT = None # CATT+(365*86400)

          if CATT != None or CBTT != None:
               n = None

          plot_check_fees_slippage(title, path, n, change_win_performance, tick_value, time_frame, 1, None, CATT, CBTT)

          file = path+title

          afunc.afunc_setup_and_load_trade_history_file(
               tick_value, time_frame, 1, ohlc_data_file_path,
               file, CATT, CBTT)

          # wegen find_linear_progression.py log
          if n != None:
               while len(afunc.trade_history) != n:
                    del afunc.trade_history[0]

          if change_win_performance != None:
               for pos_trade in afunc.trade_history:
                    if pos_trade[9] == 'win':
                         pos_trade[8] = change_win_performance


          print('r² raw:')
          print(afunc.get_r_squared())
          print()
          print("Performance raw:")
          print(afunc.get_risk_value_performance())
          print()
          print("Trades numbers:")
          print(afunc.get_number_win_loss_breakeven())
          print()
          print('Value Sizes:')
          print(afunc.get_risk_and_reward_value_ticks_of_last_two_months())
          print()
          print('Duration stats:')
          print(afunc.get_duration_stats())
          print()
          each_month = afunc.get_risk_value_performance_each_month()
          print(f'Performance for {len(each_month)-1} months:')
          print(each_month)
          print()
          print('Drawdown stats:')
          print(afunc.get_drawdowns_stats(title, plot_drawdowns_distribution=False))
          print()
          print('Win fee drain stats:')
          print(afunc.get_win_fee_drain_stats('0.02'))
          print()
          print("-------------------------\n")

          # plot_position_trade(file)

          afunc.plot_risk_value_performance_with_dates(title, show_chart=False)
          afunc.plot_risk_value_performance_with_regression_line(title, "raw performance")














def plot_position_trade(path: str):

     for i in range(5717, 0, -1):
          print(i)
          afunc.plot_candle_chart(result_file_path=path,
               position_number=i, number_candles_before=100, number_candles_after=100, show_horizontal_lines=True)

















def plot_check_fees_slippage(
     file_name, file_path, number_pos_trades, change_win_performance,
     tick_value, time_frame, ohlc_data_time_fame, ohlc_data_path,
     count_after_this_timestamp, count_before_this_timestamp
     ):

     slippage_percentage = "3.5" # in %
     fee_rate = "0.0" # in %

     slippage_percentage = Decimal(slippage_percentage)/100
     fee_rate = Decimal(fee_rate)/100

     afunc.afunc_setup_and_load_trade_history_file(tick_value, time_frame, ohlc_data_time_fame, ohlc_data_path, file_path+file_name, count_after_this_timestamp, count_before_this_timestamp)
     # total_number_pos_trades = len(afunc.trade_history)

     if number_pos_trades != None:
          while len(afunc.trade_history) != number_pos_trades:
               del afunc.trade_history[0]

     if change_win_performance != None:
          for pos_trade in afunc.trade_history:
               if pos_trade[9] == 'win':
                    pos_trade[8] = change_win_performance


     # performance nach fees & slippage anpassen

     for pos_trade in afunc.trade_history:
          entry = pos_trade[2]
          risk_value_ticks = pos_trade[4]
          exit_price = pos_trade[6]
          actual_performance = pos_trade[8]

          if pos_trade[9] == 'loss':
               actual_performance -= slippage_percentage
          
          fee_barrier = (entry*fee_rate)+(exit_price*fee_rate)
          fee_barrier /= risk_value_ticks
          actual_performance -= fee_barrier
          pos_trade[8] = actual_performance


     print()
     print('r² actual:')
     print(afunc.get_r_squared())
     print()
     print("Performance actual:")
     print(afunc.get_risk_value_performance())
     print()

     # afunc.plot_risk_value_performance_with_dates(file_name, show_chart=False)
     afunc.plot_risk_value_performance_with_regression_line(file_name, "actual performance", show_chart=False)






plot_single()












def plot_total_performance():

     slippage_percentage = "3.5" # in %
     fee_rate = "0.0" # in %

     slippage_percentage = Decimal(slippage_percentage)/100
     fee_rate = Decimal(fee_rate)/100

     with open('/home/jpbeerhold/Downloads/von bots ablage/from filezilla/DoSe/tp mit guaranteed/'+"check_log_raw.txt") as file:
          data = list(csv.reader(file))

     # filenames = [row[0] for row in data if row[0] in ['2142.txt', '2182.txt', '2185.txt', '2186.txt', '2262.txt', '4123.txt', '4143.txt', '4163.txt', '4582.txt', '4602.txt', '52369.txt', '52625.txt']]
     filenames = [row[0] for row in data]

     all_trades = []

     for file in filenames:
          file = '/home/jpbeerhold/Downloads/von bots ablage/from filezilla/DoSe/tp mit guaranteed/'+file

          CATT = 1627776000 # 1640995200 Jan2022 # 1627776000 Aug2021 # 1609459200 Jan2021
          CBTT = None # 1640995200+(365*86400)

          afunc.afunc_setup_and_load_trade_history_file(
          None, None, None, None,
          file, CATT, CBTT)

          for pos_trade in afunc.trade_history:

               entry = pos_trade[2]
               risk_value_ticks = pos_trade[4]
               exit_price = pos_trade[6]
               actual_performance = pos_trade[8]

               if pos_trade[9] == 'loss':
                    actual_performance -= slippage_percentage
               
               fee_barrier = (entry*fee_rate)+(exit_price*fee_rate)
               fee_barrier /= risk_value_ticks
               actual_performance -= fee_barrier
               pos_trade[8] = actual_performance

               all_trades.append((pos_trade[1], pos_trade[8]))
          
     all_trades.sort(key=lambda x : x[0])

     p = 0
     perf_course = []
     for item in all_trades:
          p += item[1]
          perf_course.append(p)

     print('perf:', p)

     plt.plot(perf_course)
     plt.show()


# plot_total_performance()






