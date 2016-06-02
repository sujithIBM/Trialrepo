#!/usr/local/bin/python3.4
# Licensed Materials - Property of IBM
#
# (C) Copyright IBM Corp. 2015 All Rights Reserved
#
# US Government Users Restricted Rights - Use, duplicate or
# disclosure restricted by GSA ADP Schedule Contract with
# IBM Corp.

import constants
import paramiko
import socket
import logging
import os
import time
from IpInterface import IpInterface

ENABLE_COMMAND="\nenable\n"
CONFIGURE_TERMINAL_COMMAND="configure terminal\n"
SHOW_INVENTORY_COMMAND="show inventory\n"
SNMP_V2_TRAP_SUBSCRIBE_COMMAND="snmp host "
SNMP_V2_TRAP_NOTIFY_COMMAND="snmp notify community "
SNMP_V2_TRAP_UNSUBSCRIBE_COMMAND="no snmp host "
SHOW_SNMP_HOST_COMMAND="show snmp host\n"
CHASSIS_INFORMATION="CHASSIS"
COMMAND_NOT_FOUND="command not found"
SHOW_INTERFACE_COMMAND="show interface "
SHOW_IP_ROUTE_COMMAND="show ip route\n"
DEFAULT_GATEWAY_COMMAND="ip route 0.0.0.0 0.0.0.0 "
IP_ADDRESS_TAG="IP address:"
NETMASK_TAG="Netmask:"
DEFAULT_TAG="default"
MLAG_VIP_QUALIFIER="mlag-vip"
SHOW_MLAG_VIP_COMMAND="show run | include mlag-vip\n"
INTERFACE_SHUTDOWN_COMMAND="shutdown\n"
EXIT_COMMAND="exit\n"
TEMP_HACK_FILE_DIR="/opt/ibm/puremgr/data/"
GET_VERSION_COMMAND="show version | include release\n"
CURRENT_VERSION_TAG="release"

def getType():
    return constants.device_type.Mellanox_Switch

def getManagementType():
    return constants.management_type.Hardware

def getWebURL(address):
    return "https://" + address
    
def getIPfromInterface(client_shell, interface):
    _METHOD_ = "manage_mellanox_switch.getIPfromInterface"
    client_shell.send(SHOW_INTERFACE_COMMAND + interface + "\n")
    time.sleep(2) #waiting for command to complete
    output=client_shell.recv(1000)
    logging.info(SHOW_INTERFACE_COMMAND + interface + "\n")
    output_str=output.decode('ascii')
    logging.debug(output_str)
    client_shell.send("q\n")#Dummy command
    for line in output_str.splitlines():
        #Parse the output for IP address and netmask
        if (IP_ADDRESS_TAG in line):
            if len(line.split()) > 2:
                configured_ip=line.split()[2]
                if (configured_ip.strip() != None or configured_ip.strip()!= ''):
                    logging.info("%s:: Found IP address %s for %s interface.", _METHOD_, configured_ip, interface)
                    return configured_ip
    logging.debug("%s:: No IP address found for %s interface.", _METHOD_, interface)
    return None 
    
def shutdownInterface(client_shell, interface):
    _METHOD_ = "manage_mellanox_switch.shutdownInterface"
    client_shell.send("interface " + interface + "\n")
    time.sleep(2) #waiting for command to complete
    output=client_shell.recv(1000) 
    logging.info("%s::Command Sent : interface %s\n", _METHOD_, interface)
    logging.debug(output.decode('ascii'))
    client_shell.send(INTERFACE_SHUTDOWN_COMMAND)
    time.sleep(2) #waiting for command to complete
    logging.info("%s::Command Sent : %s",_METHOD_, INTERFACE_SHUTDOWN_COMMAND)
    if client_shell.recv_ready() == True:
        output=client_shell.recv(1000) 
    else:
        logging.info("%s::Hang during receive",_METHOD_)
        return
    logging.debug(output.decode('ascii'))
    client_shell.send(EXIT_COMMAND)
    time.sleep(2) #waiting for command to complete
    output=client_shell.recv(1000) 
    logging.info("%s::Command Sent : %s",_METHOD_, EXIT_COMMAND)
    logging.debug(output.decode('ascii'))

def unShutdownInterface(client_shell, interface):
    _METHOD_ = "manage_mellanox_switch.UNshutdownInterface"
    client_shell.send("interface " + interface + "\n")
    time.sleep(2) #waiting for command to complete
    output=client_shell.recv(1000) 
    logging.info("%s::Command Sent : interface %s\n", _METHOD_, interface)
    logging.debug(output.decode('ascii'))
    client_shell.send("no " + INTERFACE_SHUTDOWN_COMMAND)
    logging.info("%s::Command Sent : no %s",_METHOD_, INTERFACE_SHUTDOWN_COMMAND)
    time.sleep(2) #waiting for command to complete
    if client_shell.recv_ready() == True:
        output=client_shell.recv(1000) 
    else:
        logging.info("%s::Hang during receive",_METHOD_)
        return
    logging.debug(output.decode('ascii'))
    client_shell.send(EXIT_COMMAND)
    time.sleep(2) #waiting for command to complete
    output=client_shell.recv(1000) 
    logging.info("%s::Command Sent : %s",_METHOD_, EXIT_COMMAND)
    logging.debug(output.decode('ascii'))
    
def writeMgmtHack(new_ip_address, interface):
    _METHOD_ = "manage_mellanox_switch.writeMgmtHack"
    filename = TEMP_HACK_FILE_DIR +"." + new_ip_address + "_mellanox"
    file = None
    try:
        file = open(filename,'w')   # Trying to create a new file or open one
        logging.debug("%s::File created %s", _METHOD_, filename)
        file.write(interface)
        logging.debug("%s::Interface added to file as %s", _METHOD_, interface)
    except Exception as e:
        logging.warning("%s::Exception during file creation/updating %s : %s", _METHOD_, filename, e)
    finally:
        if file != None:
            file.close()    

def validate(address, userid, password):
    """
    returns return code, machine_type_model, serial_number, version for rc=0
    otherwise returns return code, None, None, None
    Return 0 - Success
    Return 1 - failed to connect
    Return 2 - userid/password invalid
    Return 3 - not Mellanox
    """

    _METHOD_="manage_mellanox_switch.validate"
    machine_type_model = None
    serial_number = None

    logging.info("ENTER %s::address=%s userid=%s",_METHOD_,address,userid)
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(address, username=userid, 
                       password=password, timeout=30)
        client_shell = client.invoke_shell()

        client_shell.send(ENABLE_COMMAND)
        time.sleep(2) #waiting for command to complete
        output=client_shell.recv(1000) 
        logging.info("Command Sent : " + ENABLE_COMMAND)
        logging.debug(output.decode('ascii'))

        client_shell.send(SHOW_INVENTORY_COMMAND)
        time.sleep(2)
        output=client_shell.recv(5000)
        logging.info("Command Sent : " + SHOW_INVENTORY_COMMAND)
        output_str=output.decode('ascii')
        logging.debug(output_str)
        for line in output_str.splitlines():
            #Parse the output for machine type model and serial number
            if (line.startswith(CHASSIS_INFORMATION)):
                machine_type_model=line.split()[1]
                serial_number=line.split()[3]
                
        client_shell.send("q\n")#Dummy command        
        additional_interfaces = []
        
        # find the MLAG-VIP to add to additional IP interfaces
        client_shell.send(SHOW_MLAG_VIP_COMMAND)
        time.sleep(5)
        output=client_shell.recv(5000)
        logging.info("Command Sent : " + SHOW_MLAG_VIP_COMMAND)
        output_str=output.decode('ascii')
        logging.debug(output_str)
        for line in output_str.splitlines():
            #Parse the output for machine type model and serial number
            if (line.strip().startswith("mlag-vip")):
                #check if the MLAG VIP is configured on this maching or on the peer.
                if (len(line.split()) > 3):
                    #VIP is configured on this switch
                    mlag_vip = line.split()[3]
                    additional_ip_interface = IpInterface(constants.interface_ip_type.IPv4 , MLAG_VIP_QUALIFIER,constants.network_interface_type.Service, mlag_vip)
                    additional_ip_interface.setSharingAllowed(True)
                    additional_interfaces.append(additional_ip_interface)
         
        # Find the additional MGMT IP configured on this device which could be mgmt0 or mgmt1
        interface='mgmt1'
        configured_ip = getIPfromInterface(client_shell, interface)
        if configured_ip != None:
            if configured_ip == address:
                logging.info("%s:: mgmt1 is the management interface, mgmt0 could be the additional interface.", _METHOD_)
                interface='mgmt0'
                client_shell.send("q\n")#Dummy command
                configured_ip = getIPfromInterface(client_shell, interface)
                if configured_ip != None:
                    logging.info("%s:: Adding additional interface %s with IP %s", _METHOD_, interface, configured_ip)
                    additional_mgmt_interface = IpInterface(constants.interface_ip_type.IPv4, interface, constants.network_interface_type.AdditionalPorts, configured_ip)
                    additional_interfaces.append(additional_mgmt_interface)
            else:
                logging.info("%s:: Adding additional interface %s with IP %s", _METHOD_, interface, configured_ip)
                additional_mgmt_interface = IpInterface(constants.interface_ip_type.IPv4, interface, constants.network_interface_type.AdditionalPorts, configured_ip)
                additional_interfaces.append(additional_mgmt_interface)
                
        if machine_type_model is None:
            logging.warning(
                "%s::Device is not a Mellanox switch. address=%s useridf=%s"
                ,_METHOD_,address,userid)
            return (3, None, None, None, None)
        else:
            (rc, version) = get_version(address, userid, password)
            logging.info("%s::Device is a Mellanox switch. Machine Model:%s, Serial_Num:%s, Version:%s",
                _METHOD_,machine_type_model,serial_number,version)
            return (0, machine_type_model, serial_number, version, additional_interfaces)
    except paramiko.AuthenticationException:
        logging.error("%s::userid/password combination not valid. address=%s userid=%s",
                _METHOD_,address,userid)
        return (2, None, None, None, None)
    except socket.timeout:
        logging.error("%s::Connection timed out. Address=%s",_METHOD_,address)
        return (1, None, None, None, None)
    finally:
        client.close()

def subscribe(address,userid,password,receiver_address,community='public'):
    """ Configures the switch to send traps to a host
    Return 0 - Success
    Return 1 - failed to connect
    Return 2 - userid/password invalid
    Return 4 - failed to subscribe
    """
    _METHOD_="manage_mellanox_switch.subscribe"

    logging.info("ENTER %s::address=%s userid=%s receiver=%s"
        ,_METHOD_,address,userid,receiver_address)
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(address, username=userid, password=password, timeout=30)
        client_shell = client.invoke_shell()

        time.sleep(1)
        client_shell.send(ENABLE_COMMAND)
        time.sleep(3) #waiting for command to complete
        output=client_shell.recv(2000) 
        logging.info("Command Sent : " + ENABLE_COMMAND)
        logging.debug(output.decode('ascii'))

        client_shell.send(CONFIGURE_TERMINAL_COMMAND)
        time.sleep(2) #waiting for command to complete
        output=client_shell.recv(1000) 
        logging.info("Command Sent : " + CONFIGURE_TERMINAL_COMMAND +"\n")
        logging.debug(output.decode('ascii'))

        client_shell.send(SNMP_V2_TRAP_NOTIFY_COMMAND + community +"\n")
        time.sleep(2) #waiting for command to complete
        output=client_shell.recv(1000) 
        logging.info("Command Sent : " + SNMP_V2_TRAP_NOTIFY_COMMAND + community +"\n")
        logging.debug(output.decode('ascii'))

        client_shell.send(SNMP_V2_TRAP_SUBSCRIBE_COMMAND + receiver_address + " traps " + community +"\n")
        time.sleep(2) #waiting for command to complete
        output=client_shell.recv(1000) 
        logging.info("Command Sent : " + SNMP_V2_TRAP_SUBSCRIBE_COMMAND + receiver_address + " traps " + community +"\n")
        output_str=output.decode('ascii')
        logging.debug("Output : " + output_str)
        if COMMAND_NOT_FOUND in output_str:
            logging.info("Command did not succeed, device may not be a Mellanox switch")
            return 4
        
        #check if the file exists for bringing up the mgmt interface and bring it up accordingly
        filename = TEMP_HACK_FILE_DIR + "." + address + "_mellanox"
        file = None
        try:
            if os.path.isfile(filename):
                logging.debug("%s::File found %s", _METHOD_, filename)
                file = open(filename,'r')
                interface = file.readline()
                unShutdownInterface(client_shell, interface)
                os.remove(filename)
                logging.debug("%s::File removed %s", _METHOD_, filename)
        except Exception as e:
            logging.warning("%s::Exception during file %s operation : %s ", _METHOD_, filename, e)
        finally:
            if file != None:
                file.close()
                
        client_shell.send(SHOW_SNMP_HOST_COMMAND)
        time.sleep(2) #waiting for command to complete
        output=client_shell.recv(1000) 
        logging.info("Command Sent : " + SHOW_SNMP_HOST_COMMAND)
        output_str=output.decode('ascii')
        logging.debug("Output : " + output_str)
        if receiver_address not in output_str:
            logging.info("Traps subscription NOT successfull")
            return 4

        lines = output_str.splitlines()
        for index,line in enumerate(lines):
            #Parse the output for receiver address and the community string for the receiver address
            if (receiver_address in line):
                if (community in lines[index+4]):
                    logging.info("Traps subscription successfull")
                    return 0
                else:
                    logging.error("Traps subscription NOT successfull")
                    return 4
        logging.info("Traps subscription NOT successfull")
        return 4       

    except paramiko.AuthenticationException:
        logging.error("%s::userid/password combination not valid. address=%s userid=%s",
                _METHOD_,address,userid)
        return 2
    except socket.timeout:
        logging.error("%s::Connection timed out. Address=%s",_METHOD_,address)
        return 1
    finally:
        client.close()


def unsubscribe(address,userid,password,receiver_address,community='public'):
    """ Configures the switch to unsubscribe the host from sending traps 
    Return 0 - Success
    Return 1 - failed to connect
    Return 2 - userid/password invalid
    Return 4 - failed to unsubscribe
    """
    _METHOD_="manage_mellanox_switch.unsubscribe"

    logging.info("ENTER %s::address=%s userid=%s receiver=%s"
        ,_METHOD_,address,userid,receiver_address)
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(address, username=userid, password=password, timeout=30)
        client_shell = client.invoke_shell()

        time.sleep(1)
        client_shell.send(ENABLE_COMMAND)
        time.sleep(3) #waiting for command to complete
        output=client_shell.recv(2000) 
        logging.info("Command Sent : " + ENABLE_COMMAND)
        logging.debug(output.decode('ascii'))

        client_shell.send(CONFIGURE_TERMINAL_COMMAND)
        time.sleep(2) #waiting for command to complete
        output=client_shell.recv(1000) 
        logging.info("Command Sent : " + CONFIGURE_TERMINAL_COMMAND +"\n")
        logging.debug(output.decode('ascii'))

        client_shell.send(SNMP_V2_TRAP_UNSUBSCRIBE_COMMAND + receiver_address +"\n")
        time.sleep(2) #waiting for command to complete
        output=client_shell.recv(1000) 
        logging.info("Command Sent : " + SNMP_V2_TRAP_UNSUBSCRIBE_COMMAND + receiver_address +"\n")
        logging.debug("Output : " + output.decode('ascii'))

        client_shell.send(SHOW_SNMP_HOST_COMMAND)
        time.sleep(2) #waiting for command to complete
        output=client_shell.recv(1000) 
        logging.info("Command Sent : " + SHOW_SNMP_HOST_COMMAND)
        output_str=output.decode('ascii')
        logging.debug("Output : " + output_str)
        if COMMAND_NOT_FOUND in output_str:
            logging.info("Command did not succeed, device may not be a Mellanox switch")
            return 5

        if receiver_address in output_str:
            logging.info("Traps unsubscription NOT successfull")
            return 5
        else:
            logging.info("Traps unsubscription successfull")
            return 0
    except paramiko.AuthenticationException:
        logging.error("%s::userid/password combination not valid. address=%s userid=%s",
                _METHOD_,address,userid)
        return 2
    except socket.timeout:
        logging.error("%s::Connection timed out. Address=%s",_METHOD_,address)
        return 1
    finally:
        client.close()

def change_device_network(address,userid,password,new_ipaddress,subnet,gateway,additional_interfaces):
    """
    change_device_network will return: return code
    Return 0 - Success, the network information has been successfully changed
    Return 1 - failed to connect
    Return 2 - userid/password invalid
    Return 6 - failed to change the network information
    """
    _METHOD_ = "manage_mellanox_switch.change_device_network"

    logging.info("ENTER %s::address=%s userid=%s IP=%s subnet=%s gateway=%s",_METHOD_,address,userid,new_ipaddress,subnet,gateway)

    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(address, username=userid, password=password, timeout=30)
        client_shell = client.invoke_shell()

        time.sleep(1)
        client_shell.send(ENABLE_COMMAND)
        time.sleep(3) #waiting for command to complete
        output=client_shell.recv(2000)
        logging.info("Command Sent : " + ENABLE_COMMAND)
        logging.debug(output.decode('ascii'))

        client_shell.send(CONFIGURE_TERMINAL_COMMAND)
        time.sleep(2) #waiting for command to complete
        output=client_shell.recv(1000)
        logging.info("Command Sent : " + CONFIGURE_TERMINAL_COMMAND +"\n")
        logging.debug(output.decode('ascii'))
        
        management_interface = 'mgmt0'
        other_mgmt_interface='mgmt1'
        configured_ip=getIPfromInterface(client_shell, management_interface)
        if configured_ip != address:
            management_interface='mgmt1'
            other_mgmt_interface='mgmt0'
        logging.info("%s::management interface=%s", _METHOD_, management_interface)
        
        if subnet == None:
            subnet = "255.255.255.0"
            
        if not additional_interfaces:
            additional_interfaces = {}
            
        for ip_interface in additional_interfaces:
            if ip_interface.getQualifier() == MLAG_VIP_QUALIFIER:
                mlag_vip_address = ip_interface.getIpAddress()
               
                # find the MLAG-VIP name to add to additional IP interfaces
                client_shell.send(SHOW_MLAG_VIP_COMMAND)
                time.sleep(5)
                output=client_shell.recv(5000)
                logging.info("Command Sent : " + SHOW_MLAG_VIP_COMMAND)
                output_str=output.decode('ascii')
                logging.debug(output_str)
                
                mlag_vip_name = None
                for line in output_str.splitlines():
                    #Parse the output for machine type model and serial number
                    if (line.strip().startswith("mlag-vip")):
                         mlag_vip_name = line.split()[1]
                
                if mlag_vip_name != None:
                    #configure the mlag-vip
                    client_shell.send("mlag-vip " + mlag_vip_name + " ip " + mlag_vip_address + " " + subnet + " force\n")
                    time.sleep(2) #waiting for command to complete
                    output=client_shell.recv(1000)
                    logging.info("Command sent : mlag-vip " + mlag_vip_name + " ip " + mlag_vip_address + " " + subnet + " force\n")
                    logging.debug("Output : " + output.decode('ascii'))
                
            if ip_interface.getQualifierType() == constants.network_interface_type.AdditionalPorts:
                new_additional_ip = ip_interface.getIpAddress()
                additional_interface = ip_interface.getQualifier()
                #configure the additional IP address
                client_shell.send("interface " + additional_interface + " ip address " + new_additional_ip + " " + subnet + "\n")
                time.sleep(2) #waiting for command to complete
                output=client_shell.recv(1000)
                logging.info("interface " + additional_interface + " ip address " + new_additional_ip + " " + subnet + "\n")
                logging.debug("Output : " + output.decode('ascii'))
                
                    
        if new_ipaddress == None:
            logging.info("No IP address sent to the method, returning successful")
            return 0
            
        #As there is no dual IP management for devices, need to ensure that the current management interface
        #does not go down, so putting a hack to 'shut' the other mgmt interface, create a hidden file with under
        #data directory with ".<ip_address>_mellanox, which should be checked and removed during subscribe.
        shutdownInterface(client_shell, other_mgmt_interface)
        writeMgmtHack(new_ipaddress, other_mgmt_interface)
            
        if gateway != None:
            #Set the default gateway address for the switch
            client_shell.send(DEFAULT_GATEWAY_COMMAND + gateway +  "\n")
            logging.info(DEFAULT_GATEWAY_COMMAND + gateway + "\n")
            gateway_set=False
            for wait in range(15):
                time.sleep(2) #waiting for command to complete
                if client_shell.recv_ready() == True:
                    gateway_set=True
                    output=client_shell.recv(1000)
                    logging.debug("Output : " + output.decode('ascii'))
            if gateway_set == False:
                logging.error("%s::Hang after gateway configuration", _METHOD_)
                return 6
            #Check if the gateway is configured correctly
            client_shell.send(SHOW_IP_ROUTE_COMMAND)
            time.sleep(2) #waiting for command to complete
            output=client_shell.recv(1000)
            logging.info(SHOW_IP_ROUTE_COMMAND)
            output_str=output.decode('ascii')
            logging.debug(output_str)
            for line in output_str.splitlines():
                #Parse the output for ip address and netmask
                if (line.startswith(DEFAULT_TAG)):
                    configured_gateway=line.split()[2]
                    if (configured_gateway != gateway):
                        logging.error("Gateway not configured correctly")
                        return 6
        
        #Set the IP address for the management interface
        client_shell.send("interface " + management_interface + " ip address " + new_ipaddress + " " + subnet + "\n")
        logging.info("interface " + management_interface + " ip address " + new_ipaddress + " " + subnet + "\n")
        for wait in range(15):
            time.sleep(2) #waiting for command to complete
            if client_shell.recv_ready == True:
                output=client_shell.recv(1000)
                logging.debug("Output : " + output.decode('ascii'))
        logging.info("Network configuration successfull")
        return 0

    except paramiko.AuthenticationException:
        logging.error("%s::userid/password combination not valid. address=%s userid=%s",
                _METHOD_,address,userid)
        return 2
    except socket.timeout:
        logging.error("%s::Connection timed out. Address=%s",_METHOD_,address)
        return 1
    finally:
        client.close()

def change_device_password(address, userid, password, new_password):
    """
    change_device_password will return: return code
    Return 0 - Success, the password has been successfully changed
    Return 1 - failed to connect
    Return 2 - userid/password invalid
    Return 7 - failed to change the password
    """
    _METHOD_ = "manage_mellanox_switch.change_device_password"

    logging.info("ENTER %s::address=%s userid=%s",_METHOD_,address,userid)
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(address, username=userid, password=password, timeout=30)
        client_shell = client.invoke_shell()

        time.sleep(1)
        client_shell.send(ENABLE_COMMAND)
        time.sleep(3) #waiting for command to complete
        output=client_shell.recv(2000) 
        logging.info("Command Sent : " + ENABLE_COMMAND)
        logging.debug(output.decode('ascii'))

        client_shell.send(CONFIGURE_TERMINAL_COMMAND)
        time.sleep(2) #waiting for command to complete
        output=client_shell.recv(1000) 
        logging.info("Command Sent : " + CONFIGURE_TERMINAL_COMMAND +"\n")
        logging.debug(output.decode('ascii'))

        client_shell.send("username " + userid + " password 0 " + new_password + "\n")
        time.sleep(2) #waiting for command to complete
        output=client_shell.recv(1000) 
        #logging.info("Command Sent : username " + userid + " password 0 " + new_password + "\n")
        logging.debug("Output : " + output.decode('ascii'))

        (rc,snum, model, additional_interfaces) = validate (address,userid,new_password) 

        if (rc == 0 ):
            logging.info("Password changed successfully")
            return 0
        else:
            logging.info("Password did not change")
            return 7

    except paramiko.AuthenticationException:
        logging.error("%s::userid/password combination not valid. address=%s userid=%s",
                _METHOD_,address,userid)
        return 2
    except socket.timeout:
        logging.error("%s::Connection timed out. Address=%s",_METHOD_,address)
        return 1
    finally:
        client.close()

def get_version(address, userid, password):
     """
     get_version will return: (return code, version) for rc = 0
     Return 0 - Success, version retrieved
     Return 1 - failed to connect
     Return 2 - userid/password invalid
     Return 11 - Failed to retrieve version
     """
     _METHOD_ = "manage_mellanox_switch.get_version"

     logging.info("ENTER %s::address=%s userid=%s",_METHOD_,address,userid)

     try:
         client = paramiko.SSHClient()
         client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
         client.connect(address, username=userid,
                       password=password, timeout=30)
         client_shell = client.invoke_shell()

         client_shell.send(ENABLE_COMMAND)
         time.sleep(2) #waiting for command to complete
         output=client_shell.recv(1000)
         logging.info("Command Sent : " + ENABLE_COMMAND)
         logging.debug(output.decode('ascii'))

         client_shell.send(GET_VERSION_COMMAND)
         time.sleep(2)
         output=client_shell.recv(5000)
         output_str=output.decode('ascii')
         logging.info("Command Sent : " + GET_VERSION_COMMAND)
         logging.debug(output_str)
         for line in output_str.splitlines():
             #Parse the output for version
             if CURRENT_VERSION_TAG in line:
                 version=line.split(':')[1]
                 return (0, version.strip())
         logging.warning("%s:Could not retrieve version", _METHOD_)
         return( 11, None)

     except paramiko.AuthenticationException:
         logging.error("%s::userid/password combination not valid. address=%s userid=%s",
                 _METHOD_,address,userid)
         return (2, None)
     except socket.timeout:
         logging.error("%s::Connection timed out. Address=%s",_METHOD_,address)
         return (1, None)
     finally:
         client.close()

