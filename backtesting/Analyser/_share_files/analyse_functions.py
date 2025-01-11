'''
side, entry_time, entry_price, stop_loss_price, risk_value_ticks, exit_time, exit_price, duration_minutes, performance, result, take profit, (ema20), (ema50), ...
0   , 1         , 2          , 3              , 4               , 5        , 6         , 7               , 8          , 9     , 10         , (11)   , (12)   , ...
'''

import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ""))

import matplotlib.pyplot as plt
import mplfinance as mpf
import csv, math, numpy, time, pandas, statistics, afunc_private

from typing import Dict, List
from datetime import datetime
from decimal import InvalidOperation
from scipy import stats
from sklearn import linear_model
from collections import Counter
from afunc_private import Decistr

def warn(*args, **kwargs):
    pass
import warnings
warnings.warn = warn





"""

alle Berechnungen sind valide für Bybit Isolated Margin Mode

alle Zahlen als String zu Decimal geben
keine floats benutzen, da Nachkommastellen weggelassen werden

mit for in loops kann man Werte nicht ändern !

"""







def afunc_setup_and_load_trade_history_file(
        p_tick_value: str, p_time_frame: int, p_ohlc_data_time_frame: int, p_ohlc_data_file_path: str,
        trade_history_file_path: str, count_after_this_timestamp: int = None, count_before_this_timestamp: int = None):
    '''
    Trade history file = Backtesting results file
    '''
    global trade_history, number_decimals_perf, tick_value, time_frame, ohlc_data_time_frame, ohlc_data_file_path

    if p_time_frame != None and p_ohlc_data_time_frame != None:
        assert p_time_frame >= p_ohlc_data_time_frame

    if p_tick_value != None:
        afunc_private.afunc_private_setup(p_tick_value, p_time_frame, p_ohlc_data_time_frame, p_ohlc_data_file_path)

    tick_value = p_tick_value
    time_frame = p_time_frame
    ohlc_data_time_frame = p_ohlc_data_time_frame
    ohlc_data_file_path = p_ohlc_data_file_path



    if count_after_this_timestamp != None and count_before_this_timestamp != None:
        assert count_after_this_timestamp < count_before_this_timestamp

    with open(trade_history_file_path) as csvfile:
        trade_history = list(csv.reader(csvfile))

    for i in range(len(trade_history)-1, -1, -1):
        try:
            entry_timestamp = Decistr(trade_history[i][1])

            if math.isnan(float(trade_history[i][8])) == True:
                del trade_history[i]

            elif count_after_this_timestamp != None and count_before_this_timestamp != None:
                if entry_timestamp < count_after_this_timestamp or entry_timestamp > count_before_this_timestamp:
                    del trade_history[i]

            elif count_after_this_timestamp != None:
                if entry_timestamp < count_after_this_timestamp:
                    del trade_history[i]

            elif count_before_this_timestamp != None:
                if entry_timestamp > count_before_this_timestamp:
                    del trade_history[i]

        except IndexError:
            del trade_history[i]

    for pos_trade in trade_history:
        for i in range(len(pos_trade)):
            try:
                pos_trade[i] = Decistr(pos_trade[i])
            except InvalidOperation:
                pass

    if len(trade_history) == 0:
        return 'empty'

    number_decimals_perf = abs(trade_history[-1][8].as_tuple().exponent)


















'''
PLOTTING PERFORMANCE & CANDLES
'''





def plot_risk_value_performance_with_dates(title: str = "", plot_regression_line: bool = False, show_chart: bool = True, figure_number: int = 1):

    performance_in_risk_values_list = []
    datetime_list = []
    p = 0

    for pos_trade in trade_history:
        p += pos_trade[8]
        performance_in_risk_values_list.append(p)
        datetime_list.append(afunc_private.get_timestamp_to_datetime(pos_trade[1]))

    dataframe = pandas.DataFrame() # nur als tool für conversion & plotting
    dataframe["Perf"] = performance_in_risk_values_list
    dataframe["Dates"] = datetime_list

    # convert object to datetime64[ns]
    dataframe["Dates"] = pandas.to_datetime(dataframe["Dates"])

    dates = dataframe["Dates"]
    perf = dataframe["Perf"]
    
    plt.figure(figure_number)
    plt.plot(dates, perf, label='Performance')

    if plot_regression_line == True:
        dataframe["Perf"] = afunc_private.get_regression_line(trade_history)
        perf = dataframe["Perf"]
        plt.plot(dates, perf, label="regression line")

    plt.title(title)
    plt.xlabel("Time")
    plt.ylabel("Performance")
    plt.legend()
    plt.xticks(rotation=45)
    if show_chart == True:
        plt.show()





def plot_risk_value_performance_with_regression_line(title: str = "", label: str = None, show_chart: bool = True, figure_number: int = 2):
    y_axis = afunc_private.get_regression_line(trade_history)
    x_axis = [i for i in range(1, len(y_axis)+1)]

    perf_y = afunc_private.get_risk_value_performance_as_list(trade_history)
    perf_x = [i for i in range(1, len(perf_y)+1)]
    plt.figure(figure_number)
    plt.title(title)
    plt.plot(perf_x, perf_y, label=label)
    plt.plot(x_axis, y_axis)
    plt.legend()
    if show_chart:
        plt.show()





def plot_candle_chart(result_file_path: str, position_number: int, number_candles_before: int, number_candles_after: int, show_horizontal_lines: bool = True):
    '''
    Use this to plot ohlc data

    > Infos on how to modify the appearance of the chart:
        https://coderzcolumn.com/tutorials/data-science/candlestick-chart-in-python-mplfinance-plotly-bokeh
        https://github.com/matplotlib/mplfinance/blob/master/examples/using_lines.ipynb
    
    > Candlestick plotting expects input data in form of Dataframe from pandas
    '''

    path_for_file = sys.path[0]+'/ohlc_candle_plotting.txt'


    def __get_position_specs(position_number: int) -> List:
        '''
        Returns the row of the given position number in the results file as a list with Decimal
        '''
        nonlocal result_file_path
        
        if position_number <= 0:
            raise Exception('Position number can not be 0 or smaller.')

        try:

            with open(result_file_path) as f:
                position_data = list(csv.reader(f))

            position_data = position_data[position_number-1]
            for i in range(len(position_data)):
                try:
                    position_data[i] = Decistr(position_data[i])
                except InvalidOperation:
                    pass

            entry_timestamp = int(position_data[1])
            exit_timestamp = int(position_data[5])
            while entry_timestamp % (time_frame*60) != 0:
                entry_timestamp -= 1
            while exit_timestamp % (time_frame*60) != 0:
                exit_timestamp -= 1
            position_data[1] = entry_timestamp
            position_data[5] = exit_timestamp
            
            return position_data
        
        except IndexError:
            raise Exception('Position not found.')





    def __create_slice_for_candle_plotting(position_number: int, number_candles_before: int, number_candles_after: int) -> None:
        '''
        > Assumes that trigger_time_frame represents the same resolution the ohlc data has

        > Creates the file 'ohlc_candle_plotting.txt'. In this file is the ohlc data of the duration of the given position and additionally candles before entry and after exit
        '''


        def __get_time_frame_ohlc(ohlc_data: List, open_timestamp: int, duration: int):


            def __create_time_frame_ohlc(candle_group: List[List]):
                
                timestamp = int(candle_group[0][0])
                open = Decistr(candle_group[0][1])
                close = Decistr(candle_group[len(candle_group)-1][4])

                high = Decistr(candle_group[0][2])
                low = Decistr(candle_group[0][3])
                
                for x in range(1, len(candle_group)):
                    candle = candle_group[x]
                    temp = Decistr(candle[2])
                    if temp > high:
                        high = temp
                    temp = Decistr(candle[3])
                    if temp < low:
                        low = temp

                return (timestamp, open, high, low, close)


            current_timestamp_index = 0
            found = False
            for candle in ohlc_data:
                if int(candle[0]) == open_timestamp:
                    found = True
                    break
                else:
                    current_timestamp_index += 1
            if found == False:
                raise Exception ('open timestamp error')


            if current_timestamp_index < len(ohlc_data):
                while int(ohlc_data[current_timestamp_index][0]) % (time_frame*60) != 0:
                    current_timestamp_index -= 1
                    if current_timestamp_index < 0:
                        raise Exception ('open timestamp error')
            else:
                raise Exception ('open timestamp error')


            all_candles = []
            for _ in range(duration):
                temp_timestamp = int(ohlc_data[current_timestamp_index][0])
                candle_group = []
                time_frame_ratio = int(time_frame/ohlc_data_time_frame)
                for x in range(time_frame_ratio):
                    if current_timestamp_index < len(ohlc_data):
                        if int(ohlc_data[current_timestamp_index][0]) == temp_timestamp + (x*(60*ohlc_data_time_frame)):
                            candle_group.append(ohlc_data[current_timestamp_index])
                            current_timestamp_index += 1
                        else:
                            raise Exception('ohlc data is not clean')
                    else:
                        raise Exception ('no more ohlc data')

                all_candles.append(__create_time_frame_ohlc(candle_group))
            return all_candles




        position_data = __get_position_specs(position_number)

        with open(ohlc_data_file_path) as f:
            ohlc_data = list(csv.reader(f))

        open_timestamp = position_data[1]
        close_timestamp = position_data[5]

        with open(path_for_file, 'w') as f:
            f.write("")


        timestamp_found = False
        if time_frame != ohlc_data_time_frame:
            # additional candles are added here
            open_timestamp -= number_candles_before*time_frame*60
            close_timestamp += number_candles_after*time_frame*60

            duration = (close_timestamp - open_timestamp) / (time_frame*60)
            duration = int(duration)

            for row in ohlc_data:
                if int(row[0]) == open_timestamp:
                    timestamp_found = True
                    # writes already converted data into file
                    time_frame_candle = __get_time_frame_ohlc(ohlc_data, open_timestamp, duration)
                    for candle in time_frame_candle:
                        with open(path_for_file, 'a') as f:
                            f.write(afunc_private.get_timestamp_to_datetime(candle[0]) + ',' + str(candle[1]) + ',' + str(candle[2]) + ',' + str(candle[3]) + ',' + str(candle[4]) + "\n")
                    break


        else:
            # plotting trigger_time_frame data - assuming ohlc data has the same resolution
            open_timestamp -= number_candles_before*time_frame*60
            close_timestamp += number_candles_after*time_frame*60

            duration = (close_timestamp - open_timestamp) / (ohlc_data_time_frame*60)
            duration = int(duration+1)

            for x in range(len(ohlc_data)):
                if int(ohlc_data[x][0]) == open_timestamp:
                    timestamp_found = True
                    for i in range(x, duration+x):
                        try:
                            with open(path_for_file, 'a') as f:
                                f.write(afunc_private.get_timestamp_to_datetime(ohlc_data[i][0]) + ',' + str(ohlc_data[i][1]) + ',' + str(ohlc_data[i][2]) + ',' + str(ohlc_data[i][3]) + ',' + str(ohlc_data[i][4]) + "\n")
                        except:
                            raise Exception('No more ohlc data.')
                    break


        if timestamp_found == False:
            raise Exception('Open timestamp not in ohlc data found.')

        # inserting 'Date,Open,High,Low,Close' because it is needed for mplfinance candlestick plotting
        with open(path_for_file) as f:
            contents = f.readlines()

        contents.insert(0, 'Date,Open,High,Low,Close\n')

        with open(path_for_file, "w") as f:
            contents = "".join(contents)
            f.write(contents)






    __create_slice_for_candle_plotting(position_number, number_candles_before, number_candles_after)

    # 'Date' as index needed for plotting
    data_to_plot = pandas.read_csv(path_for_file, index_col=0, parse_dates=True)

    # temp_data_to_plot is needed for additional visualizations on the chart, because it does not have 'Date' as index
    temp_data_to_plot = pandas.read_csv(path_for_file)


    # retrieving position data
    position_data = __get_position_specs(position_number)
    
    position_type = position_data[0]
    open_timestamp = position_data[1]
    close_timestamp = position_data[5]
    # zu float da mpf.plot() es verlangt
    open_price = float(position_data[2])
    stoploss_price = float(position_data[3])
    take_profit_price = float(position_data[10])



    # adding symbols to entry and exit candles

    try:
        entry_candle_number = (temp_data_to_plot[temp_data_to_plot['Date'] == afunc_private.get_timestamp_to_datetime(open_timestamp)].index.item()) # -> get index as int - the number of the candle
        exit_candle_number = (temp_data_to_plot[temp_data_to_plot['Date'] == afunc_private.get_timestamp_to_datetime(close_timestamp)].index.item()) # -> get index as int - the number of the candle
    except:
        raise Exception('Can not find timestamp in slice. Most probably input number negative.')

    marked_candles = []
    lows = temp_data_to_plot['Low']
    highs = temp_data_to_plot['High']

    if position_type == 'long':
        for i in range(len(data_to_plot)):
            if entry_candle_number == i:
                marked_candles.append(Decistr(str(lows[i]))*Decistr("0.9995"))
            elif exit_candle_number == i:
                marked_candles.append(Decistr(str(lows[i]))*Decistr("0.9995"))
            else:
                marked_candles.append(numpy.nan)
        apd = [mpf.make_addplot(marked_candles, scatter=True, markersize=len(marked_candles), marker=r'$\Uparrow$', color='b')]

    else:
        for i in range(len(data_to_plot)):
            if entry_candle_number == i:
                marked_candles.append(Decistr(str(highs[i]))*Decistr("1.0005"))
            elif exit_candle_number == i:
                marked_candles.append(Decistr(str(highs[i]))*Decistr("1.0005"))
            else:
                marked_candles.append(numpy.nan)
        apd = [mpf.make_addplot(marked_candles, scatter=True, markersize=len(marked_candles), marker=r'$\Downarrow$', color='b')]



    # changing the appearance of the chart

    mc = mpf.make_marketcolors()
    s = mpf.make_mpf_style(marketcolors=mc)



    # visualizing open, close and trailing stoploss as horizontal lines 

    if show_horizontal_lines:
        lines = [open_price, stoploss_price, take_profit_price]

        horizontal_lines = dict(hlines=lines, colors='b', linewidths=1, linestyle='-.')


        # actual plotting

        mpf.plot(data_to_plot, type='candle', volume=False, figratio=(12,4), style=s, hlines=horizontal_lines, addplot=apd)
    else:
        mpf.plot(data_to_plot, type='candle', volume=False, figratio=(12,4), style=s, addplot=apd)

























'''
PERFORMANCE & RISK VALUE TICKS
'''





def get_risk_value_performance():
    performance = 0
    for pos_trade in trade_history:
        performance += pos_trade[8]
    return performance





def get_risk_value_performance_each_month():
    '''
    returns list with performance of each month
    '''
    monthly_perf_list = []
    perf_current_month = trade_history[0][8]
    current_month = datetime.utcfromtimestamp(int(trade_history[0][1])).strftime('%b') # as str
    for i in range(1, len(trade_history)): # skipping very first item
        item = trade_history[i]
        entry_timestamp = int(item[1])
        month = datetime.utcfromtimestamp(entry_timestamp).strftime('%b') # as number
        if month == current_month:
            perf_current_month += item[8]
        else:
            monthly_perf_list.append((current_month, str(perf_current_month)))
            perf_current_month = item[8]
            current_month = month
    monthly_perf_list.append((current_month, str(perf_current_month))) # aller letzten monat noch anhängen
    
    # calc mean
    perf_list = [Decistr(item[1]) for item in monthly_perf_list]
    mean = str(round(statistics.mean(perf_list), number_decimals_perf))
    monthly_perf_list.append(('mean', mean))
    
    return monthly_perf_list





def get_number_win_loss_breakeven() -> Dict:
    trades_available = False
    wins = 0
    reward = afunc_private.get_reward_size(trade_history, number_decimals_perf)
    losses = 0
    risk = afunc_private.get_risk_size(trade_history, number_decimals_perf)
    breakevens = 0
    number_positions = 0
    

    if reward == 'no trades' or risk == 'no trades':
        abs_win_quote = 'no trades'
        breakeven_quote = 'no trades'
        rel_win_quote = 'no trades'
    else:
        trades_available = True
    

    if trades_available == True:
        risk = abs(risk)
        breakeven_quote = round((risk/(risk+reward))*100, 2)

        for pos_trade in trade_history:
            result = pos_trade[9]
            if result == 'win':
                wins += 1
            elif result == 'loss':
                losses += 1
            else:
                breakevens += 1
    
        number_positions = wins+losses+breakevens

        if number_positions != 0:
            abs_win_quote = round((Decistr(wins)/Decistr(number_positions))*100, 2)
        else:
            abs_win_quote = 'no trades'
    
        reward *= wins
        risk *= losses
        rel_win_quote = round((reward/(reward+risk))*100, 2)


    return {'wins': wins, 'losses': losses, 'breakevens': breakevens, 'position trades': number_positions,
        'abs win quote %': str(abs_win_quote), 'breakeven win quote %': str(breakeven_quote), 'rel win quote %': str(rel_win_quote)}






def get_risk_and_reward_value_ticks_of_last_two_months(use_time: bool = False):
    '''
    gibt Größe zwischen entry & take profit, entry & stop loss wider
    '''
    if use_time == True:
        timestamp_two_months_ago = int(time.time())-(86400*60) # 60 days ago
    else:
        timestamp_two_months_ago = int(trade_history[-1][1])-(86400*60)

    REWARD_value_ticks_of_last_two_months = []
    RISK_value_ticks_of_last_two_months = []
    for pos_trade in trade_history:
        if pos_trade[1] >= timestamp_two_months_ago:
            entry_price = pos_trade[2]
            tp_price = pos_trade[10]
            REWARD_value_ticks_of_last_two_months.append(abs(entry_price-tp_price))
            RISK_value_ticks_of_last_two_months.append(pos_trade[4])
    
    final_dict = {'RISK': {}, 'REWARD': {}}

    if len(RISK_value_ticks_of_last_two_months) != 0:
        mean = afunc_private.to_nearest(statistics.mean(RISK_value_ticks_of_last_two_months))
        median = afunc_private.to_nearest(statistics.median(RISK_value_ticks_of_last_two_months))
        minimum = min(RISK_value_ticks_of_last_two_months)
        maximum = max(RISK_value_ticks_of_last_two_months)
    else:
        mean = 'no trades'
        median = 'no trades'
        minimum = 'no trades'
        maximum = 'no trades'

    final_dict['RISK']['size'] = str(afunc_private.get_risk_size(trade_history, number_decimals_perf))
    final_dict['RISK']['mean'] = str(mean)
    final_dict['RISK']['median'] = str(median)
    final_dict['RISK']['min'] = str(minimum)
    final_dict['RISK']['max'] = str(maximum)

    if len(REWARD_value_ticks_of_last_two_months) != 0:
        mean = afunc_private.to_nearest(statistics.mean(REWARD_value_ticks_of_last_two_months))
        median = afunc_private.to_nearest(statistics.median(REWARD_value_ticks_of_last_two_months))
        minimum = min(REWARD_value_ticks_of_last_two_months)
        maximum = max(REWARD_value_ticks_of_last_two_months)
    else:
        mean = 'no trades'
        median = 'no trades'
        minimum = 'no trades'
        maximum = 'no trades'

    final_dict['REWARD']['size'] = str(afunc_private.get_reward_size(trade_history, number_decimals_perf))
    final_dict['REWARD']['mean'] = str(mean)
    final_dict['REWARD']['median'] = str(median)
    final_dict['REWARD']['min'] = str(minimum)
    final_dict['REWARD']['max'] = str(maximum)

    return final_dict



























'''
DURATIONS & TIME
'''



def get_duration_stats():
    all_durations = [pos_trade[7] for pos_trade in trade_history]
    average = statistics.mean(all_durations)
    median =  statistics.median(all_durations)
    return {'mean': str(average), 'median': str(median), 'max': str(max(all_durations)), 'min': str(min(all_durations))}





def show_exit_entry_time_difference() -> List[int]:
    '''
    finding out if there are overlapping exit and entry (yes if the smallest is negative)
    '''
    time_difference_list = []
    for i in range(len(trade_history)-1):
        time_difference_list.append(trade_history[i+1][1]-trade_history[i][5])
    return time_difference_list





def show_largest_time_differences_between_positions(show_how_many: int) -> None:
    '''
    Zeigt die größten Zeitdifferenzen zwischen Positionen die vorkamen
    '''
    timestamp_differences = []
    for i in range(len(trade_history)-1):
        d = trade_history[i+1][1]-trade_history[i][5]
        if d <= 0:
            print(d, trade_history[i+1][1], trade_history[i][5])
        # assert d > 0, (d, int(trade_history[i+1][1]), int(trade_history[i][5]))
        timestamp_differences.append(d)
    print('\nLargest Time Differences between Position Trades')
    print('Mean:', round(statistics.mean(timestamp_differences)/86400, 2), 'Days')
    print('Median:', round(statistics.median(timestamp_differences)/86400, 2), 'Days')
    print(':Mins:', ':Hrs:', ':Days:')
    for i in range(show_how_many):
        print(int(max(timestamp_differences)/60), ' ', int(max(timestamp_differences)/3600), ' ', int(max(timestamp_differences)/86400))
        del timestamp_differences[numpy.argmax(timestamp_differences)]





















def get_order_cost_stats(fixed_risk: str, max_possible_leverage: int, maintenance_margin_rate_percent: str, number_decimals_calc_position_size: int):
    '''
    stats zu wie groß order costs waren
    '''

    required_quote_sizes = []

    for pos_trade in trade_history:
        entry_side = pos_trade[0]
        entry_price = pos_trade[2]
        stop_loss_price = pos_trade[3]
        risk_value_ticks = abs(entry_price-stop_loss_price)

        if entry_side == 'long':
            liq_price = stop_loss_price-risk_value_ticks
            leverage = afunc_private.get_leverage_by_liq_price(entry_side, entry_price, liq_price, maintenance_margin_rate_percent)
        else:
            liq_price = stop_loss_price+risk_value_ticks
            leverage = afunc_private.get_leverage_by_liq_price(entry_side, entry_price, liq_price, maintenance_margin_rate_percent)

        if leverage > max_possible_leverage:
            leverage = max_possible_leverage

        pos_size = afunc_private.calculate_position_size_by_fixed_risk(entry_price, stop_loss_price, fixed_risk, number_decimals_calc_position_size)
        order_cost = afunc_private.get_order_cost(entry_side, entry_price, pos_size, leverage)
        required_quote_sizes.append(order_cost)

    return {'mean': statistics.mean(required_quote_sizes), 'median': statistics.median(required_quote_sizes), 'max': max(required_quote_sizes)}





def get_drawdowns_stats(title: str = "", plot_drawdowns_distribution: bool = False):

    # drawdowns zählen
    results_list = []
    for pos_trade in trade_history:
        results_list.append(pos_trade[9])

    counter_list = []
    current_counter = 0

    for result in results_list:
        if result == 'loss':
            current_counter += 1
        elif current_counter != 0:
            counter_list.append(current_counter)
            current_counter = 0

    if len(counter_list) == 0:
        return 'empty'

    if plot_drawdowns_distribution == True:
        # drawdowns verteilung anzeigen

        sorted_list = sorted(counter_list)
        sorted_counted = Counter(sorted_list)

        range_length = list(range(max(counter_list))) # Get the largest value to get the range.
        data_series = {}

        for i in range_length:
            data_series[i] = 0 # Initialize series so that we have a template and we just have to fill in the values.

        for key, value in sorted_counted.items():
            data_series[key] = value

        data_series = pandas.Series(data_series)
        x_values = data_series.index

        # you can customize the limits of the x-axis
        plt.xlim(0, max(counter_list)+1)
        plt.bar(x_values, data_series.values)

    dict_stats = {'mean': str(statistics.mean(counter_list)), 'median': str(statistics.median(counter_list)),
        'mode': str(stats.mode(counter_list, keepdims=False)[0]), 'max': str(max(counter_list))}

    if plot_drawdowns_distribution == True:
        print(dict_stats)
        plt.title(title)
        plt.show()

    return dict_stats





def get_r_squared():
    model = linear_model.LinearRegression()
    y = afunc_private.get_risk_value_performance_as_list(trade_history)
    x = [i for i in range(1, len(y)+1)]

    y = numpy.array(y)
    x = numpy.array(x).reshape(-1, 1)

    model.fit(x, y)
    r_squared = model.score(x, y)
    return r_squared


























def check_if_risk_and_leverage_doable_single(
        start_money: str, fixed_risk: str, max_possible_leverage: int, min_distance_liq_sl: str,
        maintenance_margin_rate_percent: str, entry_fee_percent: str, exit_fee_percent: str,
        sell_stop_loss_slippage: str, buy_stop_loss_slippage: str,
        number_decimals_calc_position_size: int, plot_charts: bool = False):

    """
    min_distance_liq_sl: gewollte Mindestdistanz zwischen stop loss & liquidation price, fixe zahl verwenden ist am besten
    maintenance_margin_rate_percent: gebraucht für kalkulationen von bybit liq price, ändert sich nur mit risk limit
    sell_stop_loss_slippage/buy_stop_loss_slippage: % zusätzliche loss von fixed risk
    double_risk_on_half: fixed risk verdoppeln wenn es halb so viel risiko wie anfänglich darstellt
    """


    number_changed_risk = 0 # wie oft fixed risk ändern musste
    order_cost_course = []
    all_fees = []

    money_balance = Decistr(start_money)
    money_course = [money_balance]

    entry_fee_percent = Decistr(entry_fee_percent)/100
    exit_fee_percent = Decistr(exit_fee_percent)/100

    sell_stop_loss_slippage = Decistr(sell_stop_loss_slippage)/100
    buy_stop_loss_slippage = Decistr(buy_stop_loss_slippage)/100

    min_distance_liq_sl = Decistr(min_distance_liq_sl)
    fixed_risk = Decistr(fixed_risk)

    money_with_fee_no_slippage = Decistr(start_money)
    money_course_with_fee_no_slippage = [money_with_fee_no_slippage]

    money_no_fee_no_slippage = Decistr(start_money)
    money_course_no_fee_no_slippage = [money_no_fee_no_slippage]


    for pos_trade in trade_history:

        entry_side = pos_trade[0]
        entry_price = pos_trade[2]
        stop_loss_price = pos_trade[3]
        risk_value_ticks = pos_trade[4]
        exit_price = pos_trade[6]
        risk_value_performance = pos_trade[8]
        trade_result = pos_trade[9]


        # leverage so setzen dass leverage immer optimal genutzt wird
        if entry_side == 'long':
            liq_price = stop_loss_price-min_distance_liq_sl
            leverage = afunc_private.get_leverage_by_liq_price(entry_side, entry_price, liq_price, maintenance_margin_rate_percent)
        else:
            liq_price = stop_loss_price+min_distance_liq_sl
            leverage = afunc_private.get_leverage_by_liq_price(entry_side, entry_price, liq_price, maintenance_margin_rate_percent)
        
        # je nach kalkulation kann leverage zu groß werden
        if leverage > max_possible_leverage:
            leverage = max_possible_leverage

        if plot_charts == True:
            print(f'leverage changed to {leverage}')



        position_size = afunc_private.calculate_position_size_by_fixed_risk(entry_price, stop_loss_price, fixed_risk, number_decimals_calc_position_size)
        order_cost = afunc_private.get_order_cost(entry_side, entry_price, position_size, leverage)


        if order_cost > money_balance: # money reicht nicht, also weniger risk
            # wenn hier hin kommt wird immer risk reduziert
            # leverage muss gleich bleiben damit liq price & bankruptcy price gleich bleiben


            # neue position_size anhand von verfügbarem geld berechnen
            position_size = afunc_private.calculate_position_size_by_money_balance(entry_side, entry_price, leverage, money_balance, number_decimals_calc_position_size)


            order_cost = afunc_private.get_order_cost(entry_side, entry_price, position_size, leverage)
            
            # prüfen ob order cost passt
            if order_cost > money_balance:
                raise


            # checking if slippage applies
            temp_fixed_risk = (position_size*entry_price)*(abs(entry_price-stop_loss_price)/entry_price)
            if plot_charts == True:
                print(f'changed fixed risk from {fixed_risk} to {temp_fixed_risk}')

            slippage_cost = 0
            if trade_result != 'win':
                if entry_side == 'long': # exit side ist sell
                    slippage_cost = temp_fixed_risk*sell_stop_loss_slippage
                    slippage_ticks = afunc_private.to_nearest(risk_value_ticks*sell_stop_loss_slippage)
                    exit_price -= slippage_ticks
                else:
                    slippage_cost = temp_fixed_risk*buy_stop_loss_slippage
                    slippage_ticks = afunc_private.to_nearest(risk_value_ticks*buy_stop_loss_slippage)
                    exit_price += slippage_ticks

            fee = position_size*entry_price*entry_fee_percent
            fee += position_size*exit_price*exit_fee_percent

            money_balance += (temp_fixed_risk*risk_value_performance)-fee-slippage_cost # muss nach vergleich!
            
            if plot_charts == True:
                money_with_fee_no_slippage += (temp_fixed_risk*risk_value_performance)-fee
                money_course_with_fee_no_slippage.append(money_with_fee_no_slippage)

                money_no_fee_no_slippage += temp_fixed_risk*risk_value_performance
                money_course_no_fee_no_slippage.append(money_no_fee_no_slippage)

                order_cost_course.append(order_cost)
                money_course.append(money_balance)
                all_fees.append(fee)

            if money_balance <= 0:
                return 'no money' # damit erneut macht aber mit weniger fixed risk

            number_changed_risk += 1                
            continue



        '''
        kann sein dass leverage geändert wurde, aber wenn HIER hin kommt (if Abfrage ist False) dann kein problem
        money ist trotzdem genug
        '''


        # checking if slippage applies
        slippage_cost = 0
        if trade_result != 'win':
            if entry_side == 'long': # exit side ist sell
                slippage_cost = fixed_risk*sell_stop_loss_slippage
                slippage_ticks = afunc_private.to_nearest(risk_value_ticks*sell_stop_loss_slippage)
                exit_price -= slippage_ticks
            else:
                slippage_cost = fixed_risk*buy_stop_loss_slippage
                slippage_ticks = afunc_private.to_nearest(risk_value_ticks*buy_stop_loss_slippage)
                exit_price += slippage_ticks

        # fee mit geändertem exit price rechnen
        fee = position_size*entry_price*entry_fee_percent
        fee += position_size*exit_price*exit_fee_percent

        money_balance += (fixed_risk*risk_value_performance)-fee-slippage_cost # muss nach vergleich!
        
        if plot_charts == True:
            money_with_fee_no_slippage += (fixed_risk*risk_value_performance)-fee
            money_course_with_fee_no_slippage.append(money_with_fee_no_slippage)

            money_no_fee_no_slippage += fixed_risk*risk_value_performance
            money_course_no_fee_no_slippage.append(money_no_fee_no_slippage)

            order_cost_course.append(order_cost)
            money_course.append(money_balance)
            all_fees.append(fee)

        if money_balance <= 0:
            return 'no money' # damit erneut macht aber mit weniger fixed risk


    if plot_charts == True:
        plt.xlabel('Position Trades')
        plt.ylabel('Money required / Money')
        plt.plot(money_course, label='money course with fee and slippage')
        plt.plot(money_course_with_fee_no_slippage, label='money course with fee no slippage')
        plt.plot(money_course_no_fee_no_slippage, label='money course no fee no slippage')
        plt.plot(order_cost_course, label='order cost course')
        # plt.figtext(0.3, 0.6, str(entry_fee_percent))
        plt.legend()
        print('max order cost:', max(order_cost_course))
        plt.show()
    
    return str(money_balance-Decistr(start_money)), number_changed_risk, all_fees
















def get_profit_course_with_multiple(
    start_money: str, file_paths_with_risk: List, CATT: int, CBTT: int,
    max_possible_leverage: int, min_distance_liq_sl: str,
    maintenance_margin_rate_percent: str, entry_fee_percent: str, exit_fee_percent: str,
    sell_stop_loss_slippage: str, buy_stop_loss_slippage: str,
    number_decimals_calc_position_size: int, plot_charts: bool = False):

    """
    file_paths_with_risk: List[path, $_risk_per_trade]
    """


    number_changed_risk = 0 # wie oft fixed risk ändern musste
    order_cost_course = []
    all_fees = []

    money_balance = Decistr(start_money)
    money_course = [money_balance]

    entry_fee_percent = Decistr(entry_fee_percent)/100
    exit_fee_percent = Decistr(exit_fee_percent)/100

    sell_stop_loss_slippage = Decistr(sell_stop_loss_slippage)/100
    buy_stop_loss_slippage = Decistr(buy_stop_loss_slippage)/100

    min_distance_liq_sl = Decistr(min_distance_liq_sl)

    money_with_fee_no_slippage = Decistr(start_money)
    money_course_with_fee_no_slippage = [money_with_fee_no_slippage]

    money_no_fee_no_slippage = Decistr(start_money)
    money_course_no_fee_no_slippage = [money_no_fee_no_slippage]

    all_profits = []


    for path, fixed_risk in file_paths_with_risk:

        fixed_risk = Decistr(fixed_risk)

        afunc_setup_and_load_trade_history_file(None, None, None, None, path, CATT, CBTT)

        for pos_trade in trade_history:

            entry_side = pos_trade[0]
            entry_timestamp = pos_trade[1]
            entry_price = pos_trade[2]
            stop_loss_price = pos_trade[3]
            risk_value_ticks = pos_trade[4]
            exit_price = pos_trade[6]
            risk_value_performance = pos_trade[8]
            trade_result = pos_trade[9]


            # leverage so setzen dass leverage immer optimal genutzt wird
            if entry_side == 'long':
                liq_price = stop_loss_price-min_distance_liq_sl
                leverage = afunc_private.get_leverage_by_liq_price(entry_side, entry_price, liq_price, maintenance_margin_rate_percent)
            else:
                liq_price = stop_loss_price+min_distance_liq_sl
                leverage = afunc_private.get_leverage_by_liq_price(entry_side, entry_price, liq_price, maintenance_margin_rate_percent)
            
            # je nach kalkulation kann leverage zu groß werden
            if leverage > max_possible_leverage:
                leverage = max_possible_leverage

            if plot_charts == True:
                print(f'leverage changed to {leverage}')



            position_size = afunc_private.calculate_position_size_by_fixed_risk(entry_price, stop_loss_price, fixed_risk, number_decimals_calc_position_size)
            order_cost = afunc_private.get_order_cost(entry_side, entry_price, position_size, leverage)


            if order_cost > money_balance: # money reicht nicht, also weniger risk
                # wenn hier hin kommt wird immer risk reduziert
                # leverage muss gleich bleiben damit liq price & bankruptcy price gleich bleiben


                # neue position_size anhand von verfügbarem geld berechnen
                position_size = afunc_private.calculate_position_size_by_money_balance(entry_side, entry_price, leverage, money_balance, number_decimals_calc_position_size)


                order_cost = afunc_private.get_order_cost(entry_side, entry_price, position_size, leverage)
                
                # prüfen ob order cost passt
                if order_cost > money_balance:
                    raise


                # checking if slippage applies
                temp_fixed_risk = (position_size*entry_price)*(abs(entry_price-stop_loss_price)/entry_price)
                if plot_charts == True:
                    print(f'changed fixed risk from {fixed_risk} to {temp_fixed_risk}')

                slippage_cost = 0
                if trade_result != 'win':
                    if entry_side == 'long': # exit side ist sell
                        slippage_cost = temp_fixed_risk*sell_stop_loss_slippage
                        slippage_ticks = afunc_private.to_nearest(risk_value_ticks*sell_stop_loss_slippage)
                        exit_price -= slippage_ticks
                    else:
                        slippage_cost = temp_fixed_risk*buy_stop_loss_slippage
                        slippage_ticks = afunc_private.to_nearest(risk_value_ticks*buy_stop_loss_slippage)
                        exit_price += slippage_ticks

                fee = position_size*entry_price*entry_fee_percent
                fee += position_size*exit_price*exit_fee_percent

                profit_or_loss = (temp_fixed_risk*risk_value_performance)-fee-slippage_cost

                all_profits.append((entry_timestamp, profit_or_loss))

                money_balance += profit_or_loss # muss nach vergleich!
                
                if plot_charts == True:
                    money_with_fee_no_slippage += (temp_fixed_risk*risk_value_performance)-fee
                    money_course_with_fee_no_slippage.append(money_with_fee_no_slippage)

                    money_no_fee_no_slippage += temp_fixed_risk*risk_value_performance
                    money_course_no_fee_no_slippage.append(money_no_fee_no_slippage)

                    order_cost_course.append(order_cost)
                    money_course.append(money_balance)
                    all_fees.append(fee)

                if money_balance <= 0:
                    return 'no money' # damit erneut macht aber mit weniger fixed risk

                number_changed_risk += 1                
                continue



            '''
            kann sein dass leverage geändert wurde, aber wenn HIER hin kommt dann kein problem denn money ist genug
            '''


            # checking if slippage applies
            slippage_cost = 0
            if trade_result != 'win':
                if entry_side == 'long': # exit side ist sell
                    slippage_cost = fixed_risk*sell_stop_loss_slippage
                    slippage_ticks = afunc_private.to_nearest(risk_value_ticks*sell_stop_loss_slippage)
                    exit_price -= slippage_ticks
                else:
                    slippage_cost = fixed_risk*buy_stop_loss_slippage
                    slippage_ticks = afunc_private.to_nearest(risk_value_ticks*buy_stop_loss_slippage)
                    exit_price += slippage_ticks

            # fee mit geändertem exit price rechnen
            fee = position_size*entry_price*entry_fee_percent
            fee += position_size*exit_price*exit_fee_percent

            profit_or_loss = (fixed_risk*risk_value_performance)-fee-slippage_cost

            all_profits.append((entry_timestamp, profit_or_loss))

            money_balance += profit_or_loss # muss nach vergleich!
            
            if plot_charts == True:
                money_with_fee_no_slippage += (fixed_risk*risk_value_performance)-fee
                money_course_with_fee_no_slippage.append(money_with_fee_no_slippage)

                money_no_fee_no_slippage += fixed_risk*risk_value_performance
                money_course_no_fee_no_slippage.append(money_no_fee_no_slippage)

                order_cost_course.append(order_cost)
                money_course.append(money_balance)
                all_fees.append(fee)

            if money_balance <= 0:
                return 'no money' # damit erneut macht aber mit weniger fixed risk


    all_profits.sort(key=lambda x : x[0])



    if plot_charts == True:
        plt.xlabel('Position Trades')
        plt.ylabel('Money required / Money')
        plt.plot(money_course, label='money course with fee and slippage')
        plt.plot(money_course_with_fee_no_slippage, label='money course with fee no slippage')
        plt.plot(money_course_no_fee_no_slippage, label='money course no fee no slippage')
        plt.plot(order_cost_course, label='order cost course')
        # plt.figtext(0.3, 0.6, str(entry_fee_percent))
        plt.legend()
        print('max order cost:', max(order_cost_course))
        plt.show()
    
    return str(money_balance-Decistr(start_money)), number_changed_risk, all_fees, all_profits

















def get_trading_volume_per_month(
    start_money: str, fixed_risk: str, max_possible_leverage: int,
    min_distance_liq_sl: str, maintenance_margin_rate_percent: str,
    sell_stop_loss_slippage: str, buy_stop_loss_slippage: str,
    number_decimals_calc_position_size: int):


    money_balance = Decistr(start_money)

    min_distance_liq_sl = Decistr(min_distance_liq_sl)
    fixed_risk = Decistr(fixed_risk)

    sell_stop_loss_slippage = Decistr(sell_stop_loss_slippage)/100
    buy_stop_loss_slippage = Decistr(buy_stop_loss_slippage)/100

    volume_of_each_position_trade = []


    for pos_trade in trade_history:

        entry_timestamp = int(pos_trade[1])
        entry_side = pos_trade[0]
        entry_price = pos_trade[2]
        stop_loss_price = pos_trade[3]
        risk_value_ticks = pos_trade[4]
        exit_price = pos_trade[6]
        trade_result = pos_trade[9]


        # leverage so setzen dass leverage immer optimal genutzt wird
        if entry_side == 'long':
            liq_price = stop_loss_price-min_distance_liq_sl
            leverage = afunc_private.get_leverage_by_liq_price(entry_side, entry_price, liq_price, maintenance_margin_rate_percent)
        else:
            liq_price = stop_loss_price+min_distance_liq_sl
            leverage = afunc_private.get_leverage_by_liq_price(entry_side, entry_price, liq_price, maintenance_margin_rate_percent)
        
        # je nach kalkulation kann leverage zu groß werden
        if leverage > max_possible_leverage:
            leverage = max_possible_leverage


        position_size = afunc_private.calculate_position_size_by_fixed_risk(entry_price, stop_loss_price, fixed_risk, number_decimals_calc_position_size)
        order_cost = afunc_private.get_order_cost(entry_side, entry_price, position_size, leverage)


        if order_cost > money_balance: # money reicht nicht, also weniger risk
            # wenn hier hin kommt wird immer risk reduziert
            # leverage muss gleich bleiben damit liq price & bankruptcy price gleich bleiben


            # neue position_size anhand von verfügbarem geld berechnen
            position_size = afunc_private.calculate_position_size_by_money_balance(entry_side, entry_price, leverage, money_balance, number_decimals_calc_position_size)


            order_cost = afunc_private.get_order_cost(entry_side, entry_price, position_size, leverage)
            
            # prüfen ob order cost passt
            if order_cost > money_balance:
                raise


            # checking if slippage applies
            temp_fixed_risk = (position_size*entry_price)*(abs(entry_price-stop_loss_price)/entry_price)

            if trade_result != 'win':
                if entry_side == 'long': # exit side ist sell
                    slippage_ticks = afunc_private.to_nearest(risk_value_ticks*sell_stop_loss_slippage)
                    exit_price -= slippage_ticks
                else:
                    slippage_ticks = afunc_private.to_nearest(risk_value_ticks*buy_stop_loss_slippage)
                    exit_price += slippage_ticks

            order_volume = position_size*entry_price
            order_volume += position_size*exit_price

            volume_of_each_position_trade.append((entry_timestamp, order_volume))
           
            continue



        '''
        kann sein dass leverage geändert wurde, aber wenn HIER hin kommt (if Abfrage ist False) dann kein problem
        money ist trotzdem genug
        '''


        # checking if slippage applies
        if trade_result != 'win':
            if entry_side == 'long': # exit side ist sell
                slippage_ticks = afunc_private.to_nearest(risk_value_ticks*sell_stop_loss_slippage)
                exit_price -= slippage_ticks
            else:
                slippage_ticks = afunc_private.to_nearest(risk_value_ticks*buy_stop_loss_slippage)
                exit_price += slippage_ticks

        # fee mit geändertem exit price rechnen
        order_volume = position_size*entry_price
        order_volume += position_size*exit_price

        volume_of_each_position_trade.append((entry_timestamp, order_volume))
        

    volumes_each_month = []
    volume_current_month = volume_of_each_position_trade[0][1]
    current_month = datetime.utcfromtimestamp(int(volume_of_each_position_trade[0][0])).strftime('%b') # as str
    for i in range(1, len(volume_of_each_position_trade)):
        item = volume_of_each_position_trade[i]
        year = datetime.utcfromtimestamp(item[0]).strftime('%Y')
        month = datetime.utcfromtimestamp(item[0]).strftime('%b')
        if month == current_month:
            volume_current_month += item[1]
        else:
            volumes_each_month.append((year+'-'+current_month, str(volume_current_month)))
            volume_current_month = item[1]
            current_month = month
    volumes_each_month.append((year+'-'+current_month, str(volume_current_month)))

    
    return volumes_each_month















def get_win_fee_drain_stats(fee_rate: str):
    '''
    herausfinden wie viel Prozent fee barrier von reward value ticks einnimmt
    '''
    fee_rate = Decistr(fee_rate)/100
    on_win = []
    for pos_trade in trade_history:
        if pos_trade[9] == 'win':
            entry = pos_trade[2]
            take_profit = pos_trade[10]
            reward_value_ticks = abs(take_profit-entry)

            fee_barrier = (entry*fee_rate)+(take_profit*fee_rate)
            fee_barrier /= reward_value_ticks
            on_win.append(fee_barrier)
    return {'mean': str(round(statistics.mean(on_win)*100, 2))+' %', 'median': str(round(statistics.median(on_win)*100, 2))+' %',
            'min': str(round(min(on_win)*100, 2))+' %', 'max': str(round(max(on_win)*100, 2))+' %'}







