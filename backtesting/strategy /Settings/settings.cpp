
#include "settings.h"



// für runden
const double round_to_decimal = 0.5, specific_round_to_decimal = 0.1;
const int use_specific_after_timestamp = 1676013900; // at after this timestamp use 0.1, derived from data



// für data load
std::string base_path;
const std::string path_to_trading_files = "/home/run/all_data/Trades/";
// const std::string path_to_trading_files = "/home/jpbeerhold/Desktop/approved data/Bybit/BTCUSDT_PERP/Trades_Data/";



// für results analyser
const int min_number_pos_trades = 1000;
const double min_r_squared = 0.8;
const double slippage_decimal = 0.035;
const double fee_rate_decimal = 0.0002; // also used for take profit calc
















// profiler
Collector __c;













const std::vector<std::string> split(const std::string s, const char delim) {
    std::string tmp;
    std::vector<std::string> elems;
    std::stringstream ss(s);
    while(getline(ss, tmp, delim)) {
        elems.push_back(tmp);
    }
    return elems;
}














const VVS get_specs(const std::string &file_path) {

    // create input stream
    std::ifstream inputFile;
    inputFile.open(file_path);

    std::vector<std::string> current_line;
    VVS file_content;

    std::string temp_str, line;

    // insert string into line variable
    // loop as long as there is something
    while (getline(inputFile, line)) {
        // line into stringstream
        std::stringstream inputString(line);

        // get characters from stringstream until seperator
        while (getline(inputString, temp_str, ',')) {
            current_line.push_back(temp_str);
        }

        file_content.push_back(current_line);

        current_line.clear();
        
    }

    return file_content;

}












/*
gibt vector mit ganzen paths jeder datei zurück
*/
const std::vector<std::string> get_all_files_in_folder(const std::string &path_to_folder) {

    std::vector<std::string> files_names;

    for (const auto &entry : std::filesystem::directory_iterator(path_to_folder)) {
        files_names.push_back(entry.path().string());
    }

    std::sort(files_names.begin(), files_names.end());

    return files_names;

}










/*
return in bytes
*/
const uintmax_t get_size_of_folder(const std::string &path) {

    std::vector<std::string> v = get_all_files_in_folder(path);

    uintmax_t size = 0;
    for (const auto &f : v) {
        size += std::filesystem::file_size(f);
    }

    return size;

}












void delete_all_files_in_folder(const std::string &path_to_folder) {

    std::vector<std::string> files_names = get_all_files_in_folder(path_to_folder);

    #pragma omp parallel for schedule(dynamic)
    for (const auto &fn : files_names) {
        std::filesystem::remove(fn);
    }

}









