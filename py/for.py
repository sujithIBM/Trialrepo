count=0
print("enter name")
name=input()
for letter in name:
    if (letter in['A','E','I','O','U','a','e','i','o','u']):
        count=count+1

print("no of vowels in word is",count)
