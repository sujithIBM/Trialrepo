from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from functools import reduce
import os
import time
import yaml
import logging
import paramiko
from selenium.webdriver.support.wait import WebDriverWait

no_of_rows=0
Label=0
IP=0
version=0
base_version=0
recommended_version=0
class testing_pages:
    def __init__(self):
        self

    def open_ppim(self,driver):
        self.d=driver
        if self.d is None:
            profile = webdriver.FirefoxProfile()
            profile.set_preference("webdriver_accept_untrusted_certs", True)
            profile.set_preference("webdriver_assume_untrusted_issuer", False)
            self.d = webdriver.Firefox(profile)

        #open login page
        self.d.get("https://9.3.46.208/puremgr/HomePage.xhtml")
        time.sleep(2)#wait to complete load

        # Add security exception
        if self.d.title == "Untrusted Connection":
            try:
                self.d.click("exceptionDialogButton")
                time.sleep(2)
                print("SUCCESS: Security Exception Added")
            except Exception as e:
                print(e)
                print("Exception: Unable to add Security Exception")

        # Check if BSO Authentication page
        if self.d.title == "Authentication Proxy Login Page":
            try:
                self.d.find_element_by_name("uname").clear()
                self.d.find_element_by_name("uname").send_keys('stanjude@in.ibm.com')
                self.d.find_element_by_name("pwd").clear()
                self.d.find_element_by_name("pwd").send_keys('xxxxxxxxxx')
                self.d.find_element_by_name("ok").click()
                time.sleep(2)
                print("SUCCESS: BSO Authentication")
            except Exception as e:
                print(e)
                print("Exception: BSO Authentication Failed")

        time.sleep(5)
        if self.d.title == "IBM PurePower Manager | Login":
            try:
                username=self.d.find_element_by_name("username")
                username.send_keys("root")
                password=self.d.find_element_by_name("password")
                password.send_keys("passw0rd")
                password.send_keys(Keys.ENTER)
                time.sleep(3)#wait to complete load
                print("SUCCESS: Logged into PPIM")
            except Exception as e:
                print(e)
                print("PPIM Login Failed")
        time.sleep(5)


    #click on Hardware Inventory
    def open_hardware_inventory(self,driver):
        driver.find_element_by_xpath('//img[contains(@src,"puremgr/images/imagebar-ppimInventory.png")]').click()
        time.sleep(2)
        print("SUCCESS: Opened Hardware Inventory")

    def open_compliance_page(self,driver,logger):
        try:
            driver.find_element_by_xpath('//img[contains(@src,"puremgr/images/imagebar-ppimCompliance.png")]').click()
            time.sleep(2)
            print("SUCCESS: Opened Compliance Page")
            return 0
        except Exception as e:
            print('Exception while opening Compliance Page: ' + str(e))
            logger.error('%s',e)
            return 1

    def compliance_version(self,d,ver,logger):
        try:
            self.d=d
            print("Access compliance for pure version"+ver)
            logger.info("Accessing PurePower Version for "+ver)
            self.d.find_element_by_xpath('//*[@id="dijit_form_FilteringSelect_0"]').click()
            self.d.find_element_by_xpath('//*[@id="dijit_form_FilteringSelect_0"]').clear()
            self.d.find_element_by_xpath('//*[@id="dijit_form_FilteringSelect_0"]').send_keys(ver)
            self.d.find_element_by_xpath('//*[@id="dijit_form_FilteringSelect_0"]').send_keys(Keys.ENTER)
            self.getdata(d,logger)
            return 0
        except Exception as e:
            logger.error('Exception %s',e)
            return 1

    def add_devices(self,source_sh_file,filename,logger):
        try:
            logger.info('Starting SSH')
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.client.connect('9.3.46.208', username='root', password='PASSW0RD')

            logger.info('SUCCESS: connection established')
            ftp = self.client.open_sftp()
            ftp.put(source_sh_file,'/root/'+filename)
            logger.info("SUCCESS: transferred shell script to add devices.")

            stdin, stdout, stderr = self.client.exec_command('sh '+filename)#command goes here
            logger.info("stderr: "+str(stderr.readlines()))
            logger.info("pwd: "+str(stdout.readlines()))
            exit_status = stdout.channel.recv_exit_status()
            if exit_status == 0:
                logger.info("SUCCESS added devices")
            else:
                logger.info("Failed"+str(exit_status))

            ftp.remove('/root/'+filename)
            logger.info('SUCCESS: Cleaned up copied files')
            logger.info('Closing ssh')
            self.client.close()
            return 0
        except Exception as e:
            print("FAILED: To add multiple devices")
            logger.error('Exception: %s', e)
            return 1


    def get_grid(self,driver):
        self.rowslist=[]
        d=driver
        global no_of_rows
        self.data=[]
        #rowslist = d.find_elements_by_xpath('//div[@class="gridxMain"]')
        #rowslist = d.find_elements_by_xpath('//div[@data-dojo-attach-point="mainNode"]/div/div/table')
        self.rowslist = d.find_elements_by_xpath('.//table')
        #rowslist = d.find_elements_by_xpath('//div[@class="gridxMain"]/div/div/table/tbody')
        for table in self.rowslist:
            self.data_row=[]
            self.tds=table.find_elements_by_tag_name('td')
            if self.tds:
                for td in self.tds:
                    self.row_data=td.text
                    if self.row_data!= '':
                        self.data_row.append(self.row_data)
                if self.data_row!= []:
                    self.data.append(self.data_row)
                    no_of_rows+=1
        return self.data

    def column_numbering(self,obtained_data):
        global no_of_rows
        self.obtained_data=obtained_data
        if self.obtained_data:
            self.data=[]
            self.data=self.obtained_data
            self.columns=[]
            global Label
            global IP
            global version
            global base_version
            global recommended_version

            print("******************Column Numbering******************")
            self.headings=self.data[0]
            del self.data[0]
            self.numbering=[0,1,2,3,4,5,6,7]
            for i in range(len(self.headings)):
                self.numbering[i] = i
                if self.headings[i]=='Label':
                    Label=i
                    print(str(i)+" is Label")
                elif self.headings[i]=='IP Address':
                    IP=i
                    print(str(i)+" is IP Address")
                elif self.headings[i]=='Installed Version':
                    version=i
                    print(str(i)+" is Installed Version")
                elif self.headings[i]=='Base Version':
                    base_version=i
                    print(str(i)+" is Base Version")
                elif self.headings[i]=='Recommended Version':
                    recommended_version=i
                    print(str(i)+" is Recommended Version")
        else:
            print("ZERO Devices Found. Exiting now.")
        return self.data


    def getFromDict(self,paras, mapList):
        return reduce(lambda d, k: d[k], mapList, paras)

    def verify_label(self,parase,list1,logger):
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
            self.verify_version(InitSetting,list1,DevName,logger)


    def verify_version(self,parase,list1,Device,logger):
        k=[]
        paras=parase
        self.Device=Device
        k.append(paras['label'])
        k.append(paras['ipv4_address'])
        k.append(paras['Installed Version'])
        if list1[0]==k[0]:
            if list1[1]== k[1]:
                if list1[2]==str(k[2]):
                    print("SUCCESS: Version Validated with " + str(Device) + " for " + str(list1[0]))
                    logger.info("SUCCESS: Version Validated with " + str(Device) + " for " + str(list1[0]))
                else:
                    print("FAILED: Version not validated for "+ str(list1[0]))
                    logger.info("FAILED: Version not validated for "+ str(list1[0]))
            else:
                print("Failed: IPv4_Address not matching for " + str(list1[0]))
                logger.info("Failed: IPv4_Address not matching for " + str(list1[0]))
        #else:
            #print("Failed: Label not matching for " + str(list1[0]))

    def version_validate(self,data,paras,logger):
        logger.info('**************Version Validation Starts**************')
        print("******************VERSION VALIDATION STARTS******************")
        paras=paras
        i=0
        list1=[]
        global Label
        global IP
        global version
        while i<len(data):
            logger.info('Test' + str(i))
            print("Test " + str(i+1))
            list1.append(data[i][Label])
            list1.append(data[i][IP])
            list1.append(data[i][version])
            self.verify_label(paras,list1,logger)
            list1=[]
            i+=1
        print("******************VERSION VALIDATION ENDS******************")
        logger.info('**************Version Validation Ends**************')
