#python just creates an object when we assign a value to a variable and if reinitialize
#re init to other then the link gets broken and new value is attached to variable

a=5
print(a)
a=9
print(a)

myvar=3+4j
print(myvar)
yourvar=3-2j
print(yourvar)

x=myvar+yourvar
print(x)


#string operations
str="hello sujith"   #declaring a string
print(str[6])    #prints the 7th letter
print(str[0:5]) #printf first 6 letters
print(str[6:])  #prints letters present after 6
print(str*4 )   #prints the 4 times, i.e.., n times if n is given
print(str+ "whats up") #concatenates string

