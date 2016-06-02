paras = {'Ubuntu': {'Device_01': {'NewSetting': [{'user': None, 'netmask': None, 'rack_location': None, 'password': 'newPassw0rd', 'rack_id': None, 'gateway': None, 'ipv4_address': None, 'label': 'new_Ubuntu'}], 'InitSetting': [{'user': 'root', 'device_type': 'Ubuntu', 'rack_location': None, 'password': 'D0ntknow', 'rack_id': None, 'version': 15.04, 'ipv4_address': '9.114.104.235', 'label': 'Ubuntu15'}]}}, 'Brocade': {'Device_01': {'NewSetting': [{'user': None, 'netmask': None, 'rack_location': None, 'password': 'newPassw0rd', 'rack_id': None, 'gateway': None, 'ipv4_address': None, 'label': 'new_Brocade'}], 'InitSetting': [{'user': 'admin', 'device_type': 'Brocade', 'rack_location': 'pok', 'serial_number': None, 'password': 'passw0rd', 'rack_id': 'c', 'machine type model': None, 'ipv4_address': '192.168.93.11', 'label': 'san_switch'}]}}, 'RHEL': {'Device_01': {'NewSetting': [{'user': None, 'netmask': None, 'rack_location': None, 'password': 'newPassw0rd', 'rack_id': None, 'gateway': None, 'ipv4_address': None, 'label': 'new_RHEL7'}], 'InitSetting': [{'user': 'root', 'device_type': 'RHEL', 'rack_location': 'rhe', 'serial_number': 'XXXX', 'password': 'PASSW0RD', 'rack_id': 'e', 'machine type model': 0, 'version': 7.1, 'ipv4_address': '9.3.46.207', 'label': 'rhel7'}]}}, 'Puremgr': [{'user': 'root', 'bsoid': 'isdsvt@us.ibm.com', 'build': '20150615-1330', 'password': 'PASSW0RD', 'ipv4_address': '9.3.46.208', 'bsopw': 'Passw2rd', 'version': '1.0.0'}], 'Mellanox_Switch': {'Device_01': {'NewSetting': [{'user': None, 'netmask': None, 'rack_location': None, 'password': 'newPassw0rd', 'rack_id': None, 'gateway': None, 'ipv4_address': None, 'label': 'new_mellanox'}], 'InitSetting': [{'user': 'admin', 'device_type': 'Mellanox_Switch', 'rack_location': 'loc', 'serial_number': None, 'password': 'admin', 'rack_id': 'a', 'machine type model': None, 'ipv4_address': '192.168.93.37', 'label': 'mellanox_switch'}]}}, 'PDU': {'Device_01': {'NewSetting': [{'user': None, 'netmask': None, 'rack_location': None, 'password': 'newPassw0rd', 'rack_id': None, 'gateway': None, 'ipv4_address': None, 'label': 'new_PDU'}], 'InitSetting': [{'user': 'USERID', 'device_type': 'PDU', 'rack_location': None, 'password': 'passw0rd', 'ipv4_address': '192.168.93.25', 'rack_id': None, 'label': 'PDU3'}]}}, 'Nagiosmgr': [{'user': 'nagiosadmin', 'password': 'PASSW0RD', 'ipv4_address': '9.3.46.208', 'bsopw': 'Passw2rd', 'bsoid': 'isdsvt@us.ibm.com'}], 'IBM_Switch': {'Device_01': {'NewSetting': [{'user': None, 'netmask': None, 'rack_location': 121, 'password': 'newPassw0rd', 'rack_id': 9, 'gateway': None, 'ipv4_address': '9.114.200.99', 'label': 'new_rack'}], 'InitSetting': [{'user': 'admin', 'device_type': 'IBM_Switch', 'rack_location': 'loc', 'serial_number': None, 'password': 'admin', 'rack_id': 'a', 'machine type model': None, 'ipv4_address': '192.168.93.83', 'label': 'rack_switch'}]}}, 'HMC': {'Device_01': {'NewSetting': [{'user': None, 'netmask': None, 'rack_location': None, 'password': 'newPassw0rd', 'rack_id': None, 'gateway': None, 'ipv4_address': None, 'label': 'new_HMC'}], 'InitSetting': [{'user': 'hscroot', 'device_type': 'HMC', 'rack_location': 'HMC', 'serial_number': 'XXXX', 'password': 'abc1234', 'rack_id': 'd', 'machine type model': 0, 'ipv4_address': '9.3.46.190', 'label': 'HMC_217'}]}}, 'SVC': {'Device_01': {'NewSetting': [{'user': None, 'netmask': None, 'rack_location': None, 'password': 'newPassw0rd', 'rack_id': None, 'gateway': None, 'ipv4_address': None, 'label': 'new_v7000'}], 'InitSetting': [{'user': 'superuser', 'device_type': 'SVC', 'rack_location': 'POK', 'serial_number': 1234567, 'password': 'passw0rd', 'rack_id': 'b', 'machine type model': 0, 'ipv4_address': '192.168.93.8', 'label': 'V7000'}]}}}

print(paras)

"""gui_edit_device"""

logfile = 'logs' + os.sep + ((__file__.upper())[(__file__.rfind(os.sep)+1):]).replace('.PY', '.log')
logging.basicConfig(format= '%(asctime)-12s [%(filename)-10s] %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S', filename=logfile, filemode='w', level=logging.INFO)


"""test_gui_device"""

logfile = 'logs/' + ((__file__.upper())[(__file__.rfind('/')+1):]).replace('.PY', '.log')
logging.basicConfig(format= '%(asctime)-12s [%(filename)-10s] %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S', filename=logfile, filemode='w', level=logging.DEBUG)


"""gui_add_device"""


logfile = 'logs' + os.sep + ((__file__.upper())[(__file__.rfind(os.sep)+1):]).replace('.PY', '.log')
logging.basicConfig(format= '%(asctime)-12s [%(filename)-10s] %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S', filename=logfile, filemode='w', level=logging.DEBUG)


"""gui_add_device_webdriver"""

logfile = 'logs' + os.sep + ((__file__.upper())[(__file__.rfind(os.sep)+1):]).replace('.PY', '.log')
logging.basicConfig(format= '%(asctime)-12s [%(filename)-10s] %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S', filename=logfile, filemode='w', level=logging.DEBUG)
logger = logging.getLogger(__name__)



"test_gui_inventory"
logfile = 'logs' + os.sep + ((__file__.upper())[(__file__.rfind(os.sep)+1):]).replace('.PY', '.log')
logging.basicConfig(format= '%(asctime)-12s [%(filename)-10s] %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S', filename=logfile, filemode='w', level=logging.DEBUG)


