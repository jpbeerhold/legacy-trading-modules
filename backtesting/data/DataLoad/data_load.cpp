
#include "data_load.h"





/*

in v3
lädt trading data nur wenn geänderter preis
nutzt nur trading data wenn stop loss & take profit in gleicher candle sind

front() und at(0) kein performance unterschied
back() und at( size()-1 ) kein performance unterschied

*/












void write_to_log(const std::string text_to_write) {
    std::ofstream fout;
    fout.open(base_path+"bt_logs/bt_log.txt", std::ios::out | std::ios::app);
    fout << text_to_write+'\n';
    fout.close();
}






void does_file_exist(const std::string path) {
    bool e = std::filesystem::exists(path);
    if (e == false) {
        throw std::invalid_argument(path+" does not exist.");
    }
}








const std::vector<double> get_max_and_min(const VVD &current_trades) {

    /*
    benchmark auf ARM cloud machine ist ohne at(i) ein ganz bisschen schneller
    */

    // const int length_current_trades = current_trades.size();
    double max = current_trades.front()[1], min = max, price;

    for (const auto &trade : current_trades) {
    // for (int i=1; i<length_current_trades; i++) {

        // price = current_trades[i][1];
        price = trade[1];

        if (price > max) {
            max = price;
        }
        // kein else if
        if (price < min) {
            min = price;
        }

    }

    return {max, min};

}



const VVD generate_ohlc_data(const VVD &trading_data) {

    write_to_log("Generating ohlc data");
    write_to_log("Trading data very first timestamp: "+std::to_string(trading_data.front()[0]));
    write_to_log("Trading data very last timestamp: "+std::to_string(trading_data.back()[0]));

    int candle_timestamp = trading_data.front()[0];

    while (candle_timestamp % 60 != 0) {
        candle_timestamp--;
    }

    int next_candle_timestamp = candle_timestamp+60;

    std::vector<double> trade, max_min;
    VVD current_trades;

    double trade_timestamp, trade_price, open, high, low, close = trading_data.front()[1];
    VVD ohlc_data;

    // trading data durchgehen
    int index = 0;
    const int length_trading_data = trading_data.size();

    while (index<length_trading_data) {

        trade = trading_data[index];
        trade_timestamp = trade[0];
        trade_price = trade[1];

        // trades finden für aktuelle candle
        if (trade_timestamp < next_candle_timestamp) {

            index++;
            current_trades.push_back({trade_timestamp, trade_price});
            continue;

        }
        
        // trade timestamp ist größer gleich

        // kein trades gefunden für diese candle
        else if (current_trades.size() == 0) {
            // kann beim aller erster candle nicht passieren

            ohlc_data.push_back({double(candle_timestamp), close, close, close, close});
        }
        
        // trades gefunden
        else {

            max_min = get_max_and_min(current_trades);

            open = close;
            high = max_min[0];
            low = max_min[1];
            close = current_trades.back()[1];

            ohlc_data.push_back({double(candle_timestamp), open, high, low, close});

            current_trades.clear();

        }

        candle_timestamp += 60;
        next_candle_timestamp += 60;

    }

    // damit auch auf endliche trading data eine candle generiert wird
    // endliche trading data ist vollständig
    // current trades wird immer Inhalt haben da in load trading data Ende entfernt wurde
    max_min = get_max_and_min(current_trades);
    open = close;
    high = max_min[0];
    low = max_min[1];
    close = current_trades.back()[1];
    ohlc_data.push_back({double(candle_timestamp), open, high, low, close});

    write_to_log("Ohlc data very first timestamp: "+std::to_string(ohlc_data.front()[0]));
    write_to_log("Ohlc data very last timestamp: "+std::to_string(ohlc_data.back()[0]));

    return ohlc_data;

}





/*
const VVD load_ohlc_data(const VVD &trading_data) {

    does_file_exist(path_to_ohlc);

    std::ifstream inputFile;
    inputFile.open(path_to_ohlc);

    int load_after_this_timestamp = trading_data.front()[0];
    int load_until_this_timestamp = trading_data.back()[0];

    while (load_after_this_timestamp % 60 != 0) {
        load_after_this_timestamp--;
    }
    while (load_until_this_timestamp % 60 != 0)
    {
        load_until_this_timestamp--;
    }

    write_to_log("Loading ohlc data after including timestamp: "+std::to_string(load_after_this_timestamp));
    write_to_log("Loading ohlc data until including timestamp: "+std::to_string(load_until_this_timestamp));

    write_to_log("Trading data very first timestamp: "+std::to_string(trading_data.front()[0]));
    write_to_log("Trading data very last timestamp: "+std::to_string(trading_data.back()[0]));

    std::vector<double> current_ohlc;
    std::vector<std::vector<double>> ohlc_data;

    std::string temp_str, line;
    double timestamp, open, high, low, close;

    while (getline(inputFile, line)) {
        std::stringstream inputString(line);

        // timestamp
        getline(inputString, temp_str, ',');
        timestamp = std::stod(temp_str);


        if (timestamp >= load_after_this_timestamp && timestamp <= load_until_this_timestamp) {

            current_ohlc.push_back(timestamp);

            // open
            getline(inputString, temp_str, ',');
            open = std::stod(temp_str);
            current_ohlc.push_back(open);

            // high
            getline(inputString, temp_str, ',');
            high = std::stod(temp_str);
            current_ohlc.push_back(high);

            // low
            getline(inputString, temp_str, ',');
            low = std::stod(temp_str);
            current_ohlc.push_back(low);

            // close
            getline(inputString, temp_str, ',');
            close = std::stod(temp_str);
            current_ohlc.push_back(close);


            ohlc_data.push_back(current_ohlc);

            if (timestamp == load_until_this_timestamp) {
                break;
            }

            current_ohlc.clear();

        }

    }

    return ohlc_data;
}
*/























int find_index(const int start_index, const int ohlc_timestamp, const int length_trading_data, const VVD &trading_data, VVI &candle_timestamps_indices) {

    // in trading data index finden wo ohlc timestamp anfängt und diesen speichern

    for (int i=start_index; i<length_trading_data; i++) {

        if (trading_data[i][0] >= ohlc_timestamp) {
            candle_timestamps_indices.push_back({ohlc_timestamp, i-1}); // -1 für open preis
            return i; // nur das alleine zurückgeben damit mit lücken in trading data richtig gearbeitet wird
        }

    }

    throw std::invalid_argument("index not found for: " + std::to_string(ohlc_timestamp));

}


const VVI generate_candle_timestamps_indices(const VVD &ohlc_data, const VVD &trading_data) {
    /*
    speichert in candle_timestamps_indices die Stellen an denen die open von candle timestamps von ohlc data in trades data anfangen,
    für schnelleren Zugriff und somit schnelleres backtesting
    
    wichtig als open wird aller letzter preis welcher gehandelt wurde von candle davor genommen
    als close wird zuletzt gehandelter preis genommen (trade timestamp kleiner als nächster start timestamp)
    für high & low alle dazwischen
    */

    const int length_ohlc_data = ohlc_data.size();
    const int length_trading_data = trading_data.size();
    int ohlc_timestamp = ohlc_data[0][0], start_index = 1;

    VVI candle_timestamps_indices;
    candle_timestamps_indices.reserve(length_ohlc_data); // faster push back in find_index()
    candle_timestamps_indices.push_back({ohlc_timestamp, 0}); // very first timestamp

    for (int i=start_index; i<length_ohlc_data; i++) {

        ohlc_timestamp = ohlc_data[i][0];
        start_index = find_index(start_index, ohlc_timestamp, length_trading_data, trading_data, candle_timestamps_indices);

    }

    return candle_timestamps_indices;

}












const std::vector<std::string> get_trading_data_files_names() {
    does_file_exist(base_path+"DataLoad/trading_data_files_names.txt");

    std::ifstream inputFile;
    inputFile.open(base_path+"DataLoad/trading_data_files_names.txt");

    std::vector<std::string> files_names_trading_data;
    std::string line, name;
    while (getline(inputFile, line)) {
        std::stringstream inputString(line);
        getline(inputString, name);
        files_names_trading_data.push_back(name);
    }

    for (const std::string &f : files_names_trading_data) {
        does_file_exist(path_to_trading_files+f);
    }

    return files_names_trading_data;
}





const VVD load_trading_data() {

    const std::vector<std::string> files_names_trading_data = get_trading_data_files_names();

    std::string temp_str, line;
    std::vector<double> current_trade;
    VVD trading_data;
    double timestamp, price, before_price = 0;

    for (const std::string &current_file_name : files_names_trading_data) {

        std::ifstream inputFile;
        inputFile.open(path_to_trading_files+current_file_name);

        while (getline(inputFile, line)) {
            std::stringstream inputString(line);

            // holt sich nacheinander alle elemente zwischen trennzeichen 

            getline(inputString, temp_str, ',');
            timestamp = std::stod(temp_str);

            getline(inputString, temp_str, ',');
            price = std::stod(temp_str);


            // getline(inputString, temp_str, ',');
            // double size = std::stod(temp_str);
            // current_trade.push_back(size);

            // string side;
            // getline(inputString, side, ',');
            // current_trade.push_back(side);


            if (price != before_price) {

                // in dieser Reihenfolge
                current_trade.push_back(timestamp);
                current_trade.push_back(price);

                trading_data.push_back(current_trade);

                current_trade.clear();

                before_price = price;
            }

        }
    }

    // hat alle trading data geladen die es gibt
    // schneidet aller letzte trading ab da unvollständig

    int t = trading_data.back()[0];
    while (t % 60 != 0) {
        t--;
    }

    while (true) {
        if (trading_data.back()[0] >= t) {
            trading_data.pop_back();
        }
        else {
            break;
        }
    }

    return trading_data;
}






