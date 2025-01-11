
#include "position_trade.h"





void PositionTrade::write_to_results_file(const int entry_time_trade, const int exit_time, const double exit_price) {

    std::string result;
    double performance;
    const double duration = (exit_time-entry_time_trade)/60;

    if (entry_side == "long") {
        performance = (exit_price-entry_price)/risk_value_ticks;
    }
    else {
        performance = (entry_price-exit_price)/risk_value_ticks;
    }

    if (performance > 0) {
        result = "win";
    }
    else if (performance < 0) {
        result = "loss";
    }
    else {
        result = "breakeven";
    }

    std::ofstream fout;
    fout.open(base_path+"bt_results/"+backtest_id, std::ios::out | std::ios::app);

    fout << entry_side << ',';
    fout << std::fixed << std::setprecision(time_precision)
        << entry_time_trade << ',';
    fout << std::fixed << std::setprecision(price_precision)
        << entry_price << ','
        << stop_loss_price << ','
        << risk_value_ticks << ',';
    fout << std::fixed << std::setprecision(time_precision)
        << exit_time << ',';
    fout << std::fixed << std::setprecision(price_precision)
        << exit_price << ',';
    fout << std::fixed << std::setprecision(0)
        << duration << ',';
    fout << std::fixed << std::setprecision(performance_precision)
        << performance << ',';
    fout << result << ',';
    fout << std::fixed << std::setprecision(price_precision)
        << take_profit_price; // << ',';

    // additional
    // fout << std::fixed << std::setprecision(0)
    //     << entry_time_candle << ',';
    // fout << std::fixed << std::setprecision(8)
    //     << vola_now;

    fout << '\n';
    fout.close();
}






PositionTrade::PositionTrade(
const std::string backtest_id, const std::string entry_side, const double entry_time_candle, const double entry_price,
const double stop_loss_price, const double take_profit_price, const int time_precision, const int price_precision, const int performance_precision)
:
backtest_id(backtest_id), entry_side(entry_side), entry_time_candle(entry_time_candle), entry_price(entry_price),
stop_loss_price(stop_loss_price), take_profit_price(take_profit_price), risk_value_ticks(std::abs(entry_price-stop_loss_price)),
time_precision(time_precision), price_precision(price_precision), performance_precision(performance_precision) {}






void PositionTrade::close(const int entry_timestamp, const int exit_timestamp, const double exit_price) {
    write_to_results_file(entry_timestamp, exit_timestamp, exit_price);
}



// void PositionTrade::set_additional_for_results_file(double sma_now, double vola_now) {
//     this->sma_now = sma_now;
//     this->vola_now = vola_now;
// }


/*
void PositionTrade::show_all_variables() {
    std::cout << entry_side << ',';
    std::cout << std::fixed << std::setprecision(time_precision)
        << entry_time_trade << ',';
    std::cout << std::fixed << std::setprecision(price_precision)
        << entry_price << ','
        << stop_loss_price << ','
        << risk_value_ticks << ',';
    std::cout << std::fixed << std::setprecision(time_precision)
        << exit_time << ',';
    std::cout << std::fixed << std::setprecision(price_precision)
        << exit_price << ',';
    std::cout << std::fixed << std::setprecision(time_precision)
        << duration << ',';
    std::cout << std::fixed << std::setprecision(performance_precision)
        << performance << ',';
    std::cout << result << ',';
    std::cout << std::fixed << std::setprecision(price_precision)
        << take_profit_price << ',';

    // additional
    std::cout << std::fixed << std::setprecision(8)
        << sma_now << ',';
    std::cout << std::fixed << std::setprecision(time_precision)
        << entry_time_candle << ',';

    std::cout << std::endl;
}
*/



