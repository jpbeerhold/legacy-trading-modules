
#include "../DataRunner/data_runner.h"



const VVD generate_ohlc_data(const VVD &trading_data);

const VVD load_trading_data();

const VVI generate_candle_timestamps_indices(const VVD &ohlc_data, const VVD &trading_data);

void write_to_log(const std::string text_to_write);



