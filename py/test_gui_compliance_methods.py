'''
Created on Aug 26, 2015

@author: sujith
'''
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from functools import reduce
import time
import yaml
import os
import logging
import unittest
from asyncio.log import logger


Label = 0
IP = 0
Installedversion = 0
BaseVersion = 0
recommendedVersion = 0
Compliancestatus = 0


class testing_methods(unittest.TestCase):
    def __init__(self):
        self

    #takes the Access Compliance version for Capturing data
    def compliance_ver(self,d,ver,logger):
        self.d=d
        print("Access compliance for pure version"+ver)
        logger.info("Access compliance for pure version"+ver)
        self.d.find_element_by_xpath('//*[@id="dijit_form_FilteringSelect_0"]').click()
        self.d.find_element_by_xpath('//*[@id="dijit_form_FilteringSelect_0"]').clear()
        self.d.find_element_by_xpath('//*[@id="dijit_form_FilteringSelect_0"]').send_keys(ver)
        self.d.find_element_by_xpath('//*[@id="dijit_form_FilteringSelect_0"]').send_keys(Keys.ENTER)
        self.getdata(d,logger)

    #capture data for the Given Compliance Version
    def getdata(self,d,logger):
        global Label
        global IP
        global Installedversion
        global BaseVersion
        global recommendedVersion
        global Compliancestatus
        global paras
        self.data=[]
        self.rowslist=[]
        self.rowslist = d.find_elements_by_xpath('.//table')
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

        print("******************RAW DATA******************")
        print(self.data)
        del self.data[0]#del Button Names
        self.headings=self.data[0]
        del self.data[0]#del Column Headings
        del self.data[len(self.data)-1]#Total Section
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
                Installedversion=i
                print(str(i)+" is Installed Version")
            elif self.headings[i]=='Base Version':
                BaseVersion=i
                print(str(i)+" is Base Version")
            elif self.headings[i]=='Recommended Version':
                recommendedVersion=i
                print(str(i)+" is Recommended Version")
            elif self.headings[i]=='Compliance Status':
                Compliancestatus=i
                print(str(i)+" is Compliance status")
        print(self.data)

        with open('devices.yml','r') as f :
            self.paras = yaml.load(f)
            print(self.paras)
            logger.info('paras= '+str(self.paras))
        self.Compliance_validate(self.data,self.paras,logger)

    def getFromDict(self,paras, mapList):
            return reduce(lambda d, k: d[k], mapList, paras)

    def verify_label(self,parase,list2,logger):
        try:
            paras_list=list(parase)

            for i in range(len(paras_list)):
                Device=paras_list[i]
                if Device == 'Puremgr' or Device == 'Nagiosmgr':
                    continue
                DevName=Device
                Device=self.getFromDict(parase,[Device])
                Device_no=self.getFromDict(Device, ["Device_01"])
                InitSetting=self.getFromDict(Device_no,["InitSetting"])
                InitSetting=InitSetting[0]
                self.verify_status(InitSetting,list2,DevName,logger)
        except Exception as e:
            logger.info('FAILED while collecting data from config file. Failed for device '+str(DevName)+' from config file')
            logger.info('Exception: %s', e)

    def get_textBVRV(self,d,list2,k,logger):
        try:
            global Label
            self.data = []
            self.rowslist = []
            BV = list2[3]
            RV = list2[4]
            Label = list2[0]
            self.rowslist = d.find_elements_by_xpath('.//table')
            for table in self.rowslist:
                self.data_row=[]
                self.tds=table.find_elements_by_tag_name('td')
                if self.tds:
                    for td in self.tds:
                        if td == list2[0]:
                            BVlink=d.find_element_by_link_text(BV).get_attribute('href')
                            RVlink=d.find_element_by_link_text(RV).get_attribute('href')
                            print(BVlink)
                            self.BVlinkclick(d,BVlink,BV,logger)
                            print(RVlink)
                            self.BVlinkclick(d,RVlink,BV,logger)
                            if k[7] == BVlink and k[8]==RVlink:
                                logger.info("SUCCESS: BV and RV links matched")
                            else:
                                logger.info("FAILED: BV and RV links not matched")
        except Exception as e:
            logger.info('FAILED while checking for the links')
            logger.info('Exception: %s', e)

    def BVlinkclick(self,d,link,BV,logger):
        try:
            d.get(link)
            version1 = d.find_element_by_name(BV)
            if version1 == BV:
                logger.info("SUCCESS: Found the version in the opened link")
            else:
                logger.info("FAILED: Not found in the link")
        except Exception as e:
            logger.info('Exception: %s', e)

    def RVlinkclick(self,d,link,RV,logger):
        try:
            d.get(link)
            version1 = d.find_element_by_name(RV)
            if version1 == RV:
                logger.info("SUCCESS: Found the version in the opened link")
            else:
                logger.info("FAILED: Not found in the link")
        except Exception as e:
            logger.info('Exception: %s', e)

    def verify_status(self,parase,list2,Device,logger):
        try:
            k=[]
            global paras
            paras=parase
            self.Device=Device
            k.append(paras['label'])
            k.append(paras['ipv4_address'])
            k.append(paras['Version'])
            k.append(paras['BaseVersion'])
            k.append(paras['RecommendedVersion'])
            k.append(paras['Compliance'])
            k.append(paras['Link'])
            k.append(paras['BVUrl'])
            k.append(paras['RVUrl'])

            if list2[0]==k[0]:
                if list2[1]== k[1]:
                    if list2[2]==k[2] and list2[3]==k[3] and list2[4]==k[4]:
                        logger.info("SUCCESS: All versions are matched with the config file")
                        if list2[5]== k[5]:
                            logger.info("SUCCESS: Compliance status checked and validated")
                            if(k[6] == 'True'):
                                logger.info("SUCCESS: Device Not compliant: Checking with the links")
                                print("checking urls for BV and RV")
                                self.get_textBVRV(self.d,list2,k,logger)
                            else:
                                if list2[2] == list2[3] or list2[2]== list2[4]:
                                    print(list2[5])
                                    logger.info('Marked FALSE as '+ str(list2[5]))
                    else:
                        logger.info("SUCCESS: Versions are not matching with the config file")
                        if list2[5]=='Non Compliant':
                            logger.info('SUCCESS: Compliance status checked and validated')
                            if(k[6] == 'True'):
                                logger.info("SUCCESS: Not compliant: checking with the links")
                                print("checking urls for BV and RV")
                                self.get_textBVRV(self.d,list2,k,logger)
                            else:
                                if list2[2] == list2[3] or list2[2]== list2[4]:
                                    print(list2[5])
                                    logger.info('Marked FALSE as '+ str(list2[5]))
                        else:
                            if list2[5]=='Compliant':
                                logger.info('FAILED: WRONG Compliance Status is Displayed')

                else:
                    print('FAILED: IP Address not matching')
                    logger.info('FAILED: IP Address not matching')
            #else:
                #print('FAILED: Label not matching')
                #logger.info('FAILED: Label not matching')
        except Exception as e:
            logger.info('Exception: %s', e)
            return 1

    def Compliance_validate(self,data,paras,logger):
        try:
            print("******************VERSION VALIDATION STARTS******************")
            logger.info("******************VERSION VALIDATION STARTS******************")
            paras=paras
            i=0
            list2=[]
            global Label
            global IP
            global Installedversion
            global BaseVersion
            global RecommendedVersion
            global Compliancestatus

            while i<len(data):
                print(">>>>>Test " + str(i+1)+" for " + str(data[i][Label]))
                logger.info(">>>>>Test " + str(i+1)+" for " + str(data[i][Label]))
                list2.append(data[i][Label])
                list2.append(data[i][IP])
                list2.append(data[i][Installedversion])
                list2.append(data[i][BaseVersion])
                list2.append(data[i][recommendedVersion])
                list2.append(data[i][Compliancestatus])
                self.verify_label(paras,list2,logger)
                list2=[]
                i+=1
            print("******************VERSION VALIDATION ENDS******************")
            logger.info("******************VERSION VALIDATION ENDS******************")
            return 0
        except Exception as e:
            logger.info('Exception: %s', e)
            return 1
