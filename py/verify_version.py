paras = { 'label': 'rack_switch',
      'rack_id': 'a',
      'rack_location': 'loc',
      'machine_type_model': 'Not_mentioned', 
      'serial_number':'Not_mentioned',
      'ipv4_address': '192.168.93.83',
      'user': 'admin',
      'password': 'admin',
      'device_type': 'IBM_Switch',
          'version':'7.45'}
data=[['HMC_217', 'Hardware Management Console', 'd - HMC', 'hscroot', '7042-CR5', '10E33BB', '9.12.29.217', '8.2.0'],
 ['IBM_Switch1', 'Lenovo OEM Switch', '4 - U19', 'admin', '7120-48E', '1003317', '192.168.93.81', '7.11.2'],
 ['Mellanox1', 'Mellanox Switch', '4 - U20', 'admin', 'MSX1710', 'MT1518X00300', '192.168.93.37', '3.4.1120'],
 ['PDU1', 'Power Distribution Unit', '4 -', 'USERID', '00FW789', '4A7071', '192.168.93.25', ' '],
 ['V7K4', 'V7000', '4 - U12', 'superuser', '2076-524', '782195N', '192.168.93.8', '7.4.0.5'],
 ['VIOS1', 'Virtual I/O Server', '4 - U2', 'padmin', ' ', ' ', '192.168.93.89', '2.2.3.52'],
 ['hmc4-imm', 'Integrated Management Module', '4 - U7', 'USERID', '837401M', 'E2NF337', '9.3.46.189', '4.56']]




'''
sample =[['rack_switch','a','loc','Not_mentioned', 'Not_mentioned','192.168.93.83','admin','admin','IBM_Switch','7.45'],
['rack_switch','a','loc','Not_mentioned', 'Not_mentioned','192.168.93.83','admin','admin','IBM_Switch','7.49'],
['rack_switch','a','loc','Not_mentioned', 'Not_mentioned','192.168.93.83','admin','admin','IBM_Switch','7.45']]
'''
def verify_version(paras,list1):
    k=[]
    k.append(paras['label'])
    k.append(paras['ipv4_address'])
    k.append(paras['version'])
    if list1[0]==k[0]:
        if list1[1]== k[1]:
            if list1[2]==k[2]:
                print("the version is validated")
            else:
                print("version not validated")
        else:
            print("ipv4_adress not matching")
    else:
        print("label not matching")

"""convert the table data as a below form  """
i=0
list1=[]
while i<len(data):
	list1.append(data[i][0])
	list1.append(data[i][6])
	list1.append(data[i][7])
	print(list1)
	verify_version(paras,list1)
	list1=[]
	print(list1)
	i+=1
        

'''
    k=[]
    k.append(paras[KEY_LABEL])
    k.append(paras[KEY_IP])
    k.append(paras[KEY_VERSION])
    print ("The value of K before the condition", +k)
    if k[0]==list1[1]:
        if k[1]==list1[1]):
            if(k[2] != list1[2]):
                print ("The version of K is ", k)
                logger.error("Version is not matched" + paras[KEY_VERSION])
                return 1
            return 0
            
    @convert nested list to required form
    data=[]
    
    

'''
