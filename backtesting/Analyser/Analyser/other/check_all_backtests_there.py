
import csv


with open('z.txt') as f:
    data = list(csv.reader(f))

l = []

for item in data:
    l.append(int(float(item[0])))

l.sort()

for i in range(len(l)-1):
    assert l[i+1] - l[i] == 1


print(max(l), min(l))
