count=0
print("enter the name to find no of vowels")
char = input()
for letter in char:
    if letter in ['A','E','I','O','U','a','e','i','o','u']:
        count = count+1

print(count)
