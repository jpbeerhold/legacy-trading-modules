

'''

copying result files into folder for easy download

'''


path_pull_from = '/home/run/results collection/bt_results ohlc + trading/64578-68894/'

path_push_to = '/home/run/analyse/other/to_download/'


import csv, shutil

with open('money_performance_results_Jun-Dec2022.txt') as f:
    data = list(csv.reader(f))

del data[0:12]
print(data[0])
# quit()

# files_to_download = [row[0]+'.txt' for row in data]
files_to_download = [row[0] for row in data]


for i in range(20):
    shutil.copyfile(path_pull_from+files_to_download[i], path_push_to+files_to_download[i])
print('done')

