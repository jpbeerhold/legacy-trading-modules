
NAME = bt_DoSe
GCC = g++ -std=c++17
BOOST = -lboost_system -lboost_filesystem
OPENMP = -fopenmp
OPT = -O3 # -Ofast



compile: settings.o vola_calc.o results_analyser.o position_trade.o base_value.o data_runner.o data_load.o strategy_loop.o
	$(GCC) $(OPENMP) $(OPT) settings.o vola_calc.o results_analyser.o position_trade.o base_value.o data_runner.o data_load.o strategy_loop.o -o $(NAME) $(BOOST)

settings.o: Settings/settings.h
	$(GCC) -c $(OPENMP) $(OPT) Settings/settings.cpp

vola_calc.o: VolaCalc/vola_calc.h
	$(GCC) -c $(OPENMP) $(OPT) VolaCalc/vola_calc.cpp

results_analyser.o: ResultsAnalyser/results_analyser.h
	$(GCC) -c $(OPENMP) $(OPT) ResultsAnalyser/results_analyser.cpp

position_trade.o: PositionTrade/position_trade.h
	$(GCC) -c $(OPENMP) $(OPT) PositionTrade/position_trade.cpp

base_value.o: BaseValue/base_value.h
	$(GCC) -c $(OPENMP) $(OPT) BaseValue/base_value.cpp

data_runner.o: DataRunner/data_runner.h
	$(GCC) -c $(OPENMP) $(OPT) DataRunner/data_runner.cpp

data_load.o: DataLoad/data_load.h
	$(GCC) -c $(OPENMP) $(OPT) DataLoad/data_load.cpp

strategy_loop.o:
	$(GCC) -c $(OPENMP) $(OPT) strategy_loop.cpp

clean:
	rm *.o $(NAME)

