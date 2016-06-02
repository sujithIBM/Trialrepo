from selenium import webdriver
from test_common_version_check import testing_pages
from test_gui_compliance_methods import testing_methods

import paramiko
import logging
import os
import time
import unittest
import yaml
import shutil

'''source1='C:\\Users\\IBM_ADMIN\\workspace\\cimgr_trunk_workspace\\Test_SJ\\FVT_aug_4th\\devices_Switch.yml'#the set of devices the devices_Switch.yml file
source2='C:\\Users\\IBM_ADMIN\\workspace\\cimgr_trunk_workspace\\Test_SJ\\FVT_aug_4th\\devices_CIM_VIOS_Virt.yml'#the set of devices devices_CIM_VIOS_Virt.yml file


sh_file_one='C:\\Users\\IBM_ADMIN\\workspace\\cimgr_trunk_workspace\\Test_SJ\\FVT_aug_4th\\Switches.sh'#shell script to add devices in source1
sh_file_two='C:\\Users\\IBM_ADMIN\\workspace\\cimgr_trunk_workspace\\Test_SJ\\FVT_aug_4th\\CIM_VIOS_Virt.sh'#shell script to add devices in source2
actual_path='C:\\Users\\IBM_ADMIN\\workspace\\cimgr_trunk_workspace\\Test_SJ\\FVT_aug_4th\\devices.yml'# the existing original devices.yml file
destination=actual_path
'''
false_json_file='C:\\Python34\\false_stack_definitions.json'#the stack_definitions file that is to be copied
add_device_cmd='add_device -l Mellanox1 --rackid a --rack-location loc -u admin -p admin 192.168.93.37'
device_label='Mellanox-1'

if not os.path.exists('logs'):
    os.makedirs('logs')

logfile = 'logs' + os.sep + ((__file__.upper())[(__file__.rfind(os.sep)+1):]).replace('.PY', '.log')
logging.basicConfig(format= '%(asctime)-12s [%(filename)-10s] %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S', filename=logfile, filemode='w', level=logging.INFO)
logger = logging.getLogger(__name__)
print('#####################################################')
print('You can see log for detail: ' + logfile)
print('#####################################################')

tests=testing_pages()
testmethod=testing_methods()

DRIVER = webdriver.Chrome()

class validation(unittest.TestCase):
    def check_value(self,rc):
        global logger
        try:
            self.assertEqual(0,rc)
            logger.info('Assertion TRUE')
        except Exception as e:
            logger.error('Exception: %s', e)

validate=validation()

def add_devices(source_sh_file):
    try:
        logger.info('Starting SSH')
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect('9.3.46.208', username='root', password='PASSW0RD')

        logger.info('SUCCESS: connection established')

        stdin, stdout, stderr = client.exec_command(add_device_cmd)#command goes here
        logger.info("stderr: "+str(stderr.readlines()))
        logger.info("pwd: "+str(stdout.readlines()))
        exit_status = stdout.channel.recv_exit_status()
        if exit_status == 0:
            logger.info("SUCCESS added device")
        else:
            logger.info("Failed"+str(exit_status))

        logger.info('Closing ssh')
        client.close()
        return 0
    except Exception as e:
        print("FAILED: To add Mellanox device")
        logger.error('Exception: %s', e)
        return 1

def copy_stackdefinitions(false_json_file):
    try:
        logger.info('Starting SSH')
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect('9.3.46.208', username='root', password='PASSW0RD')
        logger.info('SUCCESS: connection established')

        ftp = client.open_sftp()

        ftp.put(false_json_file,'/opt/ibm/puremgr/etc/stack_definitions.json')
        logger.info("SUCCESS: transferred False Stack Definitions script")

        logger.info('Closing ssh')
        ftp.close()
        client.close()
        return 0
    except Exception as e:
        print("FAILED: To add stack_definitions.json file")
        logger.info('FAILED: To add stack_definitions.json file')
        logger.error('Exception: %s', e)
        return 1

def recommendations_button_check():
    try:
        print('Opening Compliance page')
        logger.info('Opening Compliance page')
        tests.open_compliance_page(DRIVER)
        DRIVER.refresh()
        time.sleep(5)

        version_number=DRIVER.find_element_by_css_selector('#widget_dijit_form_FilteringSelect_0 > div.dijitReset.dijitInputField.dijitInputContainer > input[type="hidden"]:nth-child(3)').get_attribute('value')
        print('Version is ' + str(version_number))
        logger.info('**************VERSION IS '+version_number+'*************')


        logger.info('*************************CHECKING RECOMMENDATIONS BUTTON***************************')
        logger.info('Clicking on Retrieve Installed version')
        DRIVER.find_element_by_xpath('//*[@id="RetrieveRecomendationOKButton"]').click()
        time.sleep(20)

        logger.info('Getting grid data for Recommendations Button')
        data=tests.get_grid(DRIVER)#get table data
        print(data)
        del data[0]#deleting Add\Edit\Remove
        del data[0]#deleting Column names
        del data[len(data)-1]#deleting Total and Selected sections
        logger.info('Grid Data is :')
        logger.info(data)
        print(data)

        try:
            for i in range(len(data)-1):
                count=1
                if data[i][0]==device_label:
                    if data[i][len(data[i])-1]!='Not Supported':
                        count=0
                        logger.info('SUCCESS: Stack Definitions File Rewritten')
                        print('SUCCESS: Stack Definitions File Rewritten')
                        break
                    else:
                        logger.info('FAILED: stack definitions not rewritten. Device still not supported')
                        print('FAILED: stack definitions not rewritten. Device still not supported')
            if count==1:
                logger.info('FAILED: ERROR: Device not found in grid')
        except Exception as e:
            print(e)
            logger.info('Exception: %s', e)

        #sujith's method to compare version called here
        logger.info('Calling Comparison methods')
        for i in range(3):
            if i==0:
                rc=testmethod.compliance_ver(DRIVER,'1.2.0',logger)
                validate.check_value(rc)
            elif i==1:
                rc=testmethod.compliance_ver(DRIVER,'1.2.1',logger)
                validate.check_value(rc)
            elif i==2:
                rc=testmethod.compliance_ver(DRIVER,'1.3.0',logger)
                validate.check_value(rc)


        try:
            elem=DRIVER.find_element_by_xpath('//*[@data-dojo-attach-point="recomendationLastUpdatedContainer"]')
            new_date=elem.text
        except Exception as e:
            print("FAILED: To Retirve Date")
            logger.info('Exception: %s', e)

        logger.info('Getting System date---Starting SSH')
        clientone = paramiko.SSHClient()
        clientone.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        clientone.connect('9.3.46.208', username='root', password='PASSW0RD')
        print('SUCCESS: connection established')
        stdin, stdout, stderr = clientone.exec_command('date +%Y-%m-%d')#command goes here
        logger.info("stderr: "+str(stderr.readlines()))
        date_retrieved=stdout.readlines()
        date_retrieved=date_retrieved[0]

        logger.info('SYSTEM DATE IS :'+str(date_retrieved))
        exit_status = stdout.channel.recv_exit_status()

        if exit_status == 0:
            logger.info("SUCCESS Retrieved System Date")
        else:
            logger.info("Failed"+str(exit_status))
        clientone.close()

        new_date=new_date+'\n'

        if str(new_date) == str(date_retrieved):
            logger.info('SUCCESS: Date is updated and matching')
        else:
            logger.info('FAILED: Date not matching')

        return 0
    except Exception as e:
        print("FAILED: To check Recommended version button")
        logger.info('Exception: %s', e)
        return 1

rc=copy_stackdefinitions(false_json_file)
validate.check_value(rc)

try:
    logger.info('Opening PPIM')
    print('Opening PPIM')
    tests.open_ppim(DRIVER)
    logger.info('SUCCESS: Opened PPIM')
    time.sleep(5)#wait for page to load
except Exception as e:
    print("FAILED: To open PPIM")
    logger.error('Exception: %s', e)

try:
    logger.info('Opening Compliance Page')
    rc=tests.open_compliance_page(DRIVER)
    validate.check_value(rc)
    time.sleep(2)
    print("SUCCESS: Opened Compliance Page")
    logger.info('SUCCESS: Compliance page opened')
except Exception as e:
    print("FAILED: To open Compliance Page")
    logger.error('Exception: %s', e)

version_number=DRIVER.find_element_by_css_selector('#widget_dijit_form_FilteringSelect_0 > div.dijitReset.dijitInputField.dijitInputContainer > input[type="hidden"]:nth-child(3)').get_attribute('value')
print('Version is ' + str(version_number))
logger.info('**************VERSION IS '+version_number+'*************')
logger.info('Clicking on Retrieve Installed version')

DRIVER.find_element_by_xpath('//*[@id="RetrieveInstalledVersionOKButton"]').click()
time.sleep(5)
DRIVER.find_element_by_xpath('//*[@id="ConfirmOKButton"]/div[4]/span[2]/span[1]/span').click()
time.sleep(5)

logger.info('Getting grid data')
data=tests.get_grid(DRIVER)#get table data
print(data)
del data[0]#deleting Add\Edit\Remove
del data[0]#deleting Column names
del data[len(data)-1]#deleting Total and Selected sections
logger.info('Grid Data is :')
logger.info(data)
print(data)

try:
    for i in range(len(data)-1):
        count=1
        if data[i][0]==device_label:
            if data[i][len(data[i])-1]=='Not Supported Device Type':
                count=0
                logger.info('SUCCESS: NOT SUPPORTED FOR ADDED DEVICE')
                print('SUCCESS: Added Device is not supported')
                break
            else:
                logger.info('FAILED: stack definitions not read. Added Device is still supported')
                print('FAILED: Added Device still supported')
    if count==1:
        logger.info('FAILED: Added Device not found in grid')
except Exception as e:
    print(e)
    logger.info('Exception: %s', e)

rc=recommendations_button_check()
validate.check_value(rc)

print('Closing')
logger.info('Closing')

DRIVER.close()
