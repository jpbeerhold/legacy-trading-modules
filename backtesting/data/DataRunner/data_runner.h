
#include "../ExtremaFinder/extrema_finder.h"







class TradingDataRunner {
    private:
        const int length_ohlc_data, length_trading_data;
        const VVD &ohlc_data, &trading_data;
        const VVI &candle_timestamps_indices;

        bool bt_done = false;
        int index_trading_data, index_candle_timestamps_indices = 0;
        
        void find_candle_timestamp_index(const int candle_timestamp);

        const std::vector<double> &get_trade();

        const double check_stop_loss_and_take_profit_with_trading_data(
        const std::string entry_side, const double entry_price,
        const int entry_candle_timestamp, const int exit_candle_timestamp,
        const double stop_loss_price, const double take_profit_price);

        const double check_if_take_profit_happened_with_trading_data(
        const std::string entry_side, const double entry_price, const int entry_candle_timestamp, const double take_profit_price);
    

    public:
        TradingDataRunner(const VVD &ohlc_data, const VVD &trading_data, const VVI &candle_timestamps_indices);
        TradingDataRunner(const VVD &&, const VVD &&, const VVI &&) = delete; // prevents rvalue binding

        const bool is_backtesting_done() const;

        const bool check_which_entry_happened_first(const double entry_candle_timestamp, const double long_entry_price, const double short_entry_price);

        const std::vector<double> check_position_exit(
        const std::string entry_side, const double entry_price, int ohlc_index,
        Volatility_IQR_AVG &vola_calc, ExtremaFinder &ef,
        const int entry_candle_timestamp,
        const double stop_loss_price, const double take_profit_price);


        void update_other(const double candle_timestamp, const double candle_close, Volatility_IQR_AVG &vola_calc, ExtremaFinder &ef);

};






