
#include "../ResultsAnalyser/results_analyser.h"

/*
Input numbers sollten gerundet sein
Precision Angabe auf wie viele Nachkommastellen gespeichert werden soll
*/
class PositionTrade {
    private:
        const std::string backtest_id, entry_side;
        const double entry_time_candle, entry_price, stop_loss_price, take_profit_price, risk_value_ticks;
        const int time_precision, price_precision, performance_precision;

        // additional
        // double sma_now, vola_now;

        void write_to_results_file(const int entry_time_trade, const int exit_time, const double exit_price);


    public:
        PositionTrade(
        const std::string backtest_id, const std::string entry_side, const double entry_time_candle, const double entry_price,
        const double stop_loss_price, const double take_profit_price, const int time_precision, const int price_precision, const int performance_precision);

        void close(const int entry_timestamp, const int exit_timestamp, const double exit_price);

        // void set_additional_for_results_file(double sma_now, double vola_now);

        // void show_all_variables();
};


