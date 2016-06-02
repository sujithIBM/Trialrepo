from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import time

DRIVER = None

if DRIVER is None:
    profile = webdriver.FirefoxProfile()
    profile.set_preference("webdriver_accept_untrusted_certs", True)
    profile.set_preference("webdriver_assume_untrusted_issuer", False)
    DRIVER = webdriver.Firefox(profile)

d = DRIVER

#open login page
d.get("https://9.3.46.208/ppim/login.html")
time.sleep(2)#wait to complete load

# Add security exception
if d.title == "Untrusted Connection":
    try:
        d.click("exceptionDialogButton")
        time.sleep(2)
        print("SUCCESS: Security Exception Added")
    except Exception as e:
        print(e)
        print("Exception: Unable to add Security Exception")

# Check if BSO Authentication page
if d.title == "Authentication Proxy Login Page":
    try:
        d.find_element_by_name("uname").clear()
        d.find_element_by_name("uname").send_keys('stanjude@in.ibm.com')
        d.find_element_by_name("pwd").clear()
        d.find_element_by_name("pwd").send_keys('xxxxxxxx')
        d.find_element_by_name("ok").click()
        time.sleep(2)
        print("SUCCESS: BSO Authentication")
    except Exception as e:
        print(e)
        print("Exception: BSO Authentication Failed")

if d.title == "IBM PurePower Manager | Login":
    try:
        username=d.find_element_by_name('username')
        username.send_keys("root")
        password=d.find_element_by_name('password')
        password.send_keys("passw0rd")
        password.send_keys(Keys.ENTER)
        time.sleep(3)#wait to complete load
        print("SUCCESS: Logged into PPIM")
    except Exception as e:
        print(e)
        print("PPIM Login Failed")

time.sleep(10)
#click on Hardware Inventory
d.find_element_by_xpath('//img[contains(@src,"imagebar-ppimInventory.png")]').click()
time.sleep(2)
print("SUCCESS: Opened Hardware Inventory")

data=[]
rowslist=[]

#find all visible rows
rowslist = d.find_elements_by_xpath('//div[@class="gridxMain"]/div/div/table/tbody')
for table in rowslist:
    data_row=[]
    tds=table.find_elements_by_tag_name('td')
    if tds:
        for td in tds:
            row_data=td.text
            if row_data!= '':
                data_row.append(row_data)
        if data_row!= []:
            data.append(data_row)

print(data)


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




d.close()
