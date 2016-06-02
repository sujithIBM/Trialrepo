from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import time
import yaml


#DRIVER = webdriver.Chrome()
DRIVER = None
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
        d.find_element_by_name("pwd").send_keys('xxxxxxxxxx')
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
d.find_element_by_xpath('//img[contains(@src,"imagebar-ppimCompliance.png")]').click()
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


'''data=[['Retrieve Installed version\nRetrieve Recommendations', 'Filter'],
      ['Label', 'Type', 'IP Address', 'Installed Version', 'Base Version', 'Recommended Version', 'Compliance Status'],
      ['Mellanox1', 'Mellanox Switch', '192.168.93.37', '3.4.1120', '3.4.1120', '3.4.1120', 'Compliant'],
      ['SANswitch', 'Brocade SAN Switch', '192.168.93.9', 'v7.3.0c', 'v7.3.0c', 'v7.3.0c', 'Compliant'],
      ['V7K4', 'V7000', '192.168.93.8', '7.4.0.5', '7.4.0.2', '7.4.0.2', 'Not Compliant'],
      ['VIOS1', 'Virtual I/O Server', '192.168.93.89', '2.2.3.52', '2.2.3.52', '2.2.3.52', 'Compliant'],
      ['hmc4', 'Hardware Management Console', '9.3.46.190', '8.4.1', 'V8 R830', 'V8 R830 SP1', 'Not Compliant'],
      ['Integrated Management Module', '9.3.46.189', '4.56', '4.56', '4.56', 'Compliant'],
      ['Total: 12 Selected: 0']]

'''

del data[0]


headings=data[0]
del data[0]
del data[len(data)-1]
numbering=[0,1,2,3,4,5,6]
for i in range(len(headings)):
    numbering[i] = i
    if headings[i]=='Label':
        Label=i
        print(str(i)+" is Label")
    elif headings[i]=='IP Address':
        IP=i
        print(str(i)+" is IP Address")
    elif headings[i]=='Installed Version':
        Installedversion=i
        print(str(i)+" is Version")
    elif headings[i]=='Base Version':
        BaseVersion=i
        print(str(i)+" is BaseVersion")
    elif headings[i]=='Recommended Version':
        RecomendedVersion=i
        print(str(i)+" is RecomendedVersion")   
    elif headings[i]=='Compliance Status':
        Compliancestatus=i
        print(str(i)+" is Compliance status")
else:
    print("ZERO Devices Found. Exiting now.")
    print(data)


def Compliance_validate(self,data,paras):
        print("******************VERSION VALIDATION STARTS******************")
        paras=paras
        i=0
        list2=[]
        global Label
        global IP
        global version
        while i<len(data):
            print("Test " + str(i+1))
            list2.append(data[i][Label])
            list2.append(data[i][IP])
            list2.append(data[i][Installedversion])
            list2.append(data[i][BaseVersion])
            list2.append(data[i][RecomendedVersion])
            list2.append(data[i][Compliancestatus])
            self.verify_label(paras,list1)
            list2=[]
            i+=1
        print("******************VERSION VALIDATION ENDS******************")

## verifying label

def getFromDict(self,paras, mapList):
        return reduce(lambda d, k: d[k], mapList, paras)

def verify_label(self,parase,list1):
    paras_list=list(parase)
    for i in range(len(paras_list)):
        Device=paras_list[i]
        if Device == 'Puremgr' or Device == 'Nagiosmgr':
            #print("Skipping due to incomplete data in config file")
            continue
        DevName=Device
        Device=self.getFromDict(parase,[Device])
        Device_no=self.getFromDict(Device, ["Device_01"])
        InitSetting=self.getFromDict(Device_no,["InitSetting"])
        InitSetting=InitSetting[0]
        self.verify_status(InitSetting,list2,DevName)



def verify_status(self,parase,list2,Device):
        k=[]
        global paras
        paras=parase
        self.Device=Device
        k.append(paras['label'])
        k.append(paras['ipv4_address'])
        k.append(paras['version'])
        if list1[0]==k[0]:
            if list2[1]== k[1]:
                if list2[2]==k[2]:
                    if list2[3]==list2[4] or list2[3] == list2[5]:
                        check=''
                        check=list2[6]
                        print(check)
                        if check == 'Compliant':
                            print("staus is Compliant for "+data[0][0])
                        else:
                            print("not compliant")		
                    else:
                        print("Failed: Installed Version is not matching " + str(list2[0]))
