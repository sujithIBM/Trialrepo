#!/usr/local/bin/python3.4
# Licensed Materials - Property of IBM
#
# (C) Copyright IBM Corp. 2015 All Rights Reserved
#
# US Government Users Restricted Rights - Use, duplicate or
# disclosure restricted by GSA ADP Schedule Contract with
# IBM Corp.

import simplejson
import logging
import update_mgr
import rest_server_util
import manage_nagios_core


class RestServerUpdateController(object):
    def parse_assess_compliance_result_to_dic(self, parse_str, flrt_last_updated_date):
        _METHOD_ = 'parse_assess_compliance_result_to_dic'
        compliant_version_dict = {}
        compliant_version_list = []
        flrt_updated_date_dict = {}
        compliance_result_dict = {}
        compliance_result_list = []
        result_dict = {}

        if parse_str == '' or flrt_last_updated_date == '':
            result_dict['items'] = compliance_result_list
            result_dict['label'] = 'name'
            result_dict['identifier'] = 'id'
            return result_dict
        
        flrt_updated_date_dict['flrt_last_updated_date'] = flrt_last_updated_date
        compliance_result_list.append(flrt_updated_date_dict.copy())
        flrt_updated_date_dict.clear()

        for line in parse_str:
            logging.info("entered into parsing..:%s",line)
            try:
                label, device_id, device_type, rackid, rack_location, ip_address, installed_version, base_version, base_link, recommended_update, update_link, recommended_upgrade, upgrade_link, compliance_status = line
            except Exception as e:
                raise e
            
            compliant_version_dict['label'] = label
            compliant_version_dict['id'] = device_id
            compliant_version_dict['device_type'] = device_type
            compliant_version_dict['rackid'] = rackid
            compliant_version_dict['rack_location'] = rack_location
            compliant_version_dict['mgmtIpaV4'] = ip_address
            compliant_version_dict['installed_version'] = installed_version
            compliant_version_dict['base_version'] = base_version
            compliant_version_dict['base_link'] = base_link
            compliant_version_dict['recommended_update'] = recommended_update
            compliant_version_dict['update_link'] = update_link
            compliant_version_dict['recommended_upgrade'] = recommended_upgrade
            compliant_version_dict['upgrade_link'] = upgrade_link
            compliant_version_dict['compliance_status'] = compliance_status
            
            compliant_version_list.append(compliant_version_dict.copy())            
            compliant_version_dict.clear()
          
        compliance_result_dict["compliance_results"] = compliant_version_list
        compliance_result_list.append(compliance_result_dict.copy())
        compliance_result_dict.clear()
        
        result_dict['items'] = compliance_result_list
        result_dict['label'] = 'name'
        result_dict['identifier'] = 'id'

        return result_dict
        
    def parse_collect_versions_inventory_result_to_dic(self, parse_str):
        _METHOD_ = 'parse_collect_versions_inventory_result_to_dic'
        version_dict = {}
        version_list = []
        result_dict = {}
        return_code = 200
        #HTTP return code 
        #200 for succesfull prcessing of all devices
        #206 for partial content
        #204 for empty content
        if parse_str == '':
            result_dict['items'] = version_list
            result_dict['label'] = 'name'
            result_dict['identifier'] = 'id'
            return 204, result_dict

        for line in parse_str:
            logging.info("entered into parsing..:%s",line)
            try:
                if isinstance(line, tuple):
                    rc, label, device_id, device_type, ip_address, version, fixes = line
                    if rc != 0:
                        return_code = 206   # At least one device firmware/software version could not be retrieved
                    version_dict['rc'] = rc
                    version_dict['label'] = label
                    version_dict['id'] = device_id
                    version_dict['device_type'] = device_type
                    version_dict['mgmtIpaV4'] = ip_address
                    version_dict['installed_version'] = version
                    version_dict['fixes'] = str(fixes)

                    version_list.append(version_dict.copy())
                    version_dict.clear()                        
                else:
                   return_code = 204  # May be some issue in update_mgr.collect_versions_inventory() like "no devices found"
            except Exception as e:
                raise e

        result_dict['items'] = version_list
        result_dict['label'] = 'name'
        result_dict['identifier'] = 'id'

        return return_code, result_dict
    
    
    def parse_compliance_config_result_to_dic(self, parse_str):
        _METHOD_ = 'parse_compliance_config_result_to_dic'
        compliance_result_dict = parse_str
        compliance_result_list = []
        result_dict = {}

        if parse_str == '':
            result_dict['items'] = compliance_result_list
            result_dict['label'] = 'name'
            result_dict['identifier'] = 'id'
            return result_dict
        
        compliance_result_list.append(compliance_result_dict.copy())            
        compliance_result_dict.clear()
        
        result_dict['items'] = compliance_result_list
        result_dict['label'] = 'name'
        result_dict['identifier'] = 'id'

        return result_dict
        
    
    def collect_versions_inventory(self, **arg):
        _METHOD_ = 'RestServerUpdateController.collect_versions_inventory'
        '''
        https://w3-connections.ibm.com/wikis/home?lang=en-us#!/wiki/W9db7698ce9ad_4a8a_9663_da15857f726e/page/POST%20collect_versions_inventory
        '''

        labels = ''
        all_devices = False
        deviceids = None
        ppim_version = None
        rack_id = None

        text_json = arg['content']
        if text_json == '':
            return (400, rest_server_util._generate_general_REST_failure_response())
        try:
            dict_json = simplejson.loads(text_json)
        except KeyError:
            logging.warning("%s: Key content is not found in text_json", _METHOD_)
            pass
        try:
            labels = dict_json['labels']
        except KeyError:
            logging.info("%s: Key labels is not found in text_json", _METHOD_)
            pass
        try:
            all_devices = dict_json['all_devices']
        except KeyError:
            logging.info("%s: Key all_devices is not found in text_json", _METHOD_)
            pass
        try:
            deviceids = dict_json['ids']
        except KeyError:
            logging.info("%s: Key deviceids is not found in text_json", _METHOD_)
            pass
        try:
            ppim_version = dict_json['version']
        except KeyError:
            logging.info("%s: Key ppim version is not found in text_json", _METHOD_)
            pass
        try:
            rack_id = dict_json['rack_id']
        except KeyError:
            logging.info("%s: Key rack_id version is not found in text_json", _METHOD_)
            pass

        
        if labels == '' and all_devices == False and deviceids == None and ppim_version == None and rack_id == None:
            return (400, rest_server_util._generate_general_REST_failure_response())
        # TODO  NOTE: The following special values are being considered for enhancement after GA1...
        # "*ALL_TYPE1" = indicates all type 1 elements (PowerVC)
        if deviceids == '*ALL':
            all_devices = True
            deviceids = None
        try:
            logging.debug("From %s: calling collect_versions_inventory",_METHOD_)
            version_inventory = update_mgr.collect_versions_inventory(labels,deviceids,all_devices,rack_id)
            return_code, result_dict = RestServerUpdateController.parse_collect_versions_inventory_result_to_dic(self, version_inventory)
            result = simplejson.dumps(result_dict)
            return (return_code, result)
        except Exception as e:
            logging.error("From %s: update_mgr.collect_versions_inventory exception:%s", _METHOD_ , e)
            return (500, rest_server_util._generate_general_REST_failure_response())
        
    def list_ppim_versions(self, **arg):
    
        _METHOD_ = 'RestServerUpdateController.list_ppim_versions'
        '''
        https://w3-connections.ibm.com/wikis/home?lang=en-us#!/wiki/W9db7698ce9ad_4a8a_9663_da15857f726e/page/GET%20list_ppim_versions
        '''
        try:
            rc, current_version = manage_nagios_core.get_version()
            versions = update_mgr.get_all_ppim_versions()

            # sort the versions and delete versions lesser than the current ppim version
            versions.sort()
            while len(versions) > 0:
                version = versions[0]
                if version != current_version:
                    versions.remove(version)
                else:
                    break

            result_dict = {}
            result_dict['items'] = versions
            result_dict['label'] = 'name'
            result_dict['identifier'] = 'id'
            result = simplejson.dumps(result_dict)
            return (200, result)
        except Exception as e:
            logging.error("From %s: update_mgr.get_all_ppim_versions exception:%s", _METHOD_ , e)
            return (500, rest_server_util._generate_general_REST_failure_response())        
    
    def assess_compliance(self, **arg):
        _METHOD_ = 'RestServerUpdateController.assess_compliance'
        '''
        https://w3-connections.ibm.com/wikis/home?lang=en-us#!/wiki/W9db7698ce9ad_4a8a_9663_da15857f726e/page/POST%20assess_compliance
        '''

        labels = None
        deviceids = None
        rc, puremgr_version = manage_nagios_core.get_version()
        for_all_devices = False

        text_json = arg['content']
        if text_json:
            try:
                dict_json = simplejson.loads(text_json)
            except KeyError:
                logging.warning("%s: Key content is not found in text_json", _METHOD_)
                dict_json = {}
                pass
            try:
                labels = dict_json['labels']
            except KeyError:
                logging.info("%s: Key labels is not found in text_json", _METHOD_)
                pass
            try:
                deviceids = dict_json['ids']
            except KeyError:
                logging.info("%s: Key deviceids is not found in text_json", _METHOD_)
                pass
            try:
                puremgr_version = dict_json['version']
            except KeyError:
                logging.info("%s: Key version is not found in text_json", _METHOD_)
                pass
            try:
                for_all_devices = dict_json['all_devices']
            except KeyError:
                logging.info("%s: Key all_devices is not found in text_json", _METHOD_)
                pass
        if not labels and not deviceids:
            for_all_devices = True


        try:
            rc, result = update_mgr.assess_compliance(labels,deviceids,puremgr_version,for_all_devices)
            flrt_last_updated_date = update_mgr.get_date_from_stack_definition_file()
            logging.info("flrt last queried date ====%s",flrt_last_updated_date)
            if rc == 0:
                result = simplejson.dumps(RestServerUpdateController.parse_assess_compliance_result_to_dic(self, result, flrt_last_updated_date))
                return (200, result)
            if rc == 115 or rc == 116:
                return (500, result)
        except Exception as e:
            logging.error("From %s: update_mgr.assess_compliance exception:%s", _METHOD_ , e)
            return (500, rest_server_util._generate_general_REST_failure_response())

    def query_stack_definitions(self, **arg):
        _METHOD_ = 'RestServerUpdateController.query_stack_definitions'
        '''
        https://w3-connections.ibm.com/wikis/home?lang=en-us#!/wiki/W9db7698ce9ad_4a8a_9663_da15857f726e/page/GET%20query_stack_definitions
        '''
        
        try:
            rc, msg_from_flrt = update_mgr.update_stack_definition()
            logging.info("%s::msg from flrt====%s",_METHOD_, msg_from_flrt)

            result_dict = {}
            result_dict['items'] = msg_from_flrt
            result_dict['label'] = 'name'
            result_dict['identifier'] = 'id'
            if rc == 0:
                result = simplejson.dumps(result_dict)
                return (200, result)
            elif rc == 1: # FLRT Connection related issues
                return (501, msg_from_flrt)
            elif rc == 2: # FLRT response data related issues
                return (520, msg_from_flrt)
            elif rc == 3: # Issues found during formatting data
                return (520, msg_from_flrt)
            elif rc == 4: # Client issues, not sending values to FLRT correctly
                return (400 , msg_from_flrt)
            elif rc == 5: # other issues
                return (500, msg_from_flrt)
            elif rc == 6: # FLRT Connection related issues from Proxy
                return (512, msg_from_flrt)
            elif rc == 7: # Connection issues with Proxy
                return (513, msg_from_flrt)
            elif rc == 8: # Proxy Authentication failure
                return (511 , msg_from_flrt) 
            else: # FLRT in manual mode
                return (406 , msg_from_flrt)

        except Exception as e:
            logging.error("From %s: flrt_query.update_stack_definition:%s", _METHOD_ , e)
            return (500, rest_server_util._generate_general_REST_failure_response())


    def current_compliance_config(self, **arg):
        _METHOD_ = 'RestServerUpdateController.current_compliance_config'
        '''
        https://w3-connections.ibm.com/wikis/home?lang=en-us#!/wiki/W9db7698ce9ad_4a8a_9663_da15857f726e/page/POST%20current_compliance_config
        '''
        
        try:
            logging.warning("%s: Key content is not found in text_json", _METHOD_)
            rc, current_compliance_config = update_mgr.get_compliance_config()
            result = simplejson.dumps(RestServerUpdateController.parse_compliance_config_result_to_dic(self, current_compliance_config))
            return (200, result)
        except Exception as e:
            logging.error("From %s: update_mgr.current_compliance_config exception:%s", _METHOD_ , e)
            return (500, rest_server_util._generate_general_REST_failure_response())        
    
    
    def update_compliance_config(self, **arg):
        _METHOD_ = 'RestServerUpdateController.update_compliance_config'
        '''
        https://w3-connections.ibm.com/wikis/home?lang=en-us#!/wiki/W9db7698ce9ad_4a8a_9663_da15857f726e/page/POST%20update_compliance_config
        '''
        
        flrt_connection_type = 'online'
        proxy_machine_ip = None
        proxy_machine_userid = None
        proxy_machine_encrypted_password = None

        text_json = arg['content']
        if text_json == '':
            return (400, rest_server_util._generate_general_REST_failure_response())
        try:
            dict_json = simplejson.loads(text_json)
        except KeyError:
            logging.warning("%s: Key content is not found in text_json", _METHOD_)
            pass
        try:
            flrt_connection_type = dict_json['connection_type']
        except KeyError:
            logging.info("%s: Key flrt_connection_type is not found in text_json", _METHOD_)
            pass
        try:
            proxy_machine_ip = dict_json['proxyIpaV4']
        except KeyError:
            logging.info("%s: Key proxy machine ip is not found in text_json", _METHOD_)
            pass
        try:
            proxy_machine_userid = dict_json['userid']
        except KeyError:
            logging.info("%s: Key proxy machine userid is not found in text_json", _METHOD_)
            pass
        try:
            proxy_machine_encrypted_password = dict_json['password']
        except KeyError:
            logging.info("%s: Key proxy machine encrypted password is not found in text_json", _METHOD_)
            pass

        try:
            logging.debug("From %s: calling update_compliance_config",_METHOD_)
            rc,msg= update_mgr.update_compliance_config(flrt_connection_type, proxy_machine_ip, proxy_machine_userid, proxy_machine_encrypted_password)
            result_dict = {}
            result_dict['items'] = msg
            result_dict['label'] = 'name'
            result_dict['identifier'] = 'id'
            if rc == 0:
                result = simplejson.dumps(result_dict)
                return (200, result)
            elif rc == 1: # Compliance settings related issues
                return (501, msg)
            elif rc == 2: # FLRT response data related issues
                return (520, msg)
            elif rc == 3: # Issues found during formatting data
                return (520, msg)
            elif rc == 4: # Client issues, not sending values to Compliance settings correctly
                return (400 , msg)
            elif rc == 5: # other issues
                return (500, msg)
            elif rc == 6: # Compliance settings issues from Proxy
                return (512, msg)
            elif rc == 7: # Connection issues with Proxy
                return (513, msg)
            elif rc == 8: # Proxy Authentication failure
                return (511,msg)
            elif rc == 10: # Failed to find Python 3.4 on the remote machine
                return (514, msg)
            else: # Compliance is in manual/offline mode
                return (406 , msg)
        except Exception as e:
            logging.error("From %s: update_mgr.update_compliance_config exception:%s", _METHOD_ , e)
            return (500, rest_server_util._generate_general_REST_failure_response())
