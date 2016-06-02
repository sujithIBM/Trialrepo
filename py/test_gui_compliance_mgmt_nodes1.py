from selenium import webdriver
from test_common_version_check import testing_pages


import logging
import os
import unittest

if not os.path.exists('logs'):
    os.makedirs('logs')

logfile = 'logs' + os.sep + ((__file__.upper())[(__file__.rfind(os.sep)+1):]).replace('.PY', '.log')
logging.basicConfig(format= '%(asctime)-12s [%(filename)-10s] %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S', filename=logfile, filemode='w', level=logging.INFO)
logger = logging.getLogger(__name__)
print('#############################################################')
print('You can see log for detail: ' + logfile)
print('#############################################################')
filename='AddDevices.sh'
source_sh_file='C:\\temp\\AddDevices.sh'
tests=testing_pages()
mgmt_nodes_labels=['a','b','c','d']
driver = webdriver.Chrome()

def in_same_rack(rack_location1, rack_location2):
    rack_label1 = rack_location1.split('-')[0]
    rack_label2 = rack_location2.split('-')[0]
    return rack_label1 == rack_label2

class test_mgmt_nodes(unittest.TestCase):
    def test01_removing_devices(self):
        rc=tests.remove_all(logger)
        self.assertEqual(0, rc)

    def test02_adding_mgmt_nodes(self):
        tests.add_devices(source_sh_file, filename, logger)
        logger.info(".")

    def test03_management_nodes(self):
        #self.data=[['Retrieve Installed version\nRetrieve Recommendations', 'Filter'], ['Label', 'Type', 'Rack - EIA Location', 'IP Address', 'Installed Version', 'Base Version', 'Recommended Version', 'Compliance Status'], ['a', 'PurePower Integrated Manager Hypervisor', 'Primary', '9.3.46.192', '1.2.0', '1.2.0', '1.2.0', 'Compliant'], ['b', 'PowerVC', 'Primary', '9.3.46.195', '1.2.3.1', '1.2.3.2', '1.2.3.2', 'Not Compliant'], ['f', 'PurePower Integrated Manager Service VM', 'Primary', '9.3.46.194', '1.2.0', '1.2.0', '1.2.0', 'Compliant'], ['c', 'PurePower Integrated Manager Hypervisor', 'Primary', '9.3.46.192', '1.2.0', '1.2.0', '1.2.0', 'Compliant'], ['d', 'PowerVC', 'Primary', '9.3.46.195', '1.2.3.1', '1.2.3.2', '1.2.3.2', 'Not Compliant'], ['w', 'PurePower Integrated Manager Service VM', 'Primary', '9.3.46.194', '1.2.0', '1.2.0', '1.2.0', 'Compliant'], ['a', 'PurePower Integrated Manager Hypervisor', 'PrimaryPrimary', '9.3.46.192', '1.2.0', '1.2.0', '1.2.0', 'Compliant'], ['b', 'PowerVC', 'PrimaryPrimary', '9.3.46.195', '1.2.3.1', '1.2.3.2', '1.2.3.2', 'Not Compliant'], ['c', 'PurePower Integrated Manager Service VM', 'PrimaryPrimary', '9.3.46.194', '1.2.0', '1.2.0', '1.2.0', 'Compliant'], ['d', 'PurePower Integrated Manager Hypervisor', 'PrimaryPrimary', '9.3.46.192', '1.2.0', '1.2.0', '1.2.0', 'Compliant'], ['a', 'PowerVC', 'SPrimary', '9.3.46.195', '1.2.3.1', '1.2.3.2', '1.2.3.2', 'Not Compliant'], ['c', 'PurePower Integrated Manager Service VM', 'SPrimary', '9.3.46.194', '1.2.0', '1.2.0', '1.2.0', 'Compliant'], ['d', 'PurePower Integrated Manager Hypervisor', 'SPrimary', '9.3.46.192', '1.2.0', '1.2.0', '1.2.0', 'Compliant'], ['b', 'PowerVC', 'SPrimary', '9.3.46.195', '1.2.3.1', '1.2.3.2', '1.2.3.2', 'Not Compliant'], ['r', 'PurePower Integrated Manager Service VM', 'SPrimary', '9.3.46.194', '1.2.0', '1.2.0', '1.2.0', 'Compliant'], ['c', 'PurePower Integrated Manager Hypervisor', 'qPrimary', '9.3.46.192', '1.2.0', '1.2.0', '1.2.0', 'Compliant'], ['a', 'PowerVC', 'qPrimary', '9.3.46.195', '1.2.3.1', '1.2.3.2', '1.2.3.2', 'Not Compliant'], ['q', 'PurePower Integrated Manager Service VM', '1 -', '9.3.46.194', '1.2.0', '1.2.0', '1.2.0', 'Compliant'],['e', 'PurePower Integrated Manager Hypervisor', '1 -', '9.3.46.192', '1.2.0', '1.2.0', '1.2.0', 'Compliant'],['e', 'PurePower Integrated Manager Hypervisor', 'Primary', '9.3.46.192', '1.2.0', '1.2.0', '1.2.0', 'Compliant'],['Total: 3 Selected: 0']]
        logger.info('Opening PPIM')
        tests.open_ppim(driver)
        logger.info('Opening Compliance Page')
        tests.open_compliance_page(self.driver, logger)
        self.data=tests.get_grid(self.driver)
        del self.data[0]
        self.column_headings=self.data[0]
        del self.data[0]
        del self.data[len(self.data)-1]

        for i in range(len(self.column_headings)-1):
            if self.column_headings[i]=='Rack - EIA Location':
                self.rack_location=i
            elif self.column_headings[i]=='Label':
                self.label=i

        self.group_rack_location=self.data[0][self.rack_location]
        self.dup_mgmt_node_labels=mgmt_nodes_labels
        count=4
        rack_locs_checked=[]
        rack_locs_checked.append(self.group_rack_location)
        no_of_rows=len(self.data)

        for each in self.data:
            no_of_rows=no_of_rows-1
            if not in_same_rack(each[self.rack_location],self.group_rack_location):  #each[self.rack_location]!=self.group_rack_location:
                if count!=0:
                    logger.error('Elements left out from rack ('+str(self.group_rack_location.split('-')[0])+') are '+str(self.dup_mgmt_node_labels))
                logger.info('Rack label changes from '+str(self.group_rack_location.split('-')[0])+' to '+str(each[self.rack_location.split('-')[0]]))
                self.group_rack_location=each[self.rack_location]
                self.dup_mgmt_node_labels=['a','b','c','d']
                if self.group_rack_location not in rack_locs_checked:
                    rack_locs_checked.append(self.group_rack_location)
                    if each[self.label] in self.dup_mgmt_node_labels:
                        self.dup_mgmt_node_labels.remove(each[self.label])
                        count=len(self.dup_mgmt_node_labels)
                        if count==0:
                            print('SUCESS: Management nodes are together in rack location '+str(self.group_rack_location.plit('-')[0])
                            logger.info('SUCESS: Management nodes are together in rack location '+str(self.group_rack_location))
                            self.dup_mgmt_node_labels=['a','b','c','d']
                    else:
                        print('FAILED: Management nodes are not at the beginning in the rack '+str(self.group_rack_location.split('-')[0]))
                        logger.error('FAILED: Management nodes are not at the beginning in the rack '+str(self.group_rack_location.split('-')[0]))
                        break
                else:
                    logger.info('Rack Location already checked and being repeated again.')
                    logger.error('GRID NOT SORTED ACCORDING TO RACK LOCATION')
                    break

            elif in_same_rack(each[self.rack_location],self.group_rack_location):
                if each[self.label] in self.dup_mgmt_node_labels:
                    self.dup_mgmt_node_labels.remove(each[self.label])
                    count=len(self.dup_mgmt_node_labels)
                    if count==0:
                        logger.info('SUCESS: Management nodes are together in rack location '+str(self.group_rack_location))
                        print('SUCESS: Management nodes are together in rack location '+str(self.group_rack_location))
                        self.dup_mgmt_node_labels=['a','b','c','d']
                elif self.dup_mgmt_node_labels: # count != 0
                    print('FAILED: Management nodes are not at the beginning in the rack '+str(self.group_rack_location.split('-')[0]))
                    logger.error('FAILED: Management nodes are not at the beginning in the rack '+str(self.group_rack_location.split('-')[0]))
                    break
                else:
                    continue


        if no_of_rows==0:
            logger.info('END')


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()