import re

example = '''
Sujith is 20 ,and Suku is 23 years old.
Giri is 45 and his Wife is 43.
'''

ages = re.findall(r'\d{1,3}',example)
names = re.findall(r'[A-Z][a-z]*',example)

print(names)
print(ages)

'''ageDict = {}

x = 0
for eachName in names:
    ageDict[eachName] = ages[x]
    x+=1

print(ageDict)
'''
'''
^(?:(\d+)\.)?(?:(\d+)\.)?(?:(\d+)\.)?(?:(\d+)\.)$ '''
