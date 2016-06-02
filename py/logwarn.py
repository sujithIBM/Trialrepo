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
"""convert the table data as a below form  """
list1=['rack_switch','192.168.93.83','7.45']

def verify_version(paras,list1):
    k=[]
    k.append(paras['label'])
    k.append(paras['ipv4_address'])
    k.append(paras['version'])
    if list1[0]==k[0]:
        if list1[1]== k[1]:
            if list1[2]==k[2]:
                print("the version is validated")

verify_version(paras,list1)

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
