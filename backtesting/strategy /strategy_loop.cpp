
#include "DataLoad/data_load.h"


/*

es gibt zwei modi:

FAST
Fokus auf sehr schnelles backtesting
prüft nur mit trading data wenn exits in derselben candle

dafür jedoch ist timestamp Genauigkeit auf ohlc timestamps beschrenkt

DETAILED
genaue timestamps in results dateien

*/










/*

const nutzen damit bestimme variablen nicht geändert werden können

at() und [] Zugriff auf Vector

at() nutzen wenn man verhindern möchte dass Fehler auftreten da out of bound error entsteht

[] gibt kein out of bound und kann zu extremen fehlern führen

kaum Performance unterschied, daher at() nutzen

use double
- its standard in C & C++
- high precision & performance

int könnte je nach anwendung zu klein werden -> uintmax_t

*/









/*

wie Strategie (Down Settling) funktioniert:
- nutzt closes von ohlc data als Zahlenreihe
- je nach dem an welchem timestamp man anfängt & welche inputs gegeben werden kommen unterschiedliche resultate,
  da somit jede hier aufgelistete variable unterschiedlich berechnet wird

- auf Zahlenreihe wird SMA berechnet (einen input, zB 10)
- auf Zahlenreihe wird Volatility_IQR_AVG berechnet (zwei inputs, zB 7, 1440)
- mit EMA, Volatility_IQR_AVG & distance_percent werden zwei weitere Zahlen, die entrys, berechnet
- mit Volatility_IQR_AVG, entry, take_profit- & stop_loss_multiplikator werden stop_loss und take_profit berechnet

Ziel ist es volatile ausfälle von market orders zu nutzen, welche widerum von gegenteiligen market orders erwidert werden
bzw preis fällt extrems aus, preis beruhigt sich & kommt zur ruhigen mitte zurück

SMA wird verwendet damit ein bezug zur ruhigen mitte des preises besteht
von der ruhigen mitte distanzierte entrys werden berechnet
für jeden position trade gibt es einen festen entry, stop loss & take profit





alles ist auf 1m ohlc data

backtesting has no parallel positions

Volatility_IQR_AVG vola_iqr_avg > Fragment- und Historylänge bleiben durchgehend gleich


ALLES WAS MAN ÄNDERN MUSS FÜR ANDERE DATA BACKTESTING
> settings.cpp, settings.h & strategy_loop.cpp
> trading_data_files_names.txt mit generate_files_names.py


Checklist:

- woher vola/base source data

- path angaben für data & trading data file names richtig

- specs angaben richtig


_optional_

position anzeigen lassen -> show_all_variables()

timestamp temp fragment anzeigen lassen

*/











const double to_nearest(const double number) {
    return std::round(number/round_to_decimal)*round_to_decimal;
}

const double specific_to_nearest(const double number) {
    return std::round(number/specific_round_to_decimal)*specific_round_to_decimal;
}



const double up_to_nearest(const double number) {
    return std::ceil(number/round_to_decimal)*round_to_decimal;
}

const double specific_up_to_nearest(const double number) {
    return std::ceil(number/specific_round_to_decimal)*specific_round_to_decimal;
}



const double down_to_nearest(const double number) {
    return std::floor(number/round_to_decimal)*round_to_decimal;
}

const double specific_down_to_nearest(const double number) {
    return std::floor(number/specific_round_to_decimal)*specific_round_to_decimal;
}




















int check_position(
    std::string backtest_id, int ohlc_index, const VVD &ohlc_data, const VVD &trading_data,
    SmoothedMovingAverage &SMA, Volatility_IQR_AVG &vola_calc, TradingDataRunner &tdr,
    double distance_percent, double stop_loss_multiplier, double guaranteed_win_part) {



    const std::vector<double> &candle = ohlc_data[ohlc_index];
    const double &candle_timestamp = candle[0];
    const double &candle_open = candle[1];
    const double &candle_high = candle[2];
    const double &candle_low = candle[3];
    const double &candle_close = candle[4];

    bool long_entry_found = false, short_entry_found = false;
    double long_precise_entry_price, long_rounded_entry_price, short_precise_entry_price, short_rounded_entry_price;
    
    double base_value = SMA.get_sma();
    double price_volatility = vola_calc.get_volatility_iqr_avg();
    double portion = base_value*(distance_percent/100);



    // wichtig: wenn echter limit entry nicht möglich ist, dann wird übersprungen
    // -> live: es wird erst dann entry order gesetzt wenn open von candle echten limit entry zulässt

    // write_to_position_detect(std::to_string(candle_timestamp)+","+std::to_string(candle_open)+","+std::to_string(candle_high)+","+std::to_string(candle_low));




    // es muss mit gerundetem entry auf candle geschaut werden, aber mit präzisem entry gerechnet werden
    long_precise_entry_price = base_value-portion;
    
    if (candle_timestamp >= use_specific_after_timestamp) {
        long_rounded_entry_price = specific_to_nearest(long_precise_entry_price);
    }
    else {
        long_rounded_entry_price = to_nearest(long_precise_entry_price);
    }

    if (long_rounded_entry_price <= candle_high && long_rounded_entry_price >= candle_low && long_rounded_entry_price <= candle_open) {
        long_entry_found = true;
    }

    // kein else if

    short_precise_entry_price = base_value+portion;

    if (candle_timestamp >= use_specific_after_timestamp) {
        short_rounded_entry_price = specific_to_nearest(short_precise_entry_price);
    }
    else {
        short_rounded_entry_price = to_nearest(short_precise_entry_price);
    }



    if (short_rounded_entry_price <= candle_high && short_rounded_entry_price >= candle_low && short_rounded_entry_price >= candle_open) {
        short_entry_found = true;
    }


    if (long_entry_found == true && short_entry_found == true) {
        const bool b = tdr.check_which_entry_happened_first(candle_timestamp, long_rounded_entry_price, short_rounded_entry_price);
        if (b == true) {
            short_entry_found = false;
        }
        else {
            long_entry_found = false;
        }
    }





    if (long_entry_found == true) {

        double stop_loss_price = long_precise_entry_price-(price_volatility*stop_loss_multiplier);
        double risk_value_size = long_precise_entry_price-stop_loss_price;


        // mehrere Varianten für take profit

        double take_profit_price = (long_precise_entry_price+(long_precise_entry_price*fee_rate_decimal)) / (1-fee_rate_decimal);
        take_profit_price += guaranteed_win_part*risk_value_size;

        // double take_profit_price = long_precise_entry_price+(risk_value_size*guaranteed_win_part);

        // double take_profit_price = short_precise_entry_price+(price_volatility*guaranteed_win_part);


        // rounding
        if (candle_timestamp >= use_specific_after_timestamp) {
            stop_loss_price = specific_up_to_nearest(stop_loss_price);
            take_profit_price = specific_up_to_nearest(take_profit_price);
        }
        else {
            stop_loss_price = up_to_nearest(stop_loss_price);
            take_profit_price = up_to_nearest(take_profit_price);
        }

        std::string entry_side = "long";
        PositionTrade new_pos(backtest_id, entry_side, candle_timestamp, long_rounded_entry_price, stop_loss_price, take_profit_price, 4, 1, 3);

        // new_pos.set_additional_for_results_file(base_value, price_volatility); // added for results file

        std::vector<double> exit_stats = tdr.check_position_exit(
        entry_side, long_rounded_entry_price, ohlc_index, vola_calc, SMA,
        candle_timestamp, stop_loss_price, take_profit_price);
        
        if (tdr.is_backtesting_done() == true) {
            // wenn hier hin kommt dann war eine position offen
            // new_pos.show_all_variables();
            // beende backtesting
            return -1;
        }

        ohlc_index = exit_stats[0];
        new_pos.close(candle_timestamp, exit_stats[1], exit_stats[2]);

        return ohlc_index;
    }





    else if (short_entry_found == true) {

        double stop_loss_price = short_precise_entry_price+(price_volatility*stop_loss_multiplier);
        double risk_value_size = stop_loss_price-short_precise_entry_price;
        

        // mehrere Varianten für take profit

        // kalkuliert wo take profit muss anhand fee damit gegebener Anteil von risk (guaranteed_win_part) bei win garantiert ist
        double take_profit_price = (short_precise_entry_price-(short_precise_entry_price*fee_rate_decimal)) / (1+fee_rate_decimal);
        take_profit_price -= guaranteed_win_part*risk_value_size;

        // take profit Angabe (guaranteed_win_part) steht dann genauso in result datei, da abhängig von risk_value_size
        // double take_profit_price = short_precise_entry_price-(risk_value_size*guaranteed_win_part);
        
        // take profit ist nur abhängig von vola
        // double take_profit_price = short_precise_entry_price-(price_volatility*guaranteed_win_part);


        // rounding
        if (candle_timestamp >= use_specific_after_timestamp) {
            stop_loss_price = specific_down_to_nearest(stop_loss_price);
            take_profit_price = specific_down_to_nearest(take_profit_price);
        }
        else {
            stop_loss_price = down_to_nearest(stop_loss_price);
            take_profit_price = down_to_nearest(take_profit_price);
        }

        std::string entry_side = "short";
        PositionTrade new_pos(backtest_id, entry_side, candle_timestamp, short_rounded_entry_price, stop_loss_price, take_profit_price, 4, 1, 3);

        // new_pos.set_additional_for_results_file(base_value, price_volatility); // added for results file

        std::vector<double> exit_stats = tdr.check_position_exit(
        entry_side, short_rounded_entry_price, ohlc_index, vola_calc, SMA,
        candle_timestamp, stop_loss_price, take_profit_price);
        
        if (tdr.is_backtesting_done() == true) {
            // wenn hier hin kommt dann war eine position offen
            // new_pos.show_all_variables();
            // beende backtesting
            return -1;
        }

        ohlc_index = exit_stats[0];
        new_pos.close(candle_timestamp, exit_stats[1], exit_stats[2]);
    
        return ohlc_index;
    }





    // erst nach get_volatility_iqr_avg, sma und check_position_exit
    tdr.update_other(candle_timestamp, candle_close, vola_calc, SMA);





    // nichts traf zu
    return ohlc_index;

}





















void run_backtesting(const VVS &backtests_specs, const VVD &ohlc_data, const VVD &trading_data, const VVI &candle_timestamps_indices) {

    const int length_ohlc_data = ohlc_data.size();

    #pragma omp parallel for schedule(dynamic)
    for (const auto &current_spec : backtests_specs) {

        const std::string backtest_id = current_spec[0];

        // specs zuordnung
        const double current_distance_percent = std::stod(current_spec[1]);
        SmoothedMovingAverage SMA(std::stod(current_spec[2]));

        const double current_stop_loss_multiplier = std::stod(current_spec[3]);
        const double current_guaranteed_win_part = std::stod(current_spec[4]); // of risk
        const int start_timestamp = std::stoi(current_spec[5]);

        const int iqr_history_length = std::stoi(current_spec[6]), fragment_length = std::stoi(current_spec[7]);
        Volatility_IQR_AVG vola_calc(iqr_history_length, fragment_length);
        TradingDataRunner tdr(ohlc_data, trading_data, candle_timestamps_indices);


        // auf richtigen start timestamp bringen

        int ohlc_index = 0;
        int go_to_this_timestamp = start_timestamp % 86400;

        for (ohlc_index; ohlc_index<length_ohlc_data; ohlc_index++) {

            const int &timestamp = ohlc_data[ohlc_index][0];

            if ((timestamp+60) % 86400 == go_to_this_timestamp) { // +60 für optimierung
                break;
            }
        }


        // indikatoren vorlaufen lassen

        const int number_candles = ohlc_index+(iqr_history_length*fragment_length);
        for (ohlc_index; ohlc_index<number_candles; ohlc_index++) {

            const double &candle_timestamp = ohlc_data[ohlc_index][0];
            const double &candle_close = ohlc_data[ohlc_index][4];

            tdr.update_other(candle_timestamp, candle_close, vola_calc, SMA);

        }


        for (ohlc_index; ohlc_index<length_ohlc_data; ohlc_index++) {


            ohlc_index = check_position(
            backtest_id, ohlc_index, ohlc_data, trading_data,
            SMA, vola_calc, tdr,
            current_distance_percent, current_stop_loss_multiplier, current_guaranteed_win_part);


            // write_to_position_detect("check_position exit with "+std::to_string(output));


            if (ohlc_index == -1) {
                break; // backtesting done
            }


        }
    }
}

















int main() {

    base_path = boost::filesystem::initial_path().string() + '/';



    // measure time
    auto start = std::chrono::steady_clock::now();





    // load data
    // zuerst trading data laden, danach ohlc, da ohlc abhängig von trading data geladen wird
    const VVD trading_data = load_trading_data();

    const VVD ohlc_data = generate_ohlc_data(trading_data);

    const VVI candle_timestamps_indices = generate_candle_timestamps_indices(ohlc_data, trading_data);

    omp_set_num_threads(omp_get_max_threads());





    // measure time
    double duration = (std::chrono::steady_clock::now()-start).count();
    duration /= std::pow(10, 9);
    write_to_log("Load data in seconds: "+std::to_string(duration));
    write_to_log("Load data in minutes: "+std::to_string(duration/60));
    write_to_log("Trading data size: "+std::to_string(trading_data.size()));
    write_to_log("Ohlc data size: "+std::to_string(ohlc_data.size()));


    


    // sequenziell specs dateien abarbeiten (wegen speicherplatz und parallelism)
    // get files with specs
    std::vector<std::string> specs_files = get_all_files_in_folder(base_path+"bt_specs/");

    for (const auto &sf : specs_files) {





        // get specs
        const VVS backtests_specs = get_specs(sf);
        const std::string file_name = split(sf, '/').back();
        write_to_log("\nNumber backtests for " + file_name + ": "+std::to_string(backtests_specs.size()));



        

        // measure time
        start = std::chrono::steady_clock::now();





        run_backtesting(backtests_specs, ohlc_data, trading_data, candle_timestamps_indices);





        // measure time
        duration = (std::chrono::steady_clock::now()-start).count();
        duration /= std::pow(10, 9);
        write_to_log("Backtesting duration in seconds: "+std::to_string(duration));
        write_to_log("Backtesting duration in minutes: "+std::to_string(duration/60));
        start = std::chrono::steady_clock::now();





        // total size of results files
        uintmax_t bytes = get_size_of_folder(base_path+"bt_results/");
        write_to_log("bt_results/ size in bytes: "+std::to_string(bytes));
        double giga_bytes = bytes;
        giga_bytes /= std::pow(10, 9);
        write_to_log("bt_results/ size in gigabytes: "+std::to_string(giga_bytes));





        // analyse results
        analyse_results_files();
        




        // delete results
        // delete_all_files_in_folder(base_path+"bt_results/");





        // measure time
        duration = (std::chrono::steady_clock::now()-start).count();
        duration /= std::pow(10, 9);
        write_to_log("Analysing and deletion duration for " + file_name + " in seconds: "+std::to_string(duration));


    }

    return EXIT_SUCCESS;

}






