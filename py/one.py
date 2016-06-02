import csv
'''
list1=[]
with open('C:\\Users\\IBM_ADMIN\\Desktop\\test.csv','r') as f:
        test1= csv.reader(f)
        for row in test1:
                list1.append(row)

len(list1)
list1[2]
list2=[]
i=0
while i <10:
	list2.append(list1[i])
	i=i+1
for x in list2:
        print(x)
a=list2[0]
print("the value to be added to the test2 is :")
print(a)
with open("C:\\Users\\IBM_ADMIN\\Desktop\\test2.csv", "w") as f:
	writer = csv.writer(f, delimiter=',', quoting=csv.QUOTE_MINIMAL, lineterminator='\n')
	writer.writerows(a)
'''
import random
nlines = 1507
ifile = open("C:\\Users\\IBM_ADMIN\\Desktop\\test.csv")
lines = []
samples = random.sample(range(nlines))
for sample in samples:
    ifile.seek(sample)
    lines.append(ifile.readline())
    print(lines)
