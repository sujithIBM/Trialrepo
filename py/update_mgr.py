#!/usr/local/bin/python3.4
# Licensed Materials - Property of IBM
#
# (C) Copyright IBM Corp. 2015 All Rights Reserved
#
# US Government Users Restricted Rights - Use, duplicate or
# disclosure restricted by GSA ADP Schedule Contract with
# IBM Corp.

import logging
import json
import device_mgr
import persistent_mgr
import flrt_query
import shutil
import manage_nagios_core
import constants
import collections
import os
import tarfile
import paramiko
import sshUtils
import socket
import utils
import queue
from threading import Thread
import itertools
import math
import prop_file_utils
import grp
import ast
import copy

LIB_PATH = os.path.split(os.path.realpath(__file__))[0]
BIN_DIR_PATH = LIB_PATH + "/../bin"

# Maximum number of threads that will be launched for collecting versions related inventory
MAX_INVENTORY_THREADS=15

COMPLIANCE_UNSUPPORTED_DEVICE_TYPES = [
                                       constants.device_type.PDU.name,
                                       constants.device_type.StorwizeExpansion.name,
                                       constants.device_type.AIX.name,
                                       constants.device_type.RHEL.name,
                                       constants.device_type.Ubuntu.name
                                        ]

#Compliance Status Values:
Compliance_Status = {
    'compliant' : _("Up To Date"),  # device firmware is already at the recommended level
    'compliant-but-update-available' : _("Update Available"),  # device firmware is at base level but that is different from recommended level
    'not-compliant' : _("Update Required"), # device firmware level is different from base level and different from recommended level
    'unsupported-device-type' : _("Not Supported"), # FLRT data doesn't contain version info for the specific device type
    'status-not-available' : _("Not Available") # PPIM could not retrieve version of device firmware for some reason (like device not reachable, or powerNode not managed any HMC, etc)
}

Offline_FLRT_files = [os.path.realpath(LIB_PATH + '/flrt_query.py'),
                      os.path.realpath(LIB_PATH + '/prop_file_utils.py'),
                      os.path.realpath(LIB_PATH + '/../bin/generate_stack_definition'),
                      os.path.realpath(LIB_PATH + '/../etc/updates_compliance.properties')]


PROP_CONNECTION_TYPE = 'flrt_connection_type'
PROP_PROXY_MACHINE_IP = 'proxy_machine_ip'
PROP_PROXY_MACHINE_USERID = 'proxy_machine_userid'
PROP_PROXY_MACHINE_ENCRYPTED_PASSWORD = 'proxy_machine_encrypted_password'

STACK_DEFINITIONS_FILE='/opt/ibm/puremgr/etc/stack_definitions.json'
STACK_DEFINITIONS_DEFAULT_FILE='/opt/ibm/puremgr/etc/stack_definitions_default.json'
STACK_DEFINITIONS_BACKUP_FILE='/opt/ibm/puremgr/etc/stack_definitions_backup.json'
STACK_DEFINITIONS_CORRUPT_FILE='/opt/ibm/puremgr/etc/stack_definitions_corrupt.json'
STACK_DEFINITIONS_TMP_FILE='/tmp/stack_definitions.json.flrt'
STACK_DEFINITIONS_PROXY_TMP_FILE='/tmp/stack_definitions.json.flrt.proxy'

def read_stack_definition_file(is_retry=False):
    _METHOD_="update_mgr.read_stack_definition_file"
    logging.info ("%s:: Enter - is_retry: %s", _METHOD_, is_retry)
    file_contents = None
    file = None
    filename = STACK_DEFINITIONS_FILE
    has_read_failed = False
    dict_json = None
    try:
        file = open(filename,'r')
        logging.debug("%s:: Opened file to read contents %s", _METHOD_, filename)
        file_contents = file.read()
    except Exception as e:
        logging.warning("%s::Exception during file operation %s : %s", _METHOD_, filename, e)
        has_read_failed = True
    finally:
        if file != None:
            file.close()

    if not file_contents:
        logging.warning("%s:: File content is none : %s", _METHOD_, filename)
        has_read_failed = True
    else:
        try:
            dict_json = json.loads(file_contents)
        except KeyError as e:
            logging.warning("%s: Key content error in text_json, can not load data from request body", _METHOD_)
            has_read_failed = True
        except Exception as ex:
            logging.warning("%s::Content maybe none or not right. Exception : %s",_METHOD_, ex)
            has_read_failed = True

    logging.debug("%s: has_read_failed: %s", _METHOD_,has_read_failed)
    # if reading file failed,attempt to retry
    #retry only when restore was successful
    #check is_retry to make sure we do not end up in an infinite loop if there is an exception even after restore
    if has_read_failed and not is_retry and restore_stack_definition_file():
        return read_stack_definition_file(is_retry=True)

    return dict_json

def get_all_ppim_versions():
    _METHOD_="update_mgr.get_all_ppim_versions"

    file_content_json = read_stack_definition_file()

    if not file_content_json:
        logging.warning("%s: Could not read information from stack definition file", _METHOD_)
        return None

    version_list = []
    stacks_definition = file_content_json['stacks_definition']
    if not stacks_definition:
        logging.warning("%s:: stacks_definition is None", _METHOD_)
        return version_list

    ppim_stack_list = stacks_definition['ppim_stack_list']
    if not ppim_stack_list or len(ppim_stack_list) == 0:
        logging.warning("%s:: ppim_stack_list is None or empty", _METHOD_)
        return version_list

    # Loop through the ppim stacks and get each version and add it to the list
    for ppim_stack in ppim_stack_list:
        version_list.append(ppim_stack['version'])

    return version_list

def get_date_from_stack_definition_file():
    _METHOD_="update_mgr.get_date_from_stack_definition_file"

    file_content_json = read_stack_definition_file()

    if not file_content_json:
        logging.warning("%s: Could not read information from stack definition file", _METHOD_)
        return ''

    stacks_definition = file_content_json['stacks_definition']
    if not stacks_definition:
        logging.warning("%s:: stacks_definition is None", _METHOD_)
        return ''

    date = stacks_definition['last_updated_time']
    if not date:
        logging.warning("%s:: Date could not be retrieved from stack definition file", _METHOD_)
        return ''

    return date

def get_compliant_versions(device_type, ppim_version):
    ''' Return all the compliant versions of devices of a device_type - compliant to a specific ppim version
        Example: For the hmc device type for a specifc ppim version, return
        <"base", hmc_base_version>, <"recommended_update", hmc_recommended_update_version>,
        <"recommended_upgrade", hmc_recommended_upgrade_version>
    '''
    _METHOD_="update_mgr.get_all_ppim_versions"

    file_content_json = read_stack_definition_file()

    if not file_content_json:
        logging.warning("%s: Could not read information from stack definition file", _METHOD_)
        return None

    if not device_type or not ppim_version:
        logging.warning("%s: Device type or PPIM version is None", _METHOD_)
        return None

    stacks_definition = file_content_json['stacks_definition']
    if not stacks_definition:
        logging.warning("%s:: stacks_definition is None", _METHOD_)
        return None

    ppim_stack_list = stacks_definition['ppim_stack_list']
    if not ppim_stack_list or len(ppim_stack_list) == 0:
        logging.warning("%s:: ppim_stack_list is None or empty", _METHOD_)
        return None

    for ppim_stack in ppim_stack_list:
        if ppim_version == ppim_stack['version']:
            device_type_list = ppim_stack['device_type_list']
            if not device_type_list or len(device_type_list) == 0:
                logging.warning("%s:: No device_types found for PPIM version : %s", _METHOD_, ppim_version)
                return None
            for device in device_type_list:
                if device['type']==device_type:
                    return device

    return None

def get_stack_definition(ppim_version):
    ''' Read the stack definition file for the specific puremgr_version.
        Returns a dictionary with device_type as key and value is another dictionary containing all compliant
        versions info. Example <key,value> is
        <hmc, <<"base", hmc_base_version>, <"recommended_update", hmc_recommended_update_version>,
        <"recommended_upgrade", hmc_recommended_upgrade_version>>
    '''
    _METHOD_="udpate_mgr.get_all_ppim_versions"

    return_ppim_stack = {}

    if not ppim_version or ppim_version == '':
        logging.warning("%s: PPIM version passed is None or empty", _METHOD_)
        return return_ppim_stack

    file_content_json = read_stack_definition_file()

    if not file_content_json:
        logging.warning("%s: Could not read information from stack definition file", _METHOD_)
        return return_ppim_stack

    stacks_definition = file_content_json['stacks_definition']
    if not stacks_definition:
        logging.warning("%s:: stacks_definition is None", _METHOD_)
        return return_ppim_stack

    ppim_stack_list = stacks_definition['ppim_stack_list']
    if not ppim_stack_list or len(ppim_stack_list) == 0:
        logging.warning("%s:: ppim_stack_list is None or empty", _METHOD_)
        return return_ppim_stack

    for ppim_stack in ppim_stack_list:
        if ppim_version == ppim_stack['version']:
            device_type_list = ppim_stack['device_type_list']
            if not device_type_list or len(device_type_list) == 0:
                logging.warning("%s:: No device_types found for PPIM version : %s", _METHOD_, ppim_version)
                return None
            for device_type in device_type_list:
                return_ppim_stack[device_type['type']]=device_type
            break

    return return_ppim_stack

def plugin_get_managed_devices_version(plugin, ip, userid, password, set_managed_devices_to_inventory):
    _METHOD_ = 'update_mgr.plugin_get_managed_devices_version'
    logging.info("ENTER %s::Call plugin.get_managed_devices_version() for retrieving managed devices %s.", _METHOD_, str(set_managed_devices_to_inventory));
    if "get_managed_devices_version" in dir(plugin):
        return (0 ,plugin.get_managed_devices_version(ip, userid, password, set_managed_devices_to_inventory))
    else:
        return (11, None)

def get_managed_devices_version(management_devices, managed_devices_to_inventory):
    ''' Searches for managed devices in management_devices and fetches the version for managed devices
        Input :
            management_devices - contains the management devices like HMC.
            managed_devices_to_inventory - contains the dict of managed devices like PowerNode for which version needs to be fetched.

        The code does the following until all management devices in the input is iterated or all devices are inventoried.
            1.For each management device
            2. Call plugin.get_managed_devices_version with list of managed_devices_to_inventory
                2a. plugin.get_managed_devices_version - Looks for managed devices provided in the input list and return devices with version and devices not found
            3. rc, fetched_managed_devices, devices_not_inventoried -
                fetched_managed_devices is the dict of the managed devices found in the management device with its version
                devices_not_inventoried is the list of managed devices NOT found in the management device
            4.if there are fetched_managed_devices, add them to result with new version
            5. if no devices in devices_not_inventoried, we have fetched version for all devices input, break the for loop and return the result
            6.if there are devices_not_inventoried, iterate to next management device, repeat the loop - go to step 1

        Output:
           result - list of tuples (return_code, label, device_id, device_type, ip, current_version, fixes)
           fixes in the result is a list in the below format.
           [FP24,SP02,IV1352,IV3246,MH01409,MH01451,MH01551,MH01573,myOwnFix24531,IT65432]
    '''
    _METHOD_ = 'update_mgr.get_managed_devices_version'
    logging.info("ENTER %s::Collecting versions related inventory for managed devices.", _METHOD_);
    result = []
    plugins = device_mgr.load_device_plugins()
    if managed_devices_to_inventory:
        list_managed_devices_to_inventory = list(managed_devices_to_inventory)
        if management_devices:
            # iterate through the managed devices, get the latest version that would have got updated in the above call as include_managed_nodes = True
            for device_info in management_devices:
                logging.debug("%s::Getting versions for managed device from management device with label %s.", _METHOD_, device_info.label);
                device_type = device_info.device_type
                ip = device_info.ipv4_addr
                userid = device_info.userid
                password = device_info.password
                plugin = plugins[device_type]
                (plugin_rc, details) = plugin_get_managed_devices_version(plugin, ip, userid, password, list_managed_devices_to_inventory )
                if plugin_rc != 0 :
                    logging.warning("%s:: plugin.get_managed_devices_version() not found in plugin for device type %s with name %s", _METHOD_, device_type, device_info.label)
                    continue
                if len(details) < 3:
                    logging.warning("%s:: Unexpected results from plugin.get_managed_devices_version() for device %s", _METHOD_, device_info.label)
                    continue
                rc, fetched_managed_devices, devices_not_inventoried = details

                if rc != 0:
                    logging.warning("%s:: Error occurred during plugin.get_managed_devices_version() for device %s", _METHOD_, device_info.label)
                    continue
                #logging.debug("%s::Fetched versions for managed device %s in management device %s.", _METHOD_, fetched_managed_devices, device_info.label);
                #logging.debug("%s::Could not find versions for managed device %s in management device %s.", _METHOD_, devices_not_inventoried, device_info.label);
                #check if any devices are found and its versions are fetched
                if fetched_managed_devices:
                    #iterate thru set inventoried_devices
                    for device_key in fetched_managed_devices:
                        #get fetched versions and get device object from to inventory
                        (label, device_id, device_type, ip, existing_version,existing_fixes) = managed_devices_to_inventory[device_key]
                        logging.debug("%s::Fetched version for managed device with label %s.", _METHOD_, label);
                        vrc, (current_version, current_fixes) = fetched_managed_devices[device_key]
                        # version is the first element in tuple
                        if current_version == None:
                            current_version = "" 
                        if current_fixes is None:
                            current_fixes = []
                        # Update devices.xml only if the existing version in devices.xml is different from the one obtained through get_version()
                        if existing_version != current_version:
                            device_mgr.change_device_properties(label=label, version=current_version)
                        try:
                            if isinstance(existing_fixes, str):
                                existing_fixes = ast.literal_eval(existing_fixes)
                        except Exception as e:
                            logging.error("Exception in %s converting string >>%s<< to list", _METHOD_, existing_fixes)
                        if set(existing_fixes) != set(current_fixes):
                            fixes_str = str(current_fixes)
                            device_mgr.change_device_properties(label=label, fixes=fixes_str)
                        #add the device info to the results
                        #if vrc != 0 , pass vrc as is to identify the exact problem
                        #vrc = 3 - Version information unavailable for managed node 
                        #vrc = 4 - Error occurred while running get version command for managed node
                        result.append((vrc, label, device_id, device_type, ip, current_version))
                    #remove found devices from managed_devices_to_inventory
                    list_managed_devices_to_inventory = devices_not_inventoried
                    if len(list_managed_devices_to_inventory) == 0:
                        #all devices are inventoried. no need to scan the next management node
                        break
                #end of for loop for management devices
        if len(list_managed_devices_to_inventory) > 0:
            #some devices are not found in the current environment
            logging.warning("%s:: Devices not managed by any of the management devices : " , _METHOD_, list_managed_devices_to_inventory)
            for device_key in list_managed_devices_to_inventory:
                #get fetched versions and get device object from to inventory
                (label, device_id, device_type, ip, existing_version,existing_fixes) = managed_devices_to_inventory[device_key]
                device_mgr.change_device_properties(label=label, version="")
                #rc = 12 means managed node not found in any of the management device. ie., power node not found in any hmc.
                result.append((12, label, device_id, device_type, ip, ""))

    return result

def get_device_version(label, ip, userid, password, plugin, existing_version, existing_fixes):
    ''' For the specific device,
           Get the version info by contacting the device.
           Update the version info in devices.xml, if required.
           Return (return_code,(version,fixes))
    '''
    _METHOD_ = 'update_mgr.get_device_version'
    (rc, (version,fixes)) = plugin.get_version(ip, userid, password)
    #reset version to empty string incase version is none so it will get updated in devices.xml
    if version==None:
        version = ""
    # Update devices.xml only if the existing version in devices.xml is different from the one obtained through get_version()
    if existing_version != version:
        device_mgr.change_device_properties(label=label, version=version)
        
    try:
        if isinstance(existing_fixes, str):
            existing_fixes = ast.literal_eval(existing_fixes)
    except Exception as e:
        logging.error("Exception in %s converting string >>%s<< to list", _METHOD_, existing_fixes)
    
    if set(fixes) != set(existing_fixes):
        fixes_str = str(fixes)
        device_mgr.change_device_properties(label=label, fixes=fixes_str)

    return (rc, (version,fixes))

def get_devices_versions_thread(devices, my_queue):
    '''For the given list of devices, perform version related inventory collection and
      update devices.xml with the version info.
      Prepares the list of (return_code, label, device_id, device_type, ip_address, version) for the given devices.
    '''
    _METHOD_ = 'update_mgr.get_devices_versions_thread'
    logging.info("ENTER %s::Get Devices versions.", _METHOD_);
    plugins = device_mgr.load_device_plugins()
    for device in devices:
        label = persistent_mgr.get_child_element_value(device, 'label')
        device_id = persistent_mgr.get_child_element_value(device, 'deviceid')
        ip = persistent_mgr.get_child_element_value(device, 'ipv4-service-address')
        userid = persistent_mgr.get_child_element_value(device, 'userid')
        password = persistent_mgr.get_child_element_value(device, 'password')
        password = persistent_mgr.decryptData(password)
        device_type = persistent_mgr.get_child_element_value(device, 'device-type')
        plugin = plugins[device_type]
        existing_version = persistent_mgr.get_child_element_value(device, 'version')
        existing_fixes = persistent_mgr.get_child_element_value(device, 'fixes')
        (rc, (version, fixes)) = get_device_version(label, ip, userid, password, plugin, existing_version, existing_fixes)

        my_queue.put((rc, label, device_id, device_type, ip, version, fixes))

def split_devices(iterable, size, num_lists_with_more_devices):
    ''' Split the devices into multiple lists of devices such that the first num_lists_with_more_devices lists will contain size devices each
       and the remaining lists of devices will contain size-1 devices each.
    '''
    size_changed = False
    it = iter(iterable)
    if num_lists_with_more_devices > 0:
        num_lists_with_more_devices -= 1
    else:
        size_changed = True    # No need to decrease size for this case. This case means all resultant lists will have exactly same size

    item = list(itertools.islice(it, size))
    while item:
        yield item
        if not size_changed:
            if num_lists_with_more_devices > 0:
                num_lists_with_more_devices -= 1
            else:
                size -= 1
                size_changed = True
        item = list(itertools.islice(it, size))

def get_devices_versions(devices):
    ''' For the given list of devices, perform version related inventory collection and
      update devices.xml with the version info.
      Return the list of (return_code, label, device_id, device_type, ip_address, version) for the given devices.
    '''
    _METHOD_ = 'update_mgr.get_devices_versions'
    logging.info("ENTER %s::Collecting versions related inventory - Number of devices : %d", _METHOD_, len(devices));

    result = []
    #split devices by type
    managed_devices_to_inventory, devices_to_inventory = persistent_mgr.split_elements_by_tag(devices, 'device-type', list(constants.MANAGEMENT_DEVICE_MAP))

    if devices_to_inventory: # devices not managed-by other devices (managed-by-devices: PowerNodes. These are managed-by HMCs)
        threads=[]
        my_queue = queue.Queue()

        num_devices = len(devices_to_inventory)
        num_threads = min(MAX_INVENTORY_THREADS, num_devices)
        num_devices_per_thread = math.ceil(num_devices*1.0/num_threads)
        # Assign num_devices_per_thread devices to the first num_threads_with_more_devices threads. Then
        # assign (num_devices_per_thread - 1) devices to the remaining threads. If num_threads_with_more_devices is 0, then
        # all the splits will have num_devices_per_thread as number of devices.
        num_threads_with_more_devices = num_devices % num_threads

        device_lists = list(split_devices(devices_to_inventory,num_devices_per_thread, num_threads_with_more_devices))
        logging.info("%s::devices_list length:%d", _METHOD_, len(device_lists));
        for device_list in device_lists:
            t = Thread(target=get_devices_versions_thread,args=(device_list,my_queue))
            t.start()
            threads.append(t)

        for t in threads: # Wait for threads to complete execution
            t.join()

        while not my_queue.empty():
            result.append(my_queue.get())

    if managed_devices_to_inventory: # TODO: Parallellize using threads
        logging.debug("%s::Processing managed devices.", _METHOD_)
        dict_managed_devices = {}
        management_devices_types = []
        for device in managed_devices_to_inventory:
            device_type = persistent_mgr.get_child_element_value(device, 'device-type')
            mtm = persistent_mgr.get_child_element_value(device, 'machine-type-model')
            serialnum = persistent_mgr.get_child_element_value(device, 'serial-number')
            label = persistent_mgr.get_child_element_value(device, 'label')
            device_id = persistent_mgr.get_child_element_value(device, 'deviceid')
            ip = persistent_mgr.get_child_element_value(device, 'ipv4-service-address')
            existing_version = persistent_mgr.get_child_element_value(device, 'version')
            existing_fixes = persistent_mgr.get_child_element_value(device, 'fixes')
            logging.debug("%s::Gathering managed device %s to get version later.", _METHOD_, label);
            dict_managed_devices[mtm+"_"+serialnum]=(label, device_id, device_type, ip, existing_version, existing_fixes)
            mgmt_device_type = constants.MANAGEMENT_DEVICE_MAP[device_type]
            if not mgmt_device_type in management_devices_types:
                #note down the respective management device type to later iterate its managed devices to get versions
                management_devices_types.append(mgmt_device_type)
        if management_devices_types:
            (management_devices, not_found_device_types) = persistent_mgr.get_devices_info(device_types=management_devices_types)
            logging.debug("%s::Fetched the management devices %s to get managed devices version.", _METHOD_, len(management_devices))
            result.extend(get_managed_devices_version(management_devices, dict_managed_devices))
        else:
            logging.warning("%s::No management devices found in the inventory, hence cannot collect version inventory for one or more managed device(s) %s ", _METHOD_, str(managed_devices_to_inventory));
    logging.debug("EXIT %s::result %s ", _METHOD_, str(result));

    return result

def get_all_devices_versions():
    ''' For all devices in devices.xml, perform get_version() and update devices.xml with the version info.
    Return the list of (return_code, label, device_id, device_type, ip_address, version) for all devices.
    '''
    _METHOD_ = 'update_mgr.get_all_devices_versions'
    logging.info("ENTER %s::Collecting versions related inventory.", _METHOD_);

    doc = persistent_mgr.open_config_xml()
    devices, not_found_values = persistent_mgr.get_devices(doc)
    if len(devices) == 0:
        message = _("No device found.")
        return message
    return get_devices_versions(devices)

def collect_versions_inventory(labels_str=None, device_ids_str=None, for_all_devices=False, rack_id=None):
    ''' for_all_devices: If True, then inventory collection is done for all devices and update devices.xml.
       labels is a string with comma separated values. Example: "hmc2,vios5,v7k4".
       deviceids is also a string with comma separated values.
       If deviceids is specified, then labels is ignored.
       rack_id is the rack id of the rack whose devices' inventory collection is to be done.
       For the given list of devices' labels or device_ids or the devices of a rack, perform version related inventory collection and
       update devices.xml with the version info.

       Return the list of (return_code, label, device_id, device_type, ip_address, version) for the given devices.
    '''
    _METHOD_ = 'update_mgr.collect_versions_inventory'
    logging.info("ENTER %s::Collecting versions related inventory - labels_str=%s, device_ids_str=%s, for_all_devices=%s, rack_id=%s.", _METHOD_, labels_str, device_ids_str, for_all_devices, rack_id);
    if for_all_devices == False:
        if labels_str == None and device_ids_str == None:
            message = _("Both labels and device_ids lists are empty.")
            logging.warning("%s:: Both labels_list and device_ids_list are empty.", _METHOD_)
            return message
    else:
        return get_all_devices_versions()
    doc = persistent_mgr.open_config_xml()
    devices,not_found_value = persistent_mgr.get_devices(doc, labels=labels_str, deviceids=device_ids_str, all_devices=for_all_devices, rack_id=rack_id)
    logging.warning("%s:: Labels/device ids/rack ids of devices not found:", _METHOD_, not_found_value)
    if len(devices) == 0:
        logging.warning("%s:: No devices found.", _METHOD_)
        message = _("No devices found.")
        return message
    return get_devices_versions(devices)

def get_fixes_details(fixes_list_dict):
    ''' Return list of fix details dictionaries
    Return  [ {"fix":value,"fix_link":value, "fix_order":value},...]
    '''
    
    _METHOD_ = 'update_mgr.get_fixes_details'
    result_dict = {}
    result_list = []
    
    logging.info("%s:: fixes_list_dict=%s", _METHOD_, fixes_list_dict)
    
    
    if fixes_list_dict == None:
        return result_list
    for fix_details in fixes_list_dict:
        fix  =  fix_details.get(flrt_query.FIX_VERSION)
        fix_link = fix_details.get(flrt_query.FIX_LINK)
        fix_order = fix_details.get(flrt_query.FIX_ORDER)
        
        logging.info("%s:: fix=%s,fix_link=%s,fix_order=%s", _METHOD_, fix,fix_link,fix_order)
        result_dict['fix'] = fix
        result_dict['fix_link'] = fix_link
        result_dict['fix_order'] = fix_order
        result_list.append(result_dict.copy())            
        result_dict.clear()
    return result_list
    

def get_compliant_versions_tuples(stack_def_dict=None, device_type=None):
    ''' Return the return code, a tuple of all the compliant versions of devices of the given device_type and a tuple of recommended versions.
    Return code 1 for device_type not supported
    Return code 0 for any supported device_type
    '''
    _METHOD_ = 'update_mgr.get_compliant_versions_tuples'

    versions_dict = stack_def_dict.get(device_type)
    if versions_dict == None:
        return (1, ('', ''), ('', ''),('')) # Not found in stack definition. device_type not supported in that PPIM release
    base = versions_dict.get(flrt_query.BASE_VERSION)
    
    base_fixes_list = get_fixes_details(versions_dict.get(flrt_query.BASE_VERSION_FIXES))
    
      
    if base == None:
        base = ''
    rec_update = versions_dict.get(flrt_query.UPDATE_VERSION)
    
    logging.info("%s:: UPDATE_VERSION_FIXES=%s", _METHOD_, versions_dict.get(flrt_query.UPDATE_VERSION_FIXES))
    
    rec_update_fixes_list = get_fixes_details(versions_dict.get(flrt_query.UPDATE_VERSION_FIXES))
    
    if not rec_update:
        rec_update = base
    
    #rec_upgrade = versions_dict.get(flrt_query.UPGRADE_VERSION)
    #if rec_upgrade == None:
    #    rec_upgrade = ''
    logging.debug("EXIT %s::result %s ", _METHOD_, str((0, (base, rec_update),(base_fixes_list, rec_update_fixes_list), (rec_update))));
    return (0, (base, rec_update), (base_fixes_list, rec_update_fixes_list), (rec_update))

def get_compliant_versions_details(stack_def_dict=None, device_type=None):
    ''' Return the tuple of all the compliant versions of devices of a device_type
    '''
    _METHOD_ = 'update_mgr.get_compliant_versions_details'

    versions_dict = stack_def_dict.get(device_type)
    if versions_dict == None:
        return ('','','','','','','','','') # Not found in stack definition. device_type not supported in that PPIM release
    base = versions_dict.get(flrt_query.BASE_VERSION)
    if base == None:
        base = ''
    base_link = versions_dict.get(flrt_query.BASE_LINK)
    if base_link == None:
        base_link = ''
        
    base_fixes_list = get_fixes_details(versions_dict.get(flrt_query.BASE_VERSION_FIXES))
    
    logging.info("%s:: base_fixes_list=%s", _METHOD_, base_fixes_list)
    
    rec_update = versions_dict.get(flrt_query.UPDATE_VERSION)
    update_link = versions_dict.get(flrt_query.UPDATE_LINK)
    if not rec_update:
        rec_update = base
        update_link = base_link
    if update_link == None:
        update_link = ''
        
    rec_update_fixes_list = get_fixes_details(versions_dict.get(flrt_query.UPDATE_VERSION_FIXES))
    
    rec_upgrade = versions_dict.get(flrt_query.UPGRADE_VERSION)
    if rec_upgrade == None:
        rec_upgrade = ''
    upgrade_link = versions_dict.get(flrt_query.UPGRADE_LINK)
    if upgrade_link == None:
        upgrade_link = ''
        
    upgrade_fixes_list = get_fixes_details(versions_dict.get(flrt_query.UPGRADE_VERSION_FIXES))

    return (base, base_link, base_fixes_list, rec_update, update_link, rec_update_fixes_list, rec_upgrade, upgrade_link, upgrade_fixes_list)

def is_ppim_entity(device):
    ''' Return true if the given device is an entity of management node.
    '''
    device_type = persistent_mgr.get_child_element_value(device, 'device-type')
    if (    device_type == constants.device_type.Nagios_Core.name
        or device_type == constants.device_type.Puremgr_Hypervisor.name
        or device_type == constants.device_type.Service_VM.name
        or device_type == constants.device_type.PowerVC.name
       ):
        return True
    return False

def divide_devices_into_racks(devices):
    ''' Given devices are divided in to racks based on rackid. Sorted based on rackid.
       Returns ordered dictionary with "rack"+rackid as key and the list of devices of that rack as value.
    '''
    racks = {} # ("rack"+rackid) is the dict key and the value is the list of devices of that rack
    for device in devices:
        rackid = persistent_mgr.get_child_element_value(device, 'rackid')
        rack = "rack" + rackid
        if rack in racks:
            racks["rack" + rackid].append(device)
        else:
            racks["rack" + rackid] = [device]

    sorted_racks = collections.OrderedDict(sorted(racks.items()))
    return sorted_racks

def put_mgmt_node_entities_together(devices_in_a_rack):
    ''' Returns the devices list by moving the management node entities to the front/beginning of the list.
       There is no ordering within the management node entities.
    '''
    mgmt_node_entities = []
    for device in devices_in_a_rack:
        if is_ppim_entity(device):
            mgmt_node_entities.append(device)

    result_list = mgmt_node_entities
    for device in devices_in_a_rack:
        if not is_ppim_entity(device): # if not in result_list
            result_list.append(device)
    return result_list

def change_devices_order(devices):
    ''' Changes the order of the devices such that
    (1) the devices are sorted based on rackid first and then
    (2) with in each rack, all PPIM entities are moved to the beginning of the devices list with in that rack. i.e. The dependent components are listed together/sequentially.
    '''
    _METHOD_ = 'update_mgr.change_devices_order'
    logging.info("ENTER %s:: Reordering the devices...",_METHOD_)

    racks = divide_devices_into_racks(devices)
    result_list = []
    for rack, devices_list in racks.items():
        rack_devices = put_mgmt_node_entities_together(devices_list)
        result_list.extend(rack_devices)

    return result_list

'''
If device_ids is specified, then the parameter labels will be ignored.
If puremgr_version is not specified, then the currently running puremgr version is used.
Ignores/skips devices of types which are unsupported -- for example: PDU.
'''
def assess_compliance(labels = None, device_ids = None, puremgr_version = None, for_all_devices = False):
    ''' Assess compliance of devices based on the firmware versions comparison with stack definition.
       labels: labels of the devices for which compliance assessment is to be done.
       device_ids: device_ids of devices for which compliance assessment is to be done.
       puremgr_version: the stack version against which compliance assessment to be done.
       for_all_devices: Boolean representing whether to do compliance assessment for all rack devices or not.
       Returns the list of tuples. Each tuple is like this:
       (label, device_id, device_type, ip, installed_version, base_version, base_link,
        recommented_update, update_link, recommended_upgrade, upgrade_link, compliance_status)
    '''
    _METHOD_ = 'update_mgr.assess_compliance'
    logging.info("ENTER %s:: Assessing compliance",_METHOD_)
    compliance_results = [] # list of tuples

    if puremgr_version == None:
        rc, puremgr_version = manage_nagios_core.get_version()

    doc = persistent_mgr.open_config_xml()

    devices, not_found_values = persistent_mgr.get_devices(doc, labels, device_ids, all_devices=for_all_devices)
    if devices == None or len(devices) == 0:
        logging.warning("%s:: No devices to assess compliance.",_METHOD_)
        return 0, compliance_results

    stack_def_dict = get_stack_definition(puremgr_version)
    if not stack_def_dict:
        logging.warning("%s:: Details required for compliance are not available for the purepower version %s.",_METHOD_, puremgr_version)
        return 116, _("Details required for compliance are not available for the purepower version %s") % puremgr_version

    devices = change_devices_order(devices)
    for device in devices:
        device_type = persistent_mgr.get_child_element_value(device, 'device-type')
        if device_type in COMPLIANCE_UNSUPPORTED_DEVICE_TYPES:
            logging.debug("%s:: Compliance for device type '%s' is not supported currently.",_METHOD_, device_type)
            continue

        label = persistent_mgr.get_child_element_value(device, 'label')
        device_id = persistent_mgr.get_child_element_value(device, 'deviceid')
        ip = persistent_mgr.get_child_element_value(device, 'ipv4-service-address')
        version = persistent_mgr.get_child_element_value(device, 'version')
        fixes =  persistent_mgr.get_child_element_value(device, 'fixes')
        fixes_list=ast.literal_eval(fixes)
        rackid = persistent_mgr.get_child_element_value(device, 'rackid')
        rack_location = persistent_mgr.get_child_element_value(device, 'rack-eia-location')

        base, base_link, base_fixes_list, update, update_link, update_fixes_list, upgrade, upgrade_link, upgrade_fixes_list = get_compliant_versions_details(stack_def_dict, device_type)
        if not update:
            update = base
            update_link = base_link

        compliance_status = do_assess_compliance(device_type, version, fixes_list, stack_def_dict)

        if compliance_status == Compliance_Status['compliant'] or compliance_status == Compliance_Status['status-not-available'] or compliance_status == Compliance_Status['unsupported-device-type']:
            base_fixes_list = get_active_links(base_fixes_list, [], True)
            update_fixes_list = get_active_links(update_fixes_list, [], True)
            upgrade_fixes_list = get_active_links(upgrade_fixes_list, [], True)
            base_link = ""
            update_link = ""
            upgrade_link = ""
        elif compliance_status == Compliance_Status['compliant-but-update-available']:
            base_fixes_list = get_active_links(base_fixes_list, [], True)
            base_link = ""
            update_fixes_list = get_active_links(update_fixes_list, fixes_list, False)
            upgrade_fixes_list = get_active_links(upgrade_fixes_list, fixes_list, False)
            if base == update:
                update_link = ""
        elif compliance_status == Compliance_Status['not-compliant']:
            base_fixes_list = get_active_links(base_fixes_list, fixes_list, False)
            update_fixes_list = get_active_links(update_fixes_list, fixes_list, False)
            upgrade_fixes_list = get_active_links(upgrade_fixes_list, fixes_list, False)
            if base == version:
                base_link = ""
            if update == version:
                update_link = ""
            if upgrade == version:
                upgrade_link = ""
        device_type = constants.device_type[device_type].value
        compliance_results.append((label, device_id, device_type, rackid, rack_location, ip, version, fixes_list, base, base_link, base_fixes_list, update, update_link, update_fixes_list, upgrade, upgrade_link, upgrade_fixes_list, compliance_status))

    return 0, compliance_results
def get_fixes_values(fixes_list_dict):
    fixes_list = []
    for each_value in fixes_list_dict:
        fixes_list.append(each_value["fix"]) 
    return fixes_list

def get_active_links(fixes_link_list, fix_names_list, all_values = False):
    '''it takes fixes_link_list as a list of dictionaries, each dictionary containings a 'fix' and 'fix_link' as key
    fix_names_list is a list of fix numbers of which fix links are to be removed
    if all_values = True, then remove all links    
    returns the resultant list of dictionary with only relevant links available'''
    _METHOD_ = 'update.mgr.get_active_links'
    logging.info("ENTER : %s", _METHOD_)

    fixes_active_links = copy.deepcopy(fixes_link_list)
    try:
        if fixes_link_list:
            if all_values == True:
                for each_dict in fixes_link_list:
                    each_dict['fix_link'] = ""
                return fixes_link_list
                
            for each_dict in fixes_link_list:
                if each_dict['fix'] in fix_names_list:
                    each_dict['fix_link'] = ""
                else:
                    continue
        return fixes_link_list
    except Exception as e:
        logging.error("Exception in %s >> Exception message : %s >>An error occured while handling a list of dictionary.", _METHOD_, e)
        return fixes_active_links

def do_assess_compliance(device_type = None, installed_version = None, installed_fixes = None, stack_def_dict = None):
    ''' Assess compliance of a device based on the firmware version comparison with stack definition.
       device_type: device_type of the device.
       installed_version: the version of firmware/software currently installed on the rack device.
       installed_fixes: the fixes of firmware/software currently installed on the rack device.
       stack_def_dict: Dictionary with device_type as key and compliant versions list as value.
       This method returns the compliance status value for the given device and installed_version.
    '''
    _METHOD_ = 'update_mgr.do_assess_compliance'
    logging.debug("ENTER::%s stack_def_dict is valid = %s, device_type = %s, installed_version = %s",_METHOD_, True if stack_def_dict else False, device_type, installed_version)
    if (stack_def_dict == None or not device_type):
        logging.warning("%s:: Information missing for assessing compliance.",_METHOD_)
        return Compliance_Status['status-not-available']

    # Assess compliance now.
    rc, compliant_versions, compliant_fixes, recommended_versions = get_compliant_versions_tuples(stack_def_dict, device_type)

    if rc == 0:
        base_version = compliant_versions[0]    
        base_fixes_list = get_fixes_values(compliant_fixes[0])
        recommended_fixes_list = get_fixes_values(compliant_fixes[1])

    if rc == 1:
        logging.warning("%s:: Device type '%s' is not available in the stack definition.",_METHOD_, device_type);
        status = Compliance_Status['unsupported-device-type']
    elif compliant_versions == None:
        logging.warning("%s:: Device type %s is not available in the stack definition.",_METHOD_, device_type);
        status = Compliance_Status['unsupported-device-type']
    elif not installed_version:
        status = Compliance_Status['status-not-available']
    elif installed_version not in compliant_versions:
        status = Compliance_Status['not-compliant']        
    elif installed_version in recommended_versions: 
        #base or recommended already matching with installed version; Here we are checking if recommended is matching with installed version
        if set(installed_fixes) == set(recommended_fixes_list):
            status = Compliance_Status['compliant']
        else:
            if base_version == installed_version:
                if set(base_fixes_list) == set(installed_fixes):
                    status = Compliance_Status['compliant-but-update-available']
                else:
                    status = Compliance_Status['not-compliant']
            else:
                status = Compliance_Status['not-compliant']
    else:
        status = Compliance_Status['not-compliant']
    logging.debug("EXIT %s::status %s ", _METHOD_, status);
    return status

def backup_and_overwrite_stack_definition_file(filename):
    _METHOD_= 'update_mgr.backup_and_overwrite_stack_definition_file'
    logging.info ("%s:: Enter - filename %s", _METHOD_, filename)
    rc = 0
    msg = ""
    if utils.is_file_valid(filename):
        #backup stack definition file to backup file right before replacing it
        shutil.copy(STACK_DEFINITIONS_FILE, STACK_DEFINITIONS_BACKUP_FILE)
        utils.change_file_ownership_and_permission(STACK_DEFINITIONS_BACKUP_FILE)

        #Overwrite stack definitions file
        shutil.copy(filename, STACK_DEFINITIONS_FILE)
        utils.change_file_ownership_and_permission(STACK_DEFINITIONS_FILE)
        logging.info ("%s:: Successfully copied the file %s to %s", _METHOD_, filename, STACK_DEFINITIONS_FILE)
        msg = "Successfully copied the file {} to {}".format(filename, STACK_DEFINITIONS_FILE)
    else:
        rc = 1
        logging.warning ("%s:: Operation failed as the retrieved stack definition file %s is invalid and hence not copied to %s", _METHOD_, filename, STACK_DEFINITIONS_FILE)
        msg = "Operation failed as the retrieved stack definition file %s is invalid and hence not copied to %s".format(filename, STACK_DEFINITIONS_FILE)
    logging.info ("%s:: Exit - filename %s", _METHOD_, filename)
    return rc, msg

def update_stack_definition():
    ''' Returns rc, msg. where rc could mean
      0 - Successful retrieval of stack from FLRT and overwriting the current stack definition file.
      1 - FLRT Connection related issues
      2 - FLRT response data related issues
      3 - Issues found during formatting data
      4 - Client issues, not sending values to FLRT correctly
      5 - Other Issues
      6 - FLRT Connection related issues from Proxy
      7 - Connection issues with Proxy
      8 - Proxy Authentication failure
      9 - FLRT in manual mode
    '''

    _METHOD_ = "update_mgr.update_stack_definition"
    logging.info ("%s:: Enter", _METHOD_)
    flrt_connection, ip_address, userid, password = get_flrt_mode_from_config()
    if flrt_connection == 'online':
        rc, msg, ppim_version_list = flrt_query.query_all_ppim_versions_from_flrt()
        if rc != 0:
            return rc, msg
        rc, msg, parsed_xml_response = flrt_query.query_mulitple_ppim_stacks_from_flrt(ppim_version_list)
        if rc != 0:
            return rc, msg

        rc, msg, filename = flrt_query.write_parse_xml_response_to_file(parsed_xml_response)
        if rc != 0:
            return rc, msg

        rc, msg = backup_and_overwrite_stack_definition_file(filename)
        if rc != 0:
            return rc, msg
        return (0, 'Successful')
    elif flrt_connection == 'proxy':
        rc, msg = validate_proxy_configuration(0, flrt_connection, ip_address, userid, password)
        return rc, msg
    else:
        return 9, 'FLRT Manual copy case'

def get_flrt_mode_from_config():
   _METHOD_="update_mgr.get_flrt_mode_from_config"
   flrt_connection = 'online'
   userid = None
   password = None
   ip_address = None

   flrt_connection = prop_file_utils.read_prop_from_config_file(flrt_query.UPDATES_COMPLIANCE_CONFIG_FILE, flrt_query.PROP_SECTION_COMPLIANCE, PROP_CONNECTION_TYPE)

   if flrt_connection == "proxy":
      ip_address = prop_file_utils.read_prop_from_config_file(flrt_query.UPDATES_COMPLIANCE_CONFIG_FILE, flrt_query.PROP_SECTION_COMPLIANCE, PROP_PROXY_MACHINE_IP)
      userid = prop_file_utils.read_prop_from_config_file(flrt_query.UPDATES_COMPLIANCE_CONFIG_FILE, flrt_query.PROP_SECTION_COMPLIANCE, PROP_PROXY_MACHINE_USERID)
      password = prop_file_utils.read_prop_from_config_file(flrt_query.UPDATES_COMPLIANCE_CONFIG_FILE, flrt_query.PROP_SECTION_COMPLIANCE, PROP_PROXY_MACHINE_ENCRYPTED_PASSWORD)
      password = persistent_mgr.decryptData(password)

   return (flrt_connection, ip_address, userid, password)

def get_offline_flrt_tarfile():
   ''' This method returns the filename of the tarfile that has to be copied to
       the remote machine with Internet. If the tarfile does not exist in the data
       folder, then the tarfile is created.

       returns rc, tarfile
   '''
   _METHOD_="update_mgr.get_offline_flrt_tarfile"
   #check if the file exists before creating again
   rc, ppim_version = manage_nagios_core.get_version()
   filename = '/opt/ibm/puremgr/data/offline_flrt_query_' + ppim_version + '.tar.gz'

   tar = None
   try:
       if os.path.isfile(filename):
           # Check if the tar file has latest contents, compare the timestamp of the contents and generate again if it is older
           create_tar_file = False
           tar_file_timestamp = os.path.getmtime(filename)
           for bundled_file in Offline_FLRT_files:
               bundled_file_timestamp = os.path.getmtime(bundled_file)
               if bundled_file_timestamp > tar_file_timestamp:
                   create_tar_file = True
                   break
           if not create_tar_file:               
               logging.debug("%s::Using existing tarfile %s", _METHOD_, filename)
               return (0, filename)
       tar = tarfile.open(filename, "w:gz")
       for name in Offline_FLRT_files:
           tar.add(name)
       utils.change_file_ownership_and_permission(filename)
   except Exception as e:
       logging.warning("%s:: Errors during creation of offline FLRT query tar file : %s", _METHOD_, e)
       return (1, None)
   finally:
       if tar:
           tar.close()
   logging.debug("%s::Tarfile generated as %s", _METHOD_, filename)
   return (0, filename)

def set_compliance_config(connection_type, remote_machine_ip=None, remote_machine_userid=None, remote_machine_password=None):
    ''' Updates the configuration file updates_compliance.properties with the PPIM connection type details and optionally
       the remote machine details, if required.
    '''
    _METHOD_ = "update_mgr.set_compliance_config"
    logging.info ("%s:: Enter", _METHOD_)

    rc = prop_file_utils.update_prop_in_config_file(flrt_query.UPDATES_COMPLIANCE_CONFIG_FILE, flrt_query.PROP_SECTION_COMPLIANCE, PROP_CONNECTION_TYPE, connection_type)
    if connection_type == 'proxy':
        rc = prop_file_utils.update_prop_in_config_file(flrt_query.UPDATES_COMPLIANCE_CONFIG_FILE, flrt_query.PROP_SECTION_COMPLIANCE, PROP_PROXY_MACHINE_IP, remote_machine_ip)
        if rc == 0:
            rc = prop_file_utils.update_prop_in_config_file(flrt_query.UPDATES_COMPLIANCE_CONFIG_FILE, flrt_query.PROP_SECTION_COMPLIANCE, PROP_PROXY_MACHINE_USERID, remote_machine_userid)
            if rc == 0:
                rc = prop_file_utils.update_prop_in_config_file(flrt_query.UPDATES_COMPLIANCE_CONFIG_FILE, flrt_query.PROP_SECTION_COMPLIANCE, PROP_PROXY_MACHINE_ENCRYPTED_PASSWORD, remote_machine_password)

    if rc == 0:
        msg = _("Successfully updated the configuration file.")
    else:
        msg = _("Failed to update the configuration file.")

    return rc, msg
def generate_stack_definition_remotely(remote_machine_ip, remote_machine_userid, remote_machine_password, remote_path):
    ''' Runs script on the remote machine and the script generates the stack definitions file
    '''
    _METHOD_ = "update_mgr.generate_stack_definition_remotely"
    logging.info ("%s:: Enter", _METHOD_)

    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(remote_machine_ip, username=remote_machine_userid, password=remote_machine_password, timeout=30)

        # Unarchive
        cmd = "tar -zxvf " + remote_path + " -C /tmp"
        (rc, msg) = sshUtils.runRemoteCommand(client, cmd)
        if (rc != 0):
            logging.error("%s::Failed to unarchive the package on the remote machine %s. returnCode=%d, ErrorMSg:%s", _METHOD_, remote_machine_ip, rc, msg)
            return 5
        cmd = "/usr/local/bin/python3.4 --version"
        (rc, msg) = sshUtils.runRemoteCommand(client, cmd)
        if (rc != 0):
            logging.error("%s::Failed to find Python 3.4 using command %s, on the remote machine %s. returnCode=%d, ErrorMSg:%s", _METHOD_, cmd, remote_machine_ip, rc, msg)
            return 5

        # Run the script on the remote machine
        cmd = "cd /tmp/" + BIN_DIR_PATH + ";./generate_stack_definition  >>/var/log/puremgr_compliance.log 2>&1"
        (rc, msg) = sshUtils.runRemoteCommand(client, cmd)
        return rc

    except paramiko.AuthenticationException:
        logging.error("%s::userid/password combination not valid. address=%s userid=%s", _METHOD_, remote_machine_ip, remote_machine_userid)
        return 8
    except socket.timeout:
        logging.error("%s::Connection timed out. Address=%s", _METHOD_, remote_machine_ip)
        return 7
    except TimeoutError:
        logging.error("%s::Connection timed out. Address=%s", _METHOD_, remote_machine_ip)
        return 7
    except Exception as ex:
        logging.error("%s::Exception seen. Address=%s; Exception is %s", _METHOD_, remote_machine_ip, ex)
        return 5
    finally:
        client.close()

def restore_stack_definition_file():
    ''' Attempts to restore the stack definitions file by backing up the corrupt stack definitions file
        and then replacing the stack definitions file with the backup json file
        Returns the status as
        True - if successfully restored.
        False - if failed to restore the json from backup.
    '''
    _METHOD_ = "update_mgr.restore_stack_definition_file"
    logging.info ("%s:: Enter", _METHOD_)
    try:
        if(os.path.isfile(STACK_DEFINITIONS_FILE)):
            #Backup corrupt file for debugging
            shutil.copy(STACK_DEFINITIONS_FILE, STACK_DEFINITIONS_CORRUPT_FILE)
            utils.change_file_ownership_and_permission(STACK_DEFINITIONS_CORRUPT_FILE)
            logging.debug ("%s:: Successfully backed up the corrupt stack definitions file to %s", _METHOD_, STACK_DEFINITIONS_CORRUPT_FILE)
    except IOError as e:
        logging.warning ("%s:: Error while making backup of corrupt stack definitions file :%s", _METHOD_, str(e))
        #not raising error, letting restoration carry on even if corrupt file can not be backed up
    try:
        #check if there is a backup file
        if(not utils.is_file_valid(STACK_DEFINITIONS_BACKUP_FILE)):
            #copy default file to backup file - assuming the default file is always present
            shutil.copy(STACK_DEFINITIONS_DEFAULT_FILE, STACK_DEFINITIONS_BACKUP_FILE)
            utils.change_file_ownership_and_permission(STACK_DEFINITIONS_BACKUP_FILE)
            logging.debug ("%s:: Successfully copied %s to %s", _METHOD_, STACK_DEFINITIONS_DEFAULT_FILE, STACK_DEFINITIONS_BACKUP_FILE)

        #Overwrite stack definitions file with backup file
        shutil.copy(STACK_DEFINITIONS_BACKUP_FILE, STACK_DEFINITIONS_FILE)
        utils.change_file_ownership_and_permission(STACK_DEFINITIONS_FILE)
        logging.warning ("%s:: Successfully restored the stack definitions file to %s", _METHOD_, STACK_DEFINITIONS_FILE)

    #source or destination doesn't exist
    except IOError as e:
        logging.warning ("%s:: Error while restoring stack definitions file from backup : %s", _METHOD_, str(e))
        return False

    return True

def get_compliance_config():
    ''' Reads compliance configuration from config file
    '''
    _METHOD_ = "update_mgr.get_compliance_config"
    logging.info ("%s:: Enter", _METHOD_)
    properties_dict = {}
    properties_dict = prop_file_utils.read_props_from_config_file(flrt_query.UPDATES_COMPLIANCE_CONFIG_FILE, flrt_query.PROP_SECTION_COMPLIANCE)
    return (0,properties_dict)

def update_compliance_config(connection_type, remote_machine_ip=None, remote_machine_userid=None, remote_machine_password=None):
    ''' Updates the configuration file updates_compliance.properties with the PPIM connection type details and optionally
        the remote machine details, if required.
        Returns rc, msg. where rc could mean
        0 - Successful updation of the configuration file.
        1 - Issue is reading/writing configuration form file
    '''
    _METHOD_ = "update_mgr.set_compliance_config"
    logging.info ("%s:: Enter", _METHOD_)
    logging.info("ENTER %s::update_compliance_config - connection_type=%s, remote_machine_ip=%s, remote_machine_userid=%s, remote_machine_password=%s.", _METHOD_, connection_type, remote_machine_ip, remote_machine_userid, remote_machine_password);
    
    rc = prop_file_utils.update_prop_in_config_file(flrt_query.UPDATES_COMPLIANCE_CONFIG_FILE, flrt_query.PROP_SECTION_COMPLIANCE, PROP_CONNECTION_TYPE, connection_type)
    if connection_type == 'proxy':
        rc = prop_file_utils.update_prop_in_config_file(flrt_query.UPDATES_COMPLIANCE_CONFIG_FILE, flrt_query.PROP_SECTION_COMPLIANCE, PROP_PROXY_MACHINE_IP, remote_machine_ip)
        if rc == 0:
            rc = prop_file_utils.update_prop_in_config_file(flrt_query.UPDATES_COMPLIANCE_CONFIG_FILE, flrt_query.PROP_SECTION_COMPLIANCE, PROP_PROXY_MACHINE_USERID, remote_machine_userid)
            if rc == 0:
                remote_machine_encrypted_password = persistent_mgr.encryptData(remote_machine_password)
                rc = prop_file_utils.update_prop_in_config_file(flrt_query.UPDATES_COMPLIANCE_CONFIG_FILE, flrt_query.PROP_SECTION_COMPLIANCE, PROP_PROXY_MACHINE_ENCRYPTED_PASSWORD, remote_machine_encrypted_password)

    if rc == 0 and connection_type != 'proxy':
        return (0, "Successfully updated the configuration file.")
    elif rc != 0 and connection_type != 'proxy':
        return (1,"Failed to update the configuration file.")

    rc, msg=validate_proxy_configuration(rc, connection_type, remote_machine_ip, remote_machine_userid, remote_machine_password)
    return rc, msg

def validate_proxy_configuration(prev_rc, connection_type, remote_machine_ip, remote_machine_userid, remote_machine_password):
    ''' This method generates the stack definition in the remote Machine
      Returns rc, msg. where rc could mean
      0 - Successful retrieval of stack from FLRT and overwriting the current stack definition file.
      1 - FLRT Connection related issues
      2 - FLRT response data related issues
      3 - Issues found during formatting data
      4 - Client issues, not sending values to FLRT correctly
      5 - Other Issues
      6 - FLRT Connection related issues from Proxy
      7 - Connection issues with Proxy
      8 - Proxy Authentication failure
      9 - FLRT in manual mode
    '''
    _METHOD_ = "update_mgr.validate_proxy_configuration"
    if prev_rc == 0 and connection_type == 'proxy':
        # Create package if not already there
        rc, local_path = get_offline_flrt_tarfile()
        if rc == 0:
            # Copy the package to the remote/online machine
            pkg_name = utils.get_filename_from_path(local_path)
            remote_path = "/tmp/" + pkg_name
            rc = utils.copyFileToRemoteMachine(remote_machine_ip, remote_machine_userid, remote_machine_password, local_path, remote_path)
            if rc == 0:
                # Run script on the remote machine and the script generates the stack definitions file
                rc = generate_stack_definition_remotely(remote_machine_ip, remote_machine_userid, remote_machine_password, remote_path)
                if rc == 0:
                    # Copy the generated stack definitions file from the remote machine to puremgrVM
                    rc= utils.copyFileFromRemoteMachine(remote_machine_ip, remote_machine_userid, remote_machine_password, STACK_DEFINITIONS_PROXY_TMP_FILE, STACK_DEFINITIONS_TMP_FILE)
                    utils.change_file_ownership_and_permission(STACK_DEFINITIONS_PROXY_TMP_FILE)

                    if rc == 0:
                        rc, msg = backup_and_overwrite_stack_definition_file(STACK_DEFINITIONS_PROXY_TMP_FILE)
                        if rc == 0:
                            return(0,"Stack definition generated successfully in the remote machine")
                    else:
                        return (7,"Could not copy remote file to local machine")
                elif rc == 5:
                    return(10, "Failed to find Python 3.4 on the remote machine")
                elif rc == 8:
                    return(8, "Remote machine userid/password combination not valid")
                else:
                    return(6,"Stack definition file could not be generated in the remote machine")
            elif rc == 2:
                return(8, "Remote machine userid/password combination not valid")   
            else:
                return(7,"Could not copy file to remote machine")
        else:
            logging.error("%s:: Issues during creation of tarfile", _METHOD_)
            return(5,"Tar file is not generated successfully")
    else:
        logging.error("%s:: Connection type is not proxy", _METHOD_)
        return(9,"Connection type is not proxy")
