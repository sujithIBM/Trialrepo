import re

example = '''
vios1,1,U14,,,9.12.33.102,padmin,2.2.3.3,VIOS
'''

version = re.findall(r'^(?:(\d+)\.)?(?:(\d+)\.)?(?:(\d+)\.)?(?:(\d+)\.)$',example)

print(version)


shakes = open("wssnt10.txt", "r")

for line in shakes:
    if re.match("(.*)(L|l)ove(.*)", line):
        print line,
