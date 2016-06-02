import re

s='tpokenize these words'
words=re.compile(r'\b\w+\b|\$')
words.findall(s)
