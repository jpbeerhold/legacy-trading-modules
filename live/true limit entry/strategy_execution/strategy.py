# Down Settling - True Limit Entry
# @Jannis

from logs_and_data import file_writer
from settings import Down_Settling_Parameters, general_specifications
from Bybit_Access import bybit_usdt_perp_client
import super_global_variables as super_globals
import general_helper_functions as ghf
from general_helper_functions import Decistr
from strategy_execution import helper_classes
from market_insertion import filling_and_orders_manager

import time
from typing import List




'''
imported Parameters
'''

distance_percent = Down_Settling_Parameters.distance_percent

sma_length = Down_Settling_Parameters.sma_length

sl_multiplier = Down_Settling_Parameters.stop_loss_distance_multiplier

tp_multiplier = Down_Settling_Parameters.take_profit_distance_multiplier


daily_iqr_inputs = Down_Settling_Parameters.daily_iqr_inputs

timestamp_vola_iqr_avg_empty_fragment = Down_Settling_Parameters.timestamp_vola_iqr_avg_empty_fragment


number_back_use_close = Down_Settling_Parameters.number_back_use_close





symbol = general_specifications.symbol

time_frame = general_specifications.time_frame

number_of_decimals_for_price = general_specifications.number_of_decimals_for_price














def create_PositionTrade(cancel_timestamp: int):

    def __change_after_position_trade():
        bybit_usdt_perp_client.all_orders_and_executions_collection = []
        file_writer.append_to_log_position_manager('----------------------------------------')
        return 'position trade done'


    # +2 weil muss zwei zurück
    necessary = cancel_timestamp-((number_back_use_close+2)*(time_frame*60))
    while helper_classes.candle_history.is_timestamp_in_history(necessary) == False:
        # safety feature not overloading server
        if int(time.time()) >= cancel_timestamp-50:
            file_writer.append_to_log_bybit_client('did not receive candle')
            bybit_usdt_perp_client.terminate_bot()
            raise


    base_value = Decistr(helper_classes.sma_object.get_sma())
    price_volatility = Decistr(helper_classes.vola_iqr_avg.get_average_iqr())

    portion = base_value*Decistr(distance_percent/100)


    long_entry_price = base_value-portion
    long_stop_loss_price = long_entry_price-(price_volatility*Decistr(sl_multiplier))
    long_take_profit_price = long_entry_price+(price_volatility*Decistr(tp_multiplier))

    short_entry_price = base_value+portion
    short_stop_loss_price = short_entry_price+(price_volatility*Decistr(sl_multiplier))
    short_take_profit_price = short_entry_price-(price_volatility*Decistr(tp_multiplier))


    if general_specifications.use_round == True:
        long_entry_price = float(round(long_entry_price, number_of_decimals_for_price))
        long_stop_loss_price = float(round(long_stop_loss_price, number_of_decimals_for_price))
        long_take_profit_price = float(round(long_take_profit_price, number_of_decimals_for_price))

        short_entry_price = float(round(short_entry_price, number_of_decimals_for_price))
        short_stop_loss_price = float(round(short_stop_loss_price, number_of_decimals_for_price))
        short_take_profit_price = float(round(short_take_profit_price, number_of_decimals_for_price))

    else:
        long_entry_price = ghf.to_nearest(long_entry_price, number_of_decimals_for_price)
        long_stop_loss_price = ghf.to_nearest(long_stop_loss_price, number_of_decimals_for_price)
        long_take_profit_price = ghf.to_nearest(long_take_profit_price, number_of_decimals_for_price)

        short_entry_price = ghf.to_nearest(short_entry_price, number_of_decimals_for_price)
        short_stop_loss_price = ghf.to_nearest(short_stop_loss_price, number_of_decimals_for_price)
        short_take_profit_price = ghf.to_nearest(short_take_profit_price, number_of_decimals_for_price)


    position_trade = filling_and_orders_manager.OrderHandler(
        cancel_timestamp,
        long_entry_price, long_stop_loss_price, long_take_profit_price,
        short_entry_price, short_stop_loss_price, short_take_profit_price)


    limit_entry_result = position_trade.place_both_entrys()
    
    if limit_entry_result == 'limit entry order filled completely' or limit_entry_result == 'limit entry order filled partially':
        position_trade.final_entry_time = time.time()
        stop_loss_take_profit = position_trade.place_stop_loss_and_take_profit()

        if stop_loss_take_profit == 'stop loss market order exit' or stop_loss_take_profit == 'limit stop loss order filled completely':
            return __change_after_position_trade()

        else: # 'take profit order filled completely', 'take profit market order exit'
            return __change_after_position_trade()

    else:
        return limit_entry_result




































def assert__check_if_timestamps_in_data_timestamp_close(data_timestamp_close: List[List], timestamps_to_check: List[int]) -> None:
    all_timestamps = [row[0] for row in data_timestamp_close]
    assert type(timestamps_to_check) == list
    for i in range(len(all_timestamps)-1):
        assert all_timestamps[i+1]-all_timestamps[i] == time_frame*60
    for tp in timestamps_to_check:
        assert tp in all_timestamps









def show_all_parameters() -> None:
    file_writer.append_to_log_bybit_client(f'distance_percent: {distance_percent}')
    file_writer.append_to_log_bybit_client(f'sma length(): {sma_length}')
    file_writer.append_to_log_bybit_client(f'stop_loss_distance_multiplier: {sl_multiplier}')
    file_writer.append_to_log_bybit_client(f'take_profit_distance_multiplier: {tp_multiplier}')
    file_writer.append_to_log_bybit_client(f'daily_iqr_inputs: {daily_iqr_inputs}')
    file_writer.append_to_log_bybit_client(f'timestamp_vola_iqr_avg_empty_fragment: {timestamp_vola_iqr_avg_empty_fragment}')
    file_writer.append_to_log_bybit_client(f'number_back_use_close: {number_back_use_close}')













'''
### STRATEGY MAIN FUNCTION AND ASSOCIATED ###

Die candle in der eine Position geschlossen wurde (exit) wird abgewartet bis diese abgeschlossen ist
Erst dann wird weiter gemacht bzw. auf entry geprüft, und auch erst nachdem man den close hat wird geprüft ob echter limit entry möglich ist
'''










def strategy_initialization() -> None:
    '''
    Gets candle_history and iqr_history ready
    Executes search_for_new_extrema() at last correct timestamp like in backtesting (point_of_rerun)

    How often extrema_finder is executed depends on length and rerun_extrema_finder
    The filling of iqr history & candle history start at the same time in backtesting, so they will find themselves again "aligned" in intervals given by length

    Details in Squid and look at Backtesting Code
    '''

    if super_globals.is_initialization_done == True:
        return

    while helper_classes.latest_ticker_data.get_ask() == None:
        continue

    file_writer.append_to_log_bybit_client('Initialization Started')

    daily_iqr_history_storage_amount = daily_iqr_inputs[0]*daily_iqr_inputs[1]


    def __get_timestamp_start_iqr_history_filling() -> int:
        duration_temp_fragment = daily_iqr_inputs[1]*time_frame*60 # duration of time of one temp fragment in unix
        modulo_rest_temp_fragment = timestamp_vola_iqr_avg_empty_fragment % duration_temp_fragment

        first_temp_fragment_empty_timestamp = int(time.time())
        while first_temp_fragment_empty_timestamp % duration_temp_fragment != modulo_rest_temp_fragment:
            first_temp_fragment_empty_timestamp -= 1
        first_temp_fragment_empty_timestamp += time_frame*60

        return first_temp_fragment_empty_timestamp-(daily_iqr_history_storage_amount*time_frame*60)


    def __get_necessary_data(timestamp_data_start: int) -> List[List]:
        data_timestamp_close = []
        timestamp_data_end = ghf.get_last_closed_time_frame_candle_timestamp()-(time_frame*60*(number_back_use_close))
        while True:
            time_frame_candles = bybit_usdt_perp_client.v2_rest_client.query_kline(
                symbol=symbol, interval=str(time_frame), from_time=timestamp_data_start)

            for item in time_frame_candles:
                tp = int(item['open_time'])
                data_timestamp_close.append( (tp, float(item['close'])) )
                if tp == timestamp_data_end:
                    return data_timestamp_close

            timestamp_data_start = int(time_frame_candles[-1]['open_time'])
            timestamp_data_start += time_frame*60



    def __insert_data_into_iqr_history(data_timestamp_close: List[List]) -> None:
        for row in data_timestamp_close:
            helper_classes.candle_history.add_candle(row[0], row[1])





    timestamp_data_start = __get_timestamp_start_iqr_history_filling()

    data_timestamp_close = __get_necessary_data(timestamp_data_start)

    __insert_data_into_iqr_history(data_timestamp_close)


    assert len(helper_classes.vola_iqr_avg.list) == daily_iqr_inputs[0], len(helper_classes.vola_iqr_avg.list)


    file_writer.to_z_file('sma: '+str(helper_classes.sma_object.get_sma()))
    file_writer.to_z_file('average_iqr: '+str(helper_classes.vola_iqr_avg.get_average_iqr()))
    file_writer.to_z_file('temp fragment length: '+str(len(helper_classes.vola_iqr_avg.temp_fragment)))
    file_writer.to_z_file(str(helper_classes.latest_ticker_data.get_all()))
    file_writer.to_z_file("")

    file_writer.append_to_log_bybit_client('Initialization Finished')
    file_writer.append_to_log_bybit_client('Starting Bot. All Parameters:')
    show_all_parameters()

    super_globals.is_initialization_done = True













sleep_strategy: bool = True

def strategy_main() -> None:
    global sleep_strategy

    strategy_initialization()

    t = int(time.time())
    if t % (time_frame*60) == 0:
        sleep_strategy = True
        cPT = create_PositionTrade(t+(time_frame*60))

        if cPT == 'time is over':
            sleep_strategy = False
        elif cPT == 'price no good':
            time.sleep(2) # wenn close price nicht passt für entrys, passiert genau bei % time_frame*60 == 0 

    if sleep_strategy == True:
        time.sleep(0.125)





