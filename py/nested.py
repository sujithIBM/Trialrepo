char=input()
if (ord(char)>=65 and ord(char)<=90) :
    print("upper case alphabet")
    if char in ['A','E','I','O','U']:
        print("vowel")
    else:
        print("consonant")
elif ord(char)>=97 and ord(char)<=122:
    print("lower case")
    if char in ['a','e','i','o','u']:
        print("vowel")
    else:
        print("consonant")
else:
    print("not a number")
