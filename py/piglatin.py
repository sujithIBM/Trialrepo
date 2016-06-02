'''def main():        
    sentence = input('Type what you would like translated into pig-latin and press ENTER: ')
    sentence_list = sentence.split()

    for part in sentence_list:
        first_letter = part[0]

main()
'''
name = input("enter the word :")
if name.isalpha():
    print("yes")
    x=len(name)
    print("%d",x)
    name[x]=name[0]
    print(name)
else :
    print("not a name")
