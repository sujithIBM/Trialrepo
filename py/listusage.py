#Lists and tuples


#list in python is ahybrid data type, similar to array in c, but different data types

#usage of lists uses square brackets
 
mylist=['one','two',3,4.5,3+2j]
print(mylist)
print(mylist[0])  #gives the first value
print(mylist *3 )

newlist=[3,'sujith',4.0]

add=mylist+newlist
print(add)

newlist[0]="three"  #in lists we can update also
print(newlist)

#tuples  cannot update the tuples, and also uses parenthisis

mytuple=('one','number',10)
print(mytuple)

#remaining all same operations as lists, but updation is not possible, gives trace back error,


