'''

analysing Zusammenhang/Korrelation von money performance & Abstand abs win quote zu breakeven abs win quote

Ist money performance besser je weiter die abs win quote entfernt von der breakeven win quote ist?

Resultat:
-> es ist zu erkennen dass je weiter entfernt die abs win quote zur breakeven quote ist, relativ gesehen zu 100%,
    desto mehr money performance ist machbar
    -> wahrscheinlich deshalb, weil drawdowns weniger sind
    -> es ist aber nicht oft der Fall, deshalb einfach money performance rechnen lassen
        dann von den besten solche nehmen mit große risk value ticks, große abs win quote etc


filter & money performance sollten auf den gleichen Zeitraum berechnet sein (CATT & CBTT)
'''


import csv, pandas, numpy
import matplotlib .pyplot as plt
from sklearn import linear_model
from _share_files.analyse_functions import Decistr

basic_path = '/home/jpbeerhold/Desktop/Trading/Day Trading/Code/Backtesting/Results n Analyser/Results/'
# basic_path = ''

# strategy path
basic_path += 'Down Settling BR/Bybit BTCUSDT Perp/OHLC + Trading/'

# folder path
# folder = '46145-64577/46145-64577_turned/'
# folder =  '40001-46144/'
basic_path += '1-40k/'



input_file = basic_path+'filter_Jan-Jul2022.txt'


'''
next:

money performance results von instance + filter nehmen
beide sind jan-jul2022
und evtl korrelationen finden




'''



# data ziehen

with open(input_file) as f:
    data_1 = list(csv.reader(f))
del data_1[0:3]
print(data_1[0])
print(len(data_1))




input_file = basic_path+'money_performance_results_Jan-Jul2022.txt'
with open(input_file) as f:
    data_2 = list(csv.reader(f))
del data_2[0:12]
print(data_2[0])




# nur alle files beachten die in data_2 existieren, da input file weniger hat

data_2_files = [item[0] for item in data_2]

for i in range(len(data_1)-1, -1, -1):
    if data_1[i][0] not in data_2_files:
        del data_1[i]






all_file_names = [item[0] for item in data_1]

all_abs_win_quotes = [Decistr(item[1])/100 for item in data_1]

all_reward_sizes = [Decistr(item[2]) for item in data_1]

all_breakeven_quotes = [1/(Decistr(item)+1) for item in all_reward_sizes]




all_differences = []

assert len(all_abs_win_quotes) == len(all_breakeven_quotes)

for i in range(len(all_abs_win_quotes)):
    # assert all_abs_win_quotes[i] > all_breakeven_quotes[i]
    all_differences.append(Decistr(all_abs_win_quotes[i])-Decistr(all_breakeven_quotes[i]))










# abhängig davon welche files genannt werden wird hier die performance genommen

all_money_performances = []
for current_file in all_file_names:
    for item in data_2:
        if item[0] == current_file:
            all_money_performances.append(Decistr(item[1]))
            break







all_relative_portions = [] # alle Differenzen geteilt durch 1-breakeven quotes

for i in range(len(all_differences)):
    all_relative_portions.append( Decistr(all_differences[i])/(1-Decistr(all_breakeven_quotes[i])) )




assert len(all_money_performances) == len(all_file_names) == len(all_relative_portions) == len(all_differences)




all_relative_win_quotes = []
for row in data_1:
    number_win_trades = round( Decistr(row[4])*(Decistr(row[1])/100) )
    number_loss_trades = Decistr(row[4])-number_win_trades
    reward_size = Decistr(row[2])
    rel_win_quote = (reward_size*number_win_trades)/( (reward_size*number_win_trades)+number_loss_trades )
    all_relative_win_quotes.append(rel_win_quote)



# datei bereits sortiert und in data frame packen

# all_together = pandas.DataFrame(
#     data=list(zip(all_file_names, all_reward_sizes, all_abs_win_quotes, all_breakeven_quotes,
#             all_differences, all_money_performances, all_relative_portions, all_relative_win_quotes)),
#     columns=['file', 'reward sizes', 'abs win quotes', 'breakeven win quotes',
#             'differences', 'money performances', 'relative portions', 'rel win quotes']
# )


# print(all_together)



model = linear_model.LinearRegression()

x = all_relative_portions
y = all_money_performances

# for i in range(len(x)-1, -1, -1):
#     if x[i] <= 0.5:
#         del x[i], y[i]

x = numpy.array(x).reshape(-1, 1)
y = numpy.array(y)

model.fit(x, y)
r_squared = model.score(x, y)
print(r_squared)




plt.scatter(x, y)
plt.show()









