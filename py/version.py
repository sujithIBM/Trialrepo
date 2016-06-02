import re

example = 'vios1,1,U14,,,9.12.33.102,padmin,2.2.3.3,VIOS'

version = re.findall(r'(?:(\d+)\.)?(?:(\d+)\.)?(?:(\d+)\.)?(?:(\d+)\.)',example)

print(version)

