
#include "results_analyser.h"










std::deque<double> get_performance_column(const std::string file_path) {

    // create input stream
    std::ifstream inputFile;
    inputFile.open(file_path);

    std::deque<double> column_content;

    int i = 0;
    std::string temp_str, line;

    // insert string into line variable
    // loop as long as there is something
    while (getline(inputFile, line)) {
        // line into stringstream
        std::stringstream inputString(line);

        // get characters from stringstream until seperator
        // nur performance notwendig
        while (getline(inputString, temp_str, ',')) {
            i++;
            if (i == 9) {
                i = 0;
                break;
            }
        }

        const double &performance = std::stod(temp_str);

        // check if nan or inf
        if (std::isfinite(performance) == true) {
            column_content.push_back(performance);
        }

    }

    return column_content;

}








/*
entry price, risk value ticks, exit price, performance
*/
std::deque<std::vector<double>> get_multiple_specific(const std::string &file_path) {

    // create input stream
    std::ifstream inputFile;
    inputFile.open(file_path);

    std::vector<double> required(4);
    std::vector<std::string> current_line;
    std::deque<std::vector<double>> file_content;

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

        const double &performance = std::stod(current_line[8]);

        // check if nan or inf
        if (std::isfinite(performance) == true) {
            
            required[0] = std::stod(current_line[2]); // entry price
            required[1] = std::stod(current_line[4]); // risk value ticks
            required[2] = std::stod(current_line[6]); // exit price
            required[3] = performance; // performance

            file_content.push_back(required);

        }

        current_line.clear();
        
    }

    return file_content;

}







/*

double get_r_squared_function(const DVS &single_file) {

    std::vector<double> y_data, x_data;

    double performance = 0;
    for (const auto &row : single_file) {
        performance += std::stod(row[8]);
        y_data.push_back(performance);
    }

    for (int i=1; i<y_data.size()+1; i++) {
        x_data.push_back(i);
    }

    double x_sum = 0, y_sum = 0, x_avg, y_avg, Sxx, Sxy, m; // b;

    for (int i=0; i<x_data.size(); i++) {
        x_sum += x_data[i];
        y_sum += y_data[i];
    }

    if (x_sum == 0) {
        x_avg = 0;
    }
    else {
        x_avg = x_sum/x_data.size();
    }

    if (y_sum == 0) {
        y_avg = 0;
    }
    else {
        y_avg = y_sum/y_data.size();
    }

    for (int i=0; i<x_data.size(); i++) {
        Sxx += std::pow(x_data[i]-x_avg, 2);
        Sxy += (x_data[i]-x_avg)*(y_data[i]-y_avg);
    }

    if (Sxy == 0 || Sxx == 0) {
        m = 0;
    }
    else {
        m = Sxy/Sxx;
    }

    // b = y_avg-(m*x_avg);

    return m;

}


*/









const double get_r_squared(const std::deque<double> &performance_column) {

    // create y data, Verlauf der Performance
    std::vector<double> y_data;
    y_data.reserve(performance_column.size()); // faster push back
    double performance = 0;
    for (const auto &p : performance_column) {
        performance += p;
        y_data.push_back(performance);
    }

    // create x data
    std::vector<double> x_data(performance_column.size()); // kreiert objekte
    std::iota(x_data.begin(), x_data.end(), 1); // range ab 1

    const double r = boost::math::statistics::correlation_coefficient(y_data, x_data);

    return r*r;

}










const double get_total_performance(const std::deque<double> &performance_column) {

    return std::reduce(performance_column.begin(), performance_column.end());

}












/*
hängt data an (append mode)
*/
void write_analyse_results_to_file_in_csv_format(const std::string &file_path, const std::vector<std::vector<SDvariant>> &data_to_write) {

    std::ofstream fout;
    fout.open(file_path, std::ios::out | std::ios::app);

    for (const auto &row : data_to_write) {

        // wenn resultat nicht zutraf ist vector leer
        if (row.size() == 0) {
            continue;
        }

        fout << std::get<std::string>(row[0]) << ','; // file name
        fout << std::fixed << std::setprecision(4) << std::get<double>(row[1]) << ','; // r²
        fout << std::fixed << std::setprecision(0) << std::get<double>(row[2]) << ','; // number_pos_trades_at_max
        fout << std::fixed << std::setprecision(0) << std::get<double>(row[3]); // total_number_pos_trades

        fout << '\n';

    }

    fout.close();

}











void analyse_performance_column(const int index_in_stats, const std::string &file_name, std::deque<double> &performance_column, std::vector<std::vector<SDvariant>> &stats_to_change) {


    // analysiert performance durch entfernen des ersten elements und speichert wichtige stats

    double current_max_r_squared = -1; // muss auf -1 sein damit nie größer ist als min r² auch wenn 0 angegeben wird
    int current_number_position_trades_at_max;

    const int current_total_number_pos_trades = performance_column.size();
    double current_total_performance = get_total_performance(performance_column);


    if (current_total_number_pos_trades >= min_number_pos_trades) {

        while (true) {
            
            // positive performance notwendig
            if (current_total_performance > 0) {
                double current_r_squared = get_r_squared(performance_column);

                // finde max r² mit position anzahl
                if (current_r_squared > current_max_r_squared) {
                    current_max_r_squared = current_r_squared;
                    current_number_position_trades_at_max = performance_column.size();
                }
            }

            if (performance_column.size() == min_number_pos_trades) {
                break;
            }

            current_total_performance -= performance_column.front();
            performance_column.pop_front();

        }

    }

    if (current_max_r_squared >= min_r_squared) {
        stats_to_change[index_in_stats] = {file_name, current_max_r_squared, double(current_number_position_trades_at_max), double(current_total_number_pos_trades)};
    }

}












void analyse_raw(const int index_in_stats, const std::string &file_name, const std::string &file_path, std::vector<std::vector<SDvariant>> &raw_stats) {
    /*
    finde das beste r² in roher performance (keine fee & slippage)
    */

    // braucht nur performance
    std::deque<double> performance_column = get_performance_column(file_path);

    analyse_performance_column(index_in_stats, file_name, performance_column, raw_stats);

}












void analyse_with_fees_and_slippage(const int index_in_stats, const std::string &file_name, const std::string &file_path, std::vector<std::vector<SDvariant>> &fees_and_slippage_stats) {
    /*
    finde das beste r² in tatsächlicher performance (mit fee & slippage)
    */

    // beinhaltet entry price, risk value ticks, exit price, performance um performance nach cost barrier berechnen zu können
    std::deque<std::vector<double>> multiple = get_multiple_specific(file_path);
    std::deque<double> actual_performance; // performance column mit performance nach cost barrier

    // change performance
    double performance, fee_barrier;

    for (const auto &pos_trade : multiple) {

        const double &entry_price = pos_trade[0];
        const double &risk_value_size = pos_trade[1];
        const double &exit_price = pos_trade[2];
        performance = pos_trade[3];

        // Achtung je nach Strategie ist es unterschiedlich wie slippage angerechnet wird
        if (performance < 0) { // loss
            performance -= slippage_decimal;
        }

        fee_barrier = (entry_price*fee_rate_decimal)+(exit_price*fee_rate_decimal);
        fee_barrier /= risk_value_size;
        performance -= fee_barrier;
        actual_performance.push_back(performance);

    }

    analyse_performance_column(index_in_stats, file_name, actual_performance, fees_and_slippage_stats);

}













void analyse_results_files() {

    // alle results dateien path holen
    const std::vector<std::string> results_files_paths = get_all_files_in_folder(base_path+"bt_results/");
    const int length_results_files = results_files_paths.size();
    
    // kreierte objekte sind leere vectoren
    std::vector<std::vector<SDvariant>> raw_stats(length_results_files);
    std::vector<std::vector<SDvariant>> fees_and_slippage_stats(length_results_files);

    // parallel results files analysieren
    #pragma omp parallel for schedule(dynamic)
    for (int i=0; i<length_results_files; i++) {

        const std::string &current_path = results_files_paths[i];

        const std::string file_name = split(current_path, '/').back();

        analyse_raw(i, file_name, current_path, raw_stats);

        analyse_with_fees_and_slippage(i, file_name, current_path, fees_and_slippage_stats);

    }

    write_analyse_results_to_file_in_csv_format(base_path+"bt_logs/check_log_raw.txt", raw_stats);

    write_analyse_results_to_file_in_csv_format(base_path+"bt_logs/check_log_fees_and_slippage.txt", fees_and_slippage_stats);

}









