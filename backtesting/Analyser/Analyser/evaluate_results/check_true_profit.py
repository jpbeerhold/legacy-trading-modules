'''

hiermit result files durchgucken auf einen linearen verlauf der performance


findet das höchst gefundene r² mit entsprechender position trades Anzahl


solche die den kriterien entsprechen werden erneut geprüft nach fees & slippage


nicht auf gesamte performance oder anzahl der trades schauen,
da sonst gute übersehen werden könnten
lieber infos in log hinzuschreiben & dann schauen


Duration: couple hours


Annahme ist result files haben take profit auf 10. Stelle


Auswertung:
gibt find_log.txt zurück
ist nach r² sortiert, dann untersuchen solche mit vielen Trades 


nur
path
min_number_pos_trades
min_r_squared
max_drawdown
ändern

'''


path_to_result_files = '/home/run/bt/bt_results/'
min_number_pos_trades = 1000 # bis zu welcher anzahl immer noch r² berechnet werden soll
min_r_squared = 0.8
max_drawdown = 6
slippage_percentage = "3.5" # in %
fee_rate = "0.02" # in %













# für auf PC damit kein bug ist & man arbeiten kann
# import _share_files.analyse_functions as afunc


# für auf instance
import analyse_functions as afunc

tick_value = '0.1' # not used
time_frame = 1 # not used
ohlc_data_time_fame = 1 # not used
ohlc_data_path = None # not needed

all_results_first = []



# auf r² und drawdowns prüfen
# solche die im rahmen der kriterien sind speichern

def check_r_squared_drawdowns():

    from os import walk
    filenames = next(walk(path_to_result_files), (None, None, []))[2]

    for file in filenames:
        max = 0
        number_pos_trades_at_max = None
        if afunc.afunc_setup_and_load_trade_history_file(tick_value, time_frame, ohlc_data_time_fame, ohlc_data_path, path_to_result_files+file) == 'empty':
            continue


        md = int(afunc.get_drawdowns_stats()['max'])

        total_number_pos_trades = len(afunc.trade_history)

        if total_number_pos_trades >= min_number_pos_trades and md <= max_drawdown:

            while len(afunc.trade_history) >= min_number_pos_trades: # damit nicht r² == 1.0 entsteht
                
                if afunc.get_risk_value_performance() > 0: # damit nicht gutes r² verwendet von negativer richtung
                    r_squared = afunc.get_r_squared()
                    if r_squared > max:
                        max = r_squared
                        number_pos_trades_at_max = len(afunc.trade_history)
                
                del afunc.trade_history[0]

            if max >= min_r_squared:
                all_results_first.append( (file, round(max, 4), md, number_pos_trades_at_max, total_number_pos_trades) )

    all_results_first.sort(key=lambda x: x[1], reverse=True)

    # speichern

    with open('check_log_first.txt', 'w') as f:
        f.write("file_name,r_squared,max_drawdown,pos_trades_at_r_squared,total_pos_trades\n")

    with open('check_log_first.txt', 'a') as f:
        for r in all_results_first:
            for i in range(len(r)):
                f.write(str(r[i]))
                if i != len(r)-1:
                    f.write(',')
            f.write('\n')








# im rahmen der kriterien gefundene auf fees & slippage prüfen und speichern

def check_fees_slippage():

    # auf fees und slippage prüfen, und wieder auf r²

    from decimal import Decimal
    global slippage_percentage, fee_rate

    slippage_percentage = Decimal(slippage_percentage)/100
    fee_rate = Decimal(fee_rate)/100

    all_results_second = []

    for result_tuple in all_results_first:
        file_name = result_tuple[0]
        afunc.afunc_setup_and_load_trade_history_file(tick_value, time_frame, ohlc_data_time_fame, ohlc_data_path, path_to_result_files+file_name)
        total_number_pos_trades = len(afunc.trade_history)

        while len(afunc.trade_history) != result_tuple[3]:
            del afunc.trade_history[0]

        # performance ändern

        for pos_trade in afunc.trade_history:
            entry = pos_trade[2]
            risk_value_ticks = pos_trade[4]
            exit_price = pos_trade[6]
            actual_performance = pos_trade[8]
            if pos_trade[9] == 'loss':
                # kalkulation so falls aufgrund strategie exit nicht bei stop loss sein sollte
                actual_performance -= (risk_value_ticks*slippage_percentage)/risk_value_ticks
            
            fee_barrier = (entry*fee_rate)+(exit_price*fee_rate)
            fee_barrier /= risk_value_ticks
            actual_performance -= fee_barrier
            pos_trade[8] = actual_performance



        # prüfen

        max = 0
        number_pos_trades_at_max = None

        md = int(afunc.get_drawdowns_stats()['max'])

        if total_number_pos_trades >= min_number_pos_trades and md <= max_drawdown:

            while len(afunc.trade_history) >= min_number_pos_trades: # damit nicht r² == 1.0 entsteht
                
                if afunc.get_risk_value_performance() > 0: # damit nicht gutes r² verwendet von negativer richtung
                    r_squared = afunc.get_r_squared()
                    if r_squared > max:
                        max = r_squared
                        number_pos_trades_at_max = len(afunc.trade_history)
                
                del afunc.trade_history[0]

            if max >= min_r_squared:
                all_results_second.append( (file_name, round(max, 4), md, number_pos_trades_at_max, total_number_pos_trades) )

    all_results_second.sort(key=lambda x: x[1], reverse=True)

    # speichern

    with open('check_log_second.txt', 'w') as f:
        f.write("file_name,r_squared,max_drawdown,pos_trades_at_r_squared,total_pos_trades\n")

    with open('check_log_second.txt', 'a') as f:
        for r in all_results_second:
            for i in range(len(r)):
                f.write(str(r[i]))
                if i != len(r)-1:
                    f.write(',')
            f.write('\n')









check_r_squared_drawdowns()
check_fees_slippage()
