'''
Created on Oct 14, 2015

@author: sujith

prereq: resolv.conf must be placed in C:\Python34\resolv.conf
dependent on another script test_gui_validate_access_comp_methods.py
'''
from selenium import webdriver
from test_common_methods_check import testing_pages
import logging
import os.path
import time
import unittest
#import json
#from test.test_importlib.extension.util import FILEPATH
#import shutil
from test_gui_validate_access_comp_methods import comp_methods

tests=testing_pages()
methods = comp_methods()

online = 'set_compliance_config -c online'
offline ='set_compliance_config -c offline'
resolv = 'C:\\Python34\\resolv.conf'
proxy_validip_validcred = 'set_compliance_config -c proxy -i 9.3.46.208 -u root'
proxy_invalidip_validcred = 'set_compliance_config -c proxy -i 9.3.46.207 -u root'
proxy_validip_invaliduname='set_compliance_config -c proxy -i 9.3.46.208 -u ppima'
proxy_validip_invalidpw='set_compliance_config -c proxy -i 9.3.46.208 -u ppima'
proxy_with_no_python34= 'set_compliance_config -c proxy -i 9.114.205.136 -u root'
proxy_cannot_ping = 'set_compliance_config -c proxy -i 192.168.93.43 -u USERID'
proxy_IMM_Machine ='set_compliance_config -c proxy -i 9.3.46.191 -u USERID'
proxy_v7k = 'set_compliance_config -c proxy -i 192.168.93.8 -u superuser '
proxy_with_no_py34 = 'set_compliance_config -c proxy -i 9.3.46.194 -u root'
msg1 = 'Stack definition file could not be generated in the remote machine\n'
msg2 = 'Could not copy file to remote machine\n'
valid_ip =' 9.3.46.208'
valid_un = 'root'
invalid_ip ='9.3.46.207'
invalid_un='ppima'
valid_pw='PASSW0RD'
invalid_pw = 'wrong'
mode ='proxy'
run = 'cat /opt/ibm/puremgr/etc/updates_compliance.properties'
resolv = 'C:\\Python34\\resolv.conf'

if not os.path.exists('logs'):
    os.makedirs('logs')

logfile = 'logs' + os.sep + ((__file__.upper())[(__file__.rfind(os.sep)+1):]).replace('.PY', '.log')
logging.basicConfig(format= '%(asctime)-12s [%(filename)-10s] %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S', filename=logfile, filemode='w', level=logging.INFO)
logger = logging.getLogger(__name__)

print('#####################################################')
print('You can see log for detail: ' + logfile)
print('#####################################################')



class test_Accesscompliance(unittest.TestCase):
    def test01_online_validate(self):
        try:
            rc=methods.set_comp_online(logger, online)
            self.assertEqual(0, rc)
            print("success set mode into online")
            rc=methods.Replace_resolv(resolv, logger)
            self.assertEqual(0, rc)
            print("success removed the name server, to check whether the ppim can connect to Flrt or not")
            DRIVER = webdriver.Chrome()
            print("opening PPIM")
            rc=tests.open_ppim(DRIVER, logger)
            self.assertEqual(0, rc)
            print("Success : opened PPIM")
            try:
                print("comparing the time stamps to check if they are updated")
                old_time=methods.get_stack_file_time(logger)
                print("the old time is :"+old_time)
                rc=methods.click_retrv_recmnd_button1(logger, DRIVER)
                self.assertEqual(0, rc)
                print("clicked on Retrieve Recomenditions button")
                #call the timestamp of updated file
                updated_time=methods.get_stack_file_time(logger)
                print("updated_time is: "+updated_time)
                self.assertEqual(updated_time, old_time)
                print("validated the test, ppim couldnt connect the flrt ::online case \n\n ")
            except Exception as e:
                logger.error('Exception: %s', e)
        except:
            logger.error('Exception: %s', e)

        finally:
            DRIVER.close()


    def test02_proxy_validate(self):
        try:
            rc=methods.set_comp_proxy_validip_val_cred(logger, proxy_validip_validcred, valid_ip, valid_un)
            self.assertEqual(0, rc)
            print("success set mode into proxy mode")
            rc=methods.Replace_resolv(resolv, logger)
            self.assertEqual(0, rc)
            print("success removed the name server, to check whether the ppim can connect to Flrt or not")
            DRIVER = webdriver.Chrome()
            print("opening PPIM")
            rc=tests.open_ppim(DRIVER, logger)
            self.assertEqual(0, rc)
            print("Success : opened PPIM")
            try:
                print("comparing the time stamps to check if they are updated")
                old_time=methods.get_stack_file_time(logger)
                print("the old time is :"+old_time)
                rc=methods.click_retrv_recmnd_button1(logger, DRIVER)
                self.assertEqual(0, rc)
                print("clicked on Retrieve Recomenditions button")
                #call the timestamp of updated file
                updated_time=methods.get_stack_file_time(logger)
                print("updated_time is: "+updated_time)
                self.assertEqual(updated_time, old_time)
                print("validated the test, ppim couldnt connect the flrt :: proxy case \n\n ")
            except Exception as e:
                logger.error('Exception: %s', e)
        except:
            logger.error('Exception: %s', e)

        finally:
            DRIVER.close()

    def test03_offline_validate(self):
        try:
            rc=methods.set_comp_offline(logger, offline)
            self.assertEqual(0, rc)
            print("success set mode into offline")
            rc=methods.Replace_resolv(resolv, logger)
            self.assertEqual(0, rc)
            print("success removed the name server, to check whether the ppim can connect to Flrt or not")
            DRIVER = webdriver.Chrome()
            print("opening PPIM")
            rc=tests.open_ppim(DRIVER, logger)
            self.assertEqual(0, rc)
            print("Success : opened PPIM")
            try:
                print("comparing the time stamps to check if they are updated")
                old_time=methods.get_stack_file_time(logger)
                print("the old time is :"+old_time)
                rc=methods.click_retrv_recmnd_button1(logger, DRIVER)
                self.assertEqual(0, rc)
                print("clicked on Retrieve Recomenditions button")
                #call the timestamp of updated file
                updated_time=methods.get_stack_file_time(logger)
                print("updated_time is: "+updated_time)
                self.assertEqual(updated_time, old_time)
                print("validated the test, ppim couldnt connect the flrt :: offline case \n\n ")
            except Exception as e:
                logger.error('Exception: %s', e)
        except:
            logger.error('Exception: %s', e)

        finally:
            DRIVER.close()


    def test04_proxy_wrongip_validate(self):
        try:
            rc=methods.set_comp_proxy_invalidip_val_cred(logger, proxy_invalidip_validcred, invalid_ip,valid_un)
            self.assertEqual(0, rc)
            print("success set mode into proxy mode")
            rc=methods.Replace_resolv(resolv, logger)
            self.assertEqual(0, rc)
            print("success removed the name server, to check whether the ppim can connect to Flrt or not")
            DRIVER = webdriver.Chrome()
            print("opening PPIM")
            rc=tests.open_ppim(DRIVER, logger)
            self.assertEqual(0, rc)
            print("Success : opened PPIM")
            try:
                print("comparing the time stamps to check if they are updated")
                old_time=methods.get_stack_file_time(logger)
                print("the old time is :"+old_time)
                rc=methods.click_retrv_recmnd_button1(logger, DRIVER)
                self.assertEqual(0, rc)
                print("clicked on Retrieve Recomenditions button")
                #call the timestamp of updated file
                updated_time=methods.get_stack_file_time(logger)
                print("updated_time is: "+updated_time)
                self.assertEqual(updated_time, old_time)
                print("validated the test, ppim couldnt connect the flrt :: proxy case \n\n ")
            except Exception as e:
                logger.error('Exception: %s', e)
        except:
            logger.error('Exception: %s', e)

        finally:
            DRIVER.close()


