
#include "data_runner.h"





// private

void TradingDataRunner::find_candle_timestamp_index(const int candle_timestamp) {

    // TIMER __timer("tdr_find_candle_timestamp_index");

    // index für trading data so ändern dass mit trading data ab candle timestamp gearbeitet wird

    for (int i=index_candle_timestamps_indices; i<length_ohlc_data; i++) {
        if (candle_timestamps_indices[i][0] == candle_timestamp) {
            index_trading_data = candle_timestamps_indices[i][1];
            index_candle_timestamps_indices = i; // nur dies alleine für wenn erst check_which_entry_happened_first() & danach direkt check_if_take_profit_happened_with_trading_data()
            return;
        }
    }
    throw std::invalid_argument("candle_timestamp not found: " + std::to_string(candle_timestamp));
}



const std::vector<double> &TradingDataRunner::get_trade() {

    const std::vector<double> &current_trade = trading_data[index_trading_data];

    index_trading_data++;

    if (index_trading_data == length_trading_data) {
        bt_done = true;
    }

    return current_trade;
}



/*
findet immer einen exit da exit bereits in candle gefunden wurde
prüft Zustände die in dieser candle auftreten:
entry + stop loss + take profit
stop loss + take profit
*/
const double TradingDataRunner::check_stop_loss_and_take_profit_with_trading_data(
    const std::string entry_side, const double entry_price,
    const int entry_candle_timestamp, const int exit_candle_timestamp,
    const double stop_loss_price, const double take_profit_price) {

    bool entry_found = false;

    find_candle_timestamp_index(exit_candle_timestamp); // in trading data ab richtiger stelle gucken

    while (true) {

        const double &trade_price = get_trade()[1];

        // nur wenn entry & exit in derselben candle sind dann zuerst entry finden
        if (entry_found == false && entry_candle_timestamp == exit_candle_timestamp) {

            if (entry_side == "long") {
                if (trade_price <= entry_price) {
                    entry_found = true;
                }
            }
            else {
                if (trade_price >= entry_price) {
                    entry_found = true;
                }
            }

            if (entry_found == false) {
                continue;
            }
        }


        if (entry_side == "long") {
            if (trade_price <= stop_loss_price) {
                return stop_loss_price;
            }
            else if (trade_price >= take_profit_price) {
                return take_profit_price;
            }
        }
        else {
            if (trade_price >= stop_loss_price) {
                return stop_loss_price;
            }
            else if (trade_price <= take_profit_price) {
                return take_profit_price;
            }
        }

    }

}



/*
prüft Zustand
entry + take profit
*/
const double TradingDataRunner::check_if_take_profit_happened_with_trading_data(
    const std::string entry_side, const double entry_price, const int entry_candle_timestamp, const double take_profit_price) {

    bool entry_found = false;
    const int stop_timestamp = entry_candle_timestamp+60;

    find_candle_timestamp_index(entry_candle_timestamp); // in trading data ab richtiger stelle gucken

    while (true) {
        const std::vector<double> &current_trade = get_trade();

        const double &trade_timestamp = current_trade[0];

        if (trade_timestamp >= stop_timestamp) {
            // take profit did not happen
            return -1;
        }

        const double &trade_price = current_trade[1];

        // zuerst entry finden
        if (entry_found == false) {

            if (entry_side == "long") {
                if (trade_price <= entry_price) {
                    entry_found = true;
                }
            }
            else {
                if (trade_price >= entry_price) {
                    entry_found = true;
                }
            }

            if (entry_found == false) {
                continue;
            }
        }

        // prüfen auf take profit hit
        if (entry_side == "long") {
            if (trade_price >= take_profit_price) {
                return take_profit_price;
            }
        }
        else {
            if (trade_price <= take_profit_price) {
                return take_profit_price;
            }
        }

        if (bt_done == true) {
            return -1;
        }

    }

}






// public

TradingDataRunner::TradingDataRunner(
const VVD &ohlc_data, const VVD &trading_data, const VVI &candle_timestamps_indices)
:
length_ohlc_data(ohlc_data.size()), length_trading_data(trading_data.size()), ohlc_data(ohlc_data), trading_data(trading_data), candle_timestamps_indices(candle_timestamps_indices) {}



const bool TradingDataRunner::is_backtesting_done() const {
    return bt_done;
}



/*
findet immer einen entry da entry bereits in candle gefunden wurde
true == long
false == short
*/
const bool TradingDataRunner::check_which_entry_happened_first(const double entry_candle_timestamp, const double long_entry_price, const double short_entry_price) {

    find_candle_timestamp_index(entry_candle_timestamp);

    while (true) {

        const double &trade_price = get_trade()[1];

        if (trade_price <= long_entry_price) {
            return true;
        }
    
        if (trade_price >= short_entry_price) {
            return false;
        }

    }
}












const std::vector<double> TradingDataRunner::check_position_exit(
    const std::string entry_side, const double entry_price, int ohlc_index,
    Volatility_IQR_AVG &vola_calc, ExtremaFinder &ef,
    const int entry_candle_timestamp,
    const double stop_loss_price, const double take_profit_price) {
    
    // TIMER __timer1("tdr_check_position_exit");


    bool stop_loss_hit = false, take_profit_hit = false;


    // exit finden, auch in entry candle
    while (true) {
      
        // TIMER __timer2("tdr_while_loop_candle_refs");

        const std::vector<double> &candle = ohlc_data[ohlc_index];
        const double &candle_timestamp = candle[0];
        const double &candle_high = candle[2];
        const double &candle_low = candle[3];
        const double &candle_close = candle[4];

        // __timer2.end();

        update_other(candle_timestamp, candle_close, vola_calc, ef);



        // TIMER __timer3("tdr_while_loop_ifs");



        if (entry_side == "long") {
            if (stop_loss_price >= candle_low) {
                stop_loss_hit = true;
            }
            // kein else if
            if (take_profit_price <= candle_high) {
                take_profit_hit = true;
            }
        }
        else {
            if (stop_loss_price <= candle_high) {
                stop_loss_hit = true;
            }
            // kein else if
            if (take_profit_price >= candle_low) {
                take_profit_hit = true;
            }
        }



        // diese Reihenfolge
        if (stop_loss_hit == false && take_profit_hit == false) {
            ohlc_index++;
            if (ohlc_index == length_ohlc_data) {
                bt_done = true;
                break;
            }
            continue;
        }
        
        // Zustände
        // entry + stop loss + take profit
        // stop loss + take profit
        else if (stop_loss_hit == true && take_profit_hit == true) {
            // wird immer einen exit finden
            const double exit_price = check_stop_loss_and_take_profit_with_trading_data(
                entry_side, entry_price,
                entry_candle_timestamp, candle_timestamp,
                stop_loss_price, take_profit_price
            );
            return {double(ohlc_index), double(candle_timestamp), exit_price};
        }
        
        // Zustände
        // entry + stop loss
        // stop loss
        else if (stop_loss_hit == true) {
            return {double(ohlc_index), double(candle_timestamp), stop_loss_price};
        }

        else { // take_profit_hit == true
            // Zustand entry + take profit
            if (entry_candle_timestamp == candle_timestamp) {
                // wenn trading data zu ende ist sowieso bei letzer candle
                // gibt -1 zurück und bt_done auf true
                const double exit_price = check_if_take_profit_happened_with_trading_data(entry_side, entry_price, entry_candle_timestamp, take_profit_price);
                if (exit_price != -1) { // take profit did happen
                    return {double(ohlc_index), double(candle_timestamp), exit_price};
                }
                take_profit_hit = false;
            }

            // Zustand take profit
            else {
                return {double(ohlc_index), double(candle_timestamp), take_profit_price};
            }
        }



        // für wenn doch kein take profit hit war
        ohlc_index++;
        if (ohlc_index == length_ohlc_data) {
            bt_done = true;
            break;
        }



    }

    // kommt hier hin wenn ohlc data zu Ende ist oder trading data für check take profit zu Ende ist
    return {};

}







/*
diese Funktion kann flexibel geändert werden
*/
void TradingDataRunner::update_other(
    const double candle_timestamp, const double candle_close,
    Volatility_IQR_AVG &vola_calc, ExtremaFinder &ef) {

    vola_calc.add_source(candle_close);
    ef.append({candle_timestamp, candle_close});
}




