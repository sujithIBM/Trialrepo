from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from get_configuration import get_config
import time
import yaml

DRIVER = webdriver.Chrome()
#DRIVER = None
#DRIVER = webdriver.Ie()

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

#rowslist = d.find_elements_by_xpath('//div[@class="gridxMain"]')
rowslist = d.find_elements_by_xpath('.//table')
#rowslist = d.find_elements_by_xpath('//div[@class="gridxMain"]/div/div/table/tbody')
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

print("******************RAW DATA******************")
print(data)

del data[0]#deleting Add Edit Remove Configure Network data
del data[len(data)-1]#deleting Total:xx Selected: xx row


print("******************Column Numbering******************")
headings=data[0]
del data[0]
numbering=[0,1,2,3,4,5,6,7]
for i in range(len(headings)):
    numbering[i] = i
    if headings[i]=='Label':
        Label=i
        print(str(i)+" is Label")
    elif headings[i]== 'Type':
        Type=i
        print(str(i)+" is Type")
    elif headings[i]=='IP Address':
        IP=i
        print(str(i)+" is IP Address")
    elif headings[i]=='Version':
        version=7
        print(str(i)+" is Version")
version=7#to delete when version is available in GUI
print("7 is Version")#to delete when version is available in GUI

columns=[]
for i in range(0,7):
    col_data=data[i][0]
    columns.append(col_data)
print("Column is " + str(columns))

print("******************ACTUAL GRID DATA******************")
for i in range(len(data)):
    print(data[i])


with open('devices.yaml','r') as f :
    doc=yaml.load(f)
    paras = doc[data[0][0]]
print(paras)
#Sample Data

def verify_version(paras,list1):
    k=[]
    k.append(paras['label'])
    k.append(paras['ipv4_address'])
    k.append(paras['version'])
    if list1[0]==k[0]:
        if list1[1]== k[1]:
            if list1[2]==k[2]:
                print("SUCCESS: Version Validated")
            else:
                print("FAILED: Version not validated")
        else:
            print("Failed: IPv4_Address not matching")
    else:
        print("Failed: Label not matching")

"""convert the table data as a below form  """
print("******************VERSION VALIDATION STARTS******************")
i=0
list1=[]
while i<len(data):
    print("Test " + str(i+1))
    list1.append(data[i][Label])
    list1.append(data[i][IP])
    list1.append(data[i][7])
    verify_version(paras,list1)
    list1=[]
    i+=1
print("******************VERSION VALIDATION ENDS******************")

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
