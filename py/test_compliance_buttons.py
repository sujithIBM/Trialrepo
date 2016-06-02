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
'''
source1='C:\\Users\\IBM_ADMIN\\workspace\\cimgr_trunk_workspace\\Test_SJ\\FVT_aug_4th\\devices_Switch.yml'#the set of devices the devices_Switch.yml file
source2='C:\\Users\\IBM_ADMIN\\workspace\\cimgr_trunk_workspace\\Test_SJ\\FVT_aug_4th\\devices_CIM_VIOS_Virt.yml'#the set of devices devices_CIM_VIOS_Virt.yml file
source3='C:\\Users\\IBM_ADMIN\\workspace\\cimgr_trunk_workspace\\Test_SJ\\FVT_aug_4th\\devices_Other.yml'#the set of devices devices_Other file
source4='C:\\Users\\IBM_ADMIN\\workspace\\cimgr_trunk_workspace\\Test_SJ\\FVT_aug_4th\\devices_SVC.yml'#the set of devices devices_SVC.yml file

sh_file_one='C:\\Users\\IBM_ADMIN\\workspace\\cimgr_trunk_workspace\\Test_SJ\\FVT_aug_4th\\Switches.sh'#shell script to add devices in source1
sh_file_two='C:\\Users\\IBM_ADMIN\\workspace\\cimgr_trunk_workspace\\Test_SJ\\FVT_aug_4th\\CIM_VIOS_Virt.sh'#shell script to add devices in source2
sh_file_three='C:\\Users\\IBM_ADMIN\\workspace\\cimgr_trunk_workspace\\Test_SJ\\FVT_aug_4th\\Other.sh'#shell script to add devices in source3
sh_file_four='C:\\Users\\IBM_ADMIN\\workspace\\cimgr_trunk_workspace\\Test_SJ\\FVT_aug_4th\\SVC.sh'#shell script to add devices in source4

actual_path='C:\\Users\\IBM_ADMIN\\workspace\\cimgr_trunk_workspace\\Test_SJ\\FVT_aug_4th\\devices.yml'# the existing original devices.yml file
false_json_file='C:\\Python34\\false_stack_definitions.json'#the stack_definitions file that is to be copied
destination=actual_path
device_label=['Mellanox1','VIOS1','service4']#device labels that are removed from the stackdefinitions.json file
'''

if not os.path.exists('logs'):
    os.makedirs('logs')

logfile = 'logs' + os.sep + ((__file__.upper())[(__file__.rfind(os.sep)+1):]).replace('.PY', '.log')
logging.basicConfig(format= '%(asctime)-12s [%(filename)-10s] %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S', filename=logfile, filemode='w', level=logging.INFO)
logger = logging.getLogger(__name__)
print('#############################################################')
print('You can see log for detail: ' + logfile)
print('#############################################################')

tests=testing_pages()
testmethod=testing_methods()
data=[]
count=2
class validation(unittest.TestCase):
    def check_value(self,rc):
        global logger
        try:
            self.assertEqual(0,rc)
            logger.info('Assertion TRUE')
        except Exception as e:
            logger.error('Exception: %s', e)

validate=validation()

DRIVER = None

if DRIVER is None:
    logger.info('Setting up FireFox')
    profile = webdriver.FirefoxProfile()
    profile.set_preference("webdriver_accept_untrusted_certs", True)
    profile.set_preference("webdriver_assume_untrusted_issuer", False)
    DRIVER= webdriver.Firefox(profile)

logger.info('Opening PPIM')
print('Opening PPIM')
tests.open_ppim(DRIVER)
time.sleep(5)#wait for page to load
dlabel=0

def copy_stackdefinitions(false_json_file):
    try:
        logger.info('Copying Stackdefinitions file to Rack')
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

def check_device_support():
    try:
        for i in range(len(data)-1):
            count=1
            for j in range(len(device_label)-1):
                if data[i][0]==device_label[j]:
                    if data[i][len(data[i])-1]!='Not Supported':
                        count=0
                        logger.info('SUCCESS: Stack Definitions File Rewritten')
                        print('SUCCESS: Stack Definitions File Rewritten')
                        return 0
                    else:
                        count=0
                        logger.info('FAILED: stack definitions not rewritten. Device still not supported')
                        print('FAILED: stack definitions not rewritten. Device still not supported')
                        return 0
        if count==1:
            logger.info('FAILED: ERROR: Device not found in grid to check supportability')
            return 0
    except Exception as e:
        print(e)
        logger.info('Exception: %s', e)
        return 1

def call_comparison_method():
    try:
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
            else:
                logger.info('ERROR: Access Compliance Version is Invalid')
        return 0
    except Exception as e:
        logger.info('FAILED: To Compare the grid data')
        logger.error('Exception: %s', e)
        return 1

def recommendations_button_check():
    try:
        version_number=DRIVER.find_element_by_css_selector('#widget_dijit_form_FilteringSelect_0 > div.dijitReset.dijitInputField.dijitInputContainer > input[type="hidden"]:nth-child(3)').get_attribute('value')
        print('Version is ' + str(version_number))
        logger.info('**************VERSION IS '+version_number+'*************')


        logger.info('*************************CHECKING RECOMMENDATIONS BUTTON***************************')
        logger.info('Clicking on Retrieve Recommendations Button')
        DRIVER.find_element_by_xpath('//*[@id="RetrieveRecomendationOKButton"]').click()
        time.sleep(5)
        
        logger.info('Getting grid data for Recommendations Button')
        data=tests.get_grid(DRIVER)
        
        del data[0]#deleting Add\Edit\Remove
        del data[0]#deleting Column names
        del data[len(data)-1]#deleting Total and Selected sections
        logger.info('Grid Data is :')
        logger.info(data)

        rc=check_device_support()
        if dlabel!=1:
            validate.check_value(rc)

        rc=call_comparison_method()
        validate.check_value(rc)

        try:
            elem=DRIVER.find_element_by_xpath('//*[@data-dojo-attach-point="recomendationLastUpdatedContainer"]')
            new_date=elem.text
        except Exception as e:
            print("FAILED: To Retrieve Date")
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

def add_devices(source_sh_file):
    try:
        logger.info('Adding Devices')
        logger.info('Starting SSH')
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect('9.3.46.208', username='root', password='PASSW0RD')

        logger.info('SUCCESS: connection established')
        ftp = client.open_sftp()
        ftp.put(source_sh_file,'/root/add_multiple_devices_script.sh')
        logger.info("SUCCESS: transferred shell script to add devices.")

        stdin, stdout, stderr = client.exec_command('sh add_multiple_devices_script.sh')#command goes here
        logger.info("stderr: "+str(stderr.readlines()))
        logger.info("pwd: "+str(stdout.readlines()))
        exit_status = stdout.channel.recv_exit_status()
        if exit_status == 0:
            logger.info("SUCCESS: added devices")
        else:
            logger.info("FAILED:"+str(exit_status))

        ftp.remove('/root/add_multiple_devices_script.sh')
        logger.info('SUCCESS: Cleaned up copied files')
        logger.info('Closing ssh')
        client.close()
        return 0
    except Exception as e:
        print("FAILED: To add multiple devices")
        logger.error('Exception: %s', e)
        return 1

def remove_all_devices():
    try:
        logger.info('****************Removing all device start****************')
        logger.info('Trying to connect via ssh')
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect('9.3.46.208', username='root', password='PASSW0RD')
        logger.info('Connected via ssh')
        stdin, stdout, stderr = client.exec_command('remove_device -a')
        exit_status = stdout.channel.recv_exit_status()
        if exit_status == 0:
            print('SUCCESS: Removed all devices')
            logger.info('SUCCESS: Removed all devices')
            time.sleep(10)
        else:
            print("Error removing all devices", exit_status)
            logger.info('Error removing all devices')
            logger.info(exit_status)
        client.close()
        logger.info('Closed ssh')
        logger.info('****************Removing all device end****************')
        return 0
    except Exception as e:
        print("FAILED: To remove all devices")
        logger.info('Exception: %s', e)
        return 1

def retrieve_installed_version_check():
    try:
        print('Opening Compliance page')
        logger.info('Opening Compliance page')
        tests.open_compliance_page(DRIVER,logger)
        DRIVER.refresh()
        time.sleep(5)

        try:
            version_number=DRIVER.find_element_by_css_selector('#dijit_form_FilteringSelect_0').get_attribute('value')
            print('Version is ' + str(version_number))
            logger.info('**************VERSION IS '+version_number+'*************')
        except:
            print('Could not get version')
        logger.info('Clicking on Retrieve Installed version')
        #DRIVER.find_element_by_css_selector('#dijit_form_Button_7').click()
        DRIVER.find_element_by_xpath('//*[@id="RetrieveInstalledVersionOKButton"]').click()
        time.sleep(5)
        #DRIVER.find_element_by_xpath('//*[@id="ConfirmOKButton"]/div[4]/span[2]/span[1]/span').click()
        DRIVER.find_element_by_xpath('//*[@id="dijit_form_Button_3"]').click()
        time.sleep(5)
        '''
        logger.info('Getting grid data')
        data=tests.get_grid(DRIVER)#get table data
        print(data)
        del data[0]#deleting Add\Edit\Remove

        data=tests.column_numbering(data)
        del data[0]#deleting Column names
        del data[len(data)-1]#deleting Total and Selected sections
        logger.info('Grid Data is :')
        logger.info(data)
        
        with open('devices.yml','r') as f :
            paras=yaml.load(f)
            logger.info('The Config file is loaded as: '+str(paras))
            f.close()
        '''
        rc=call_comparison_method()
        validate.check_value(rc)

        rc=recommendations_button_check()
        validate.check_value(rc)

        logger.info('Removing all devices')
        rc=remove_all_devices()
        validate.check_value(rc)
        return 0
    except Exception as e:
        print("FAILED: To check retrieve installed version button")
        logger.info('Exception: %s', e)
        return 1

def overwrite_devicesyml(source,destination):
    try:
        shutil.copy(source,destination)
        logger.info('SUCCESS: devices.yml file overwritten')
    except Exception as e:
        print("FAILED: To overwrite devices.yml")
        logger.error('Exception: %s', e)

shutil.copy(actual_path,'C:\\devices.yml')
rc=remove_all_devices()
validate.check_value(rc)

if not rc:
    for i in range(4):
        try:
            if i==0:
                logger.info('*******************Starting first iteration*******************')
                rc=copy_stackdefinitions(false_json_file)
                validate.check_value(rc)
                overwrite_devicesyml(source1, destination)
                rc=add_devices(sh_file_one)
                validate.check_value(rc)
                if not rc:
                    rc=retrieve_installed_version_check()
                    validate.check_value(rc)
                else:
                    logger.info('FAILED to add devices')
            elif i==1:
                logger.info('*******************Starting second iteration*******************')
                rc=copy_stackdefinitions(false_json_file)
                validate.check_value(rc)
                overwrite_devicesyml(source2, destination)
                rc=add_devices(sh_file_two)
                validate.check_value(rc)
                if not rc:
                    rc=retrieve_installed_version_check()
                    validate.check_value(rc)
                else:
                    logger.info('FAILED to add devices')
            elif i==2:
                logger.info('*******************Starting Third iteration*******************')
                rc=copy_stackdefinitions(false_json_file)
                validate.check_value(rc)
                overwrite_devicesyml(source3, destination)
                rc=add_devices(sh_file_three)
                validate.check_value(rc)
                if not rc:
                    rc=retrieve_installed_version_check()
                    validate.check_value(rc)
                else:
                    logger.info('FAILED to add devices')
            elif i==3:
                logger.info('*******************Starting Fourth iteration*******************')
                rc=copy_stackdefinitions(false_json_file)
                validate.check_value(rc)
                overwrite_devicesyml(source4, destination)
                rc=add_devices(sh_file_four)
                validate.check_value(rc)
                if not rc:
                    dlabel=1
                    rc=retrieve_installed_version_check()
                    validate.check_value(rc)
                else:
                    logger.info('FAILED to add devices')
            else:
                logger.info('END OF ITERATIONS')
        except Exception as e:
            print("FAILED: To check all devices")
            logger.info('Exception: %s', e)
else:
    logger.info('ERROR Removing all devices before start. Exiting now.')
    exit()

print('Cleaning up')
shutil.copy('C:\\devices.yml',actual_path)
logger.info('SUCCESS: Cleaned up data')
print('Closing')
logger.info('Closing')

DRIVER.close()
