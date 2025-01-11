
#include <omp.h>
#include <vector>
#include <deque>
#include <cstdint>
#include <string>
#include <algorithm>
#include <variant>
#include <iterator>
#include <iostream>
#include <iomanip>
#include <sstream>
#include <fstream>
#include <filesystem>
#include <math.h>
#include <cmath>
#include <numeric>
#include <stdexcept>
#include <chrono>
#include <bits/stdc++.h>

#include <boost/filesystem.hpp>
#include <boost/math/statistics/bivariate_statistics.hpp>

using VVI = std::vector<std::vector<int>>;
using VVD = std::vector<std::vector<double>>;
using VVS = std::vector<std::vector<std::string>>;
using SDvariant = std::variant<std::string, double>;

extern const int min_number_pos_trades, use_specific_after_timestamp;
extern const double round_to_decimal, specific_round_to_decimal, min_r_squared, slippage_decimal, fee_rate_decimal;
extern std::string base_path;
extern const std::string path_to_trading_files;


const std::vector<std::string> split(const std::string s, const char delim);

const VVS get_specs(const std::string &file_path);

const std::vector<std::string> get_all_files_in_folder(const std::string &path_to_folder);

const uintmax_t get_size_of_folder(const std::string &path);

void delete_all_files_in_folder(const std::string &path_to_folder);









// profiler

class Collector {
    private:
        int size = 0;
        std::vector<std::string> all_func_names;
        std::vector<double> all_durations;
        std::vector<int> all_counts;

    public:
        Collector() {}

        ~Collector() {
            show();
        }
        
        void add(const std::string func_name, const double duration) {
            for (int i=0; i<size; i++) {
                const std::string &name = all_func_names[i]; 
                if (name == func_name) {
                    all_durations[i] += duration;
                    all_counts[i]++;
                    return;
                }
            }
            all_func_names.push_back(func_name);
            all_durations.push_back(duration);
            all_counts.push_back(1);
            size++;
        }

        void show() {
            std::ofstream fout;
            fout.open(base_path+"bt_logs/profiler_data.txt", std::ios::out | std::ios::app);
            for (int i=0; i<size; i++) {
                fout << all_func_names[i] << ",";
                fout << all_durations[i] << ",";
                fout << all_counts[i];
                fout << '\n';
            }
            fout.close();
        }

};


// profiler
extern Collector __c;


class TIMER {
    private:
        bool did_end = false;
        const std::string func_name;
        std::chrono::_V2::steady_clock::time_point start = std::chrono::steady_clock::now();

        void store_time() {
            std::chrono::duration<int64_t, std::nano> duration = std::chrono::steady_clock::now()-start;
            double d = duration.count();
            d /= std::pow(10, 9);
            __c.add(func_name, d);
        }

    public:

        TIMER(const std::string func_name) : func_name(func_name) {}

        ~TIMER() {
            if (did_end == false) {
                store_time();
            }
        }

        void end() {
            store_time();
            did_end = true;
        }

};



