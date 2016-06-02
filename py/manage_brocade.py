#!/usr/local/bin/python3.4
# Licensed Materials - Property of IBM
#
# (C) Copyright IBM Corp. 2015 All Rights Reserved
#
# US Government Users Restricted Rights - Use, duplicate or
# disclosure restricted by GSA ADP Schedule Contract with
# IBM Corp.

import constants
import sys
import pexpect
import logging
import paramiko
import socket
from time import sleep
from optparse import OptionParser

Timeout = 120
ROOT_PROMPT = '#'
Timeout_CmdRep = 15
GET_VERSION_COMMAND = "version show | grep OS"
CURRENT_VERSION_TAG = "OS"

# python dictionary brocade model to check the switch MTM
brocade_switch_model = {}
brocade_switch_model["71"] = "Brocade 300 Switch"
brocade_switch_model["109"] = "Brocade 6510 Switch"
brocade_switch_model["117"]= "Brocade 6547 Embedded Switch"

def getType():
    return constants.device_type.Brocade

def getManagementType():
    return constants.management_type.Hardware

def getWebURL(address):
    return "https://" + address

def validate(address, userid, password):
    """
    validate will return: return code 
    '0' --> Success, the managed device is BRCD, machine_type_model, version #SSN
    '1' --> failed to connect
    '2' --> invalide userid/password
    '3' --> Not a BRCD
    """
    machine_type_model = None
    serial_number = None
    _METHOD_ = "manage_brocade.validate"
    CHASSIS_SHOW_CMD = "chassisshow"
    SWITCH_SHOW_CMD = "switchshow"
    
    logging.info("ENTER %s::address=%s userid=%s",_METHOD_,address,userid)
    ssh_conn_cmd = "ssh -o StrictHostKeyChecking=false -l " + userid + " " + address
    try:
    
    
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(address, username=userid, 
                       password=password, timeout=Timeout)
        (stdin, stdout, stderr) = client.exec_command(CHASSIS_SHOW_CMD)
        stdin.close()
        
        for line in stdout.read().decode('ascii').splitlines():
            index = line.strip().find("Serial Num:")
            if (index == 0): 
                serial_number=line.split()[-1]
                logging.info ("Switch SSN::%s",  serial_number)

        (stdin, stdout, stderr) = client.exec_command(SWITCH_SHOW_CMD)
        stdin.close()
        for line in stdout.read().decode('ascii').splitlines():
            index = line.strip().find("switchType:")
            if (index >= 0):
                switch_type = line.split()[-1]
                #logging.info ("The switch type::%s ", switch_type)
                sub_rel_index = switch_type.strip().find('.')
                release = switch_type[:sub_rel_index].strip()
                #logging.info ("The switch release::%s", release)
                if release in brocade_switch_model:
                    machine_type_model = brocade_switch_model[release]
                else:
                    machine_type_model = release

                logging.info("Machine Type Model::%s", machine_type_model)
                    

        if machine_type_model is None:
            logging.warning(
            "%s::Device is not an BRCD, chassisshow and switchshow failed in the output. address=%s userid=%s"
            ,_METHOD_,address,userid)
            return (3, None, None, None, None)
        else:
            rc, version = get_version(address, userid, password)
            logging.info("%s::Device is a brocade switch. MTM:%s, Serial_Num:%s, Version:%s",
            _METHOD_,machine_type_model,serial_number,version)
            return (0, machine_type_model, serial_number, version, None)

        
    except paramiko.AuthenticationException:
        logging.error("%s::userid/password combination not valid. address=%s userid=%s",
                _METHOD_,address,userid)
        return (2, None, None, None, None)
    except socket.timeout:
        logging.error("%s::Connection timed out. Address=%s",_METHOD_,address)
        return (1, None, None, None, None)
    finally:
        client.close()


def subscribe(address, userid, password, receiver_address):

    """
    This function will call snmpConfig to configure the snmpv1 in the brocade switch 
    to submit the Traps to the receiver nagios server
    The return values:
    '0' --> success
    '1' --> connection to the brocade switch failed
    '2' --> invalid userid/password 
    '4' --> snmpConfig failed to add the target server in snmpv1 
    """
    _METHOD_ = "manage_brocade.subscribe"
    logging.info("ENTER %s::address=%s userid=%s receiver=%s",_METHOD_,address,userid,receiver_address)
    ssh_conn_cmd = "ssh -o StrictHostKeyChecking=false -l " + userid + " " + address
    switch_admin = userid + "> "
    
    try:
        ssh_conn_child = pexpect.spawn(ssh_conn_cmd)
        ssh_conn_child.timeout = Timeout
        ssh_conn_index = ssh_conn_child.expect(['(?i)password:' , pexpect.EOF, pexpect.TIMEOUT])
        if ssh_conn_index == 0: 
            ssh_conn_child.sendline(password)
            # if shell prompts for password again, the password / user combination wrong
            ssh_conn_index = ssh_conn_child.expect([switch_admin, "(?i)password:", ROOT_PROMPT])
            if ssh_conn_index == 0:
                ssh_conn_child.send("snmpconfig --enable snmpv1\r")
                ssh_conn_child.expect(switch_admin,timeout=Timeout_CmdRep)
                ssh_conn_child.send("snmpconfig --set snmpv1\r")
                ssh_conn_child.expect("] ")
                ssh_conn_child.send("\r")
                ssh_output = ssh_conn_child.before.decode('ascii')
                fields = ssh_output.split("\r\n")
                for field in fields:
                    field_inf = "After set snmpv1 command: " + field 
                skipTrap = False
                line = field
                while line.find(switch_admin) < 0:
                    #logging.info("Debug initial while line::%s ",  line)
                    if line.find("Trap Recipient's IP address") >=0:
                        if line.find("0.0.0.0") < 0: 
                            #The Traps has been configured, send("\r") 3 times
                            ssh_conn_child.send("\r")
                            ssh_conn_child.expect("]")
                            ssh_conn_child.send("\r")
                            ssh_conn_child.expect("]")
                            ssh_conn_child.send("\r")
                            if line.find(receiver_address) >=0:
                                # The reciver has been added in snmp trap configuration
                                skipTrap = True
                                logging.info ("%s::The snmp trap already configured. No need to reconfigure. address=%s userid=%s targe=%s", _METHOD_, address, userid, receiver_address)
                        elif line.find("0.0.0.0") >= 0:
                            #Find the available Trap configuration 
                            if skipTrap == True:
                                logging.info("The Trap Community has been setup, skip it")
                                #Send("\r")  
                                ssh_conn_child.send("\r")
                            else: 
                                ssh_conn_child.send(receiver_address+"\r")
                                ssh_conn_child.expect("]")
                                ssh_output = ssh_conn_child.before.decode('ascii')
                                trap_sv = ssh_output.split("\r\n")
                                for trap in trap_sv:
                                    logging.debug("trap::%s", trap)
                                ssh_conn_child.send("4\r")
                                ssh_conn_child.expect ("]")
                                ssh_output = ssh_conn_child.before.decode('ascii')
                                trap_ports = ssh_output.split("\r\n")
                                for trap_port in trap_ports:
                                    logging.debug("trap port:" + trap_port)

                                ssh_conn_child.send("162\r")
                                skipTrap = True
                                logging.info ("%s::The Trap subcribe has been done. address=%s userid=%s targe=%s", _METHOD_, address, userid, receiver_address)


                    ssh_conn_index = ssh_conn_child.expect (["]", switch_admin])              
                    ssh_output = ssh_conn_child.before.decode('ascii')

                    if ssh_conn_index == 0:
                        lines = ssh_output.split("\r\n")
                        for line in lines:
                            logging.debug ("debug line::%s", line)
                        logging.debug ("final line::%s", line)
                        if line.find("Community") >=0:
                            #Find the next Trap Community, needs to send "\r"
                            ssh_conn_child.send("\r")
                            ssh_conn_child.expect("]")
                            ssh_output = ssh_conn_child.before.decode('ascii')
                            items = ssh_output.split("\r\n")
                            for item in items:
                                logging.debug ("debug item::%s", item)
                            logging.debug ("final item::%s", item)
                            line = item

                    elif ssh_conn_index == 1:
                        #logging.info ("I hit end of the snmp conf")
                        lines = ssh_output.split("\r\n")
                        for line in lines:
                            #logging.info ("%s %s", switch_admin, line)
                            line = line + switch_admin
            elif ssh_conn_index == 1:
                logging.error("%s::userid/password combination not valid. address=%s userid=%s", _METHOD_, address, userid)
                return 2
            elif ssh_conn_index == 2:
                logging.warning("%s::The device is not a brocade switch. address=%s userid=%s", _METHOD_, address, userid)
                return 4
        else:
            logging.error("%s::Connection timed out. Address=%s",_METHOD_,address)
            return 1
                
        return 0
    except Exception as e:
        #print("%s:: exception error", _METHOD_+"::"+str(e))
        logging.error("%s:: exception error", _METHOD_+"::"+str(e))
        return 3

    finally:
        ssh_conn_child.close()


def unsubscribe(address, userid, password, receiver_address):
    """
    Unsubscribes the Nagios server that the system won't receive 
    the brocade Traps
    Returned values:
    '0' --> success
    '1' --> connection failed 
    '2' --> invalid userid/password combination 
    '5' --> after login the Brocade switch, the snmpConfig operation failed
    """
    _METHOD_ = "manage_brocade.unsubscribe"

    Timeout = 120
    logging.info("ENTER %s::address=%s userid=%s receiver=%s", _METHOD_, address, userid, receiver_address)
    
    ssh_conn_cmd = "ssh -o StrictHostKeyChecking=false -l " + userid + " " + address
    try:
        ssh_conn_child = pexpect.spawn(ssh_conn_cmd)
        ssh_conn_child.timeout = Timeout
        ssh_conn_index = ssh_conn_child.expect(['(?i)password:', pexpect.EOF, pexpect.TIMEOUT])
        if ssh_conn_index == 0: 
            ssh_conn_child.sendline(password)
            # if shell prompts for password again, the password / user combination wrong
            switch_admin = userid + "> "
            ssh_conn_index = ssh_conn_child.expect([switch_admin, "(?i)password:", ROOT_PROMPT])
            if ssh_conn_index == 0:
                ssh_conn_child.send("snmpconfig --set snmpv1\r")
                ssh_conn_child.expect("] ")
                ssh_conn_child.send("\r")
                ssh_output = ssh_conn_child.before.decode('ascii')
                fields = ssh_output.split("\r\n")
                for field in fields:
                    field_inf = "After set snmpv1 command: " + field 
                    logging.debug (field_inf)
                skipTrap = False
                line = field
                while line.find(switch_admin) < 0:
                    logging.debug("Debug initial while line::%s ", line)
                    if line.find("Trap Recipient's IP address") >=0:
                        if line.find("0.0.0.0") < 0: 
                            # The Traps has been configured, verify if it's the target switch
                            if line.find(receiver_address) >=0:
                                ssh_conn_child.send("0.0.0.0\r")
                                logging.info("%s::receiver %s was not subscribed to receive traps", _METHOD_, receiver_address)
                                #return 0
                            else: # The Traps has been configured, skip it
                                ssh_conn_child.send("\r")
                                ssh_conn_child.expect("]")
                                ssh_conn_child.send("\r")
                                ssh_conn_child.expect("]")
                                ssh_conn_child.send("\r")
                        elif line.find("0.0.0.0") >= 0:
                            #Find the empty Trap configuration, skip it 
                            logging.info("The Trap Community has not configured, skip it")
                            #send("\r") 
                            ssh_conn_child.send("\r")

                    ssh_conn_index = ssh_conn_child.expect (["]", switch_admin])              
                    ssh_output = ssh_conn_child.before.decode('ascii')

                    if ssh_conn_index == 0:
                        lines = ssh_output.split("\r\n")
                        for line in lines:
                            logging.debug ("debug line::%s ", line)
                        logging.debug ("final line::%s ", line)
                        if line.find("Community") >=0:
                            #Find the next Trap Community, needs to send \r
                            ssh_conn_child.send("\r")
                            ssh_conn_child.expect("]")
                            ssh_output = ssh_conn_child.before.decode('ascii')
                            items = ssh_output.split("\r\n")
                            for item in items:
                                logging.debug ("debug item::%s", item)
                            line = item

                    elif ssh_conn_index == 1:
                        lines = ssh_output.split("\r\n")
                        for line in lines:
                            logging.debug("admin> %s", line)
                        line = line + switch_admin
            elif ssh_conn_index == 1:
                logging.error("%s::userid/password combination not valid. address=%s userid=%s", _METHOD_, address, userid)
                return 2
            elif ssh_conn_index ==2:
                logging.warning("%s::The device is not a brocade switch. address=%s userid=%s", _METHOD_, address, userid)
                return 5
        else:
            logging.error("%s::Connection timed out. Address=%s",_METHOD_,address)
            return 1
 
        logging.info("%s:: has been completed successfully. Address=%s",_METHOD_,address)
        return 0
            
    except Exception as e:
        #print("%s:: exception error", _METHOD_+"::"+str(e))
        logging.error("%s:: exception error", _METHOD_+"::"+str(e))
        return 3

    finally:
        ssh_conn_child.close()


def change_device_password(address, userid, password, new_password):
    """
    change_device_password will return: return code 
    '0' --> Success, the password has been successfully changed
    '1' --> failed to connect
    '2' --> invalide userid/password
    '3' --> Not a BRCD
    '7' --> change password failed
    """
    _METHOD_ = "manage_brocade.change_device_password"
    OLD_PASSWD_PROMPT = "Enter old password:"
    NEW_PASSWD_PROMPT = "Enter new password:"
    NEW_PASSWD_CONFIRM_PROMPT = "Re-type new password:"
    CHANGE_PASSWD_CMD = "passwd"
    logging.info("ENTER %s::address=%s userid=%s",_METHOD_,address,userid)
    ssh_conn_cmd = "ssh -o StrictHostKeyChecking=false -l " + userid + " " + address
    try:
        ssh_conn_child = pexpect.spawn(ssh_conn_cmd)
        ssh_conn_child.timeout = Timeout
        ssh_conn_index = ssh_conn_child.expect(["(?i)password:", pexpect.EOF, pexpect.TIMEOUT])
        if ssh_conn_index == 0: 
            ssh_conn_child.sendline(password)
            #if shell prompts for password again, the password / user combination wrong
            switch_admin = userid + "> "
            ssh_conn_index = ssh_conn_child.expect([switch_admin, "(?i)password:", ROOT_PROMPT])
            if ssh_conn_index == 0:
                ssh_conn_child.sendline(CHANGE_PASSWD_CMD)
                ssh_conn_child.expect(OLD_PASSWD_PROMPT)
                ssh_conn_child.sendline(password)
                ssh_conn_child.expect(NEW_PASSWD_PROMPT)
                ssh_conn_child.sendline(new_password)
                ssh_conn_index = ssh_conn_child.expect([NEW_PASSWD_CONFIRM_PROMPT, NEW_PASSWD_PROMPT])
                if ssh_conn_index == 0:
                    ssh_conn_child.sendline(new_password)
                    ssh_conn_child.expect(switch_admin)
                    ssh_conn_child.send("exit")
                    return (0)
                elif ssh_conn_index == 1:
                    return (7)
            elif ssh_conn_index == 1:
                logging.error("%s::userid/password combination not valid. address=%s userid=%s", _METHOD_, address, userid)
                return (2)
            elif ssh_conn_index == 2:
                #TODO check the command result
                logging.warning("%s::Device is not a brocade switch. address=%s userid=%s", _METHOD_, address, userid) 
                return (3)
        else:
            logging.error("%s::Connection timed out. Address=%s",_METHOD_,address)
            return (1)

    except Exception as e:
        #print("%s:: exception error", _METHOD_+"::"+str(e))
        logging.error("%s:: exception error", _METHOD_+"::"+str(e))
        return (7)
        
    finally:
        ssh_conn_child.close()


def change_device_network(address, userid, password, new_address, subnet, gateway, additional_interfaces=None):
    """
    change_device_network will return: return code 
    '0' --> Success, the password has been successfully changed
    '1' --> failed to connect
    '2' --> invalide userid/password
    '3' --> Not a BRCD
    '6' --> change IP address failed
    """
    _METHOD_ = "manage_brocade.change_device_network"
    IP_ADDR_PROMPT = "Ethernet IP Address"
    SUBNETMASK_PROMPT = "Ethernet Subnetmask"
    GATEWAY_PROMPT = "Gateway IP Address"
    DHCP_PROMPT = "DHCP"
    IP_CHG_COMFIRMED = "IP address is being changed"
    CHANGE_IPADDR_CMD = "ipaddrset"
    logging.info("ENTER %s::address=%s userid=%s new_address=%s subnet=%s gateway=%s", _METHOD_, address, userid, new_address, subnet, gateway)
    ssh_conn_cmd = "ssh -o StrictHostKeyChecking=false -l " + userid + " " + address
    try:
        ssh_conn_child = pexpect.spawn(ssh_conn_cmd)
        ssh_conn_child.timeout = 30
        ssh_conn_index = ssh_conn_child.expect(["(?i)password:", pexpect.EOF, pexpect.TIMEOUT])
        if ssh_conn_index == 0: 
            ssh_conn_child.sendline(password)
            #if shell prompts for password again, the password / user combination wrong
            switch_admin = userid + "> "
            ssh_conn_index = ssh_conn_child.expect([switch_admin, "(?i)password:", ROOT_PROMPT])
            if ssh_conn_index == 0:
                ssh_conn_child.sendline(CHANGE_IPADDR_CMD)
                ssh_conn_child.expect(IP_ADDR_PROMPT)
                ssh_conn_child.sendline(new_address)
                ssh_conn_index = ssh_conn_child.expect([SUBNETMASK_PROMPT, IP_ADDR_PROMPT])
                if ssh_conn_index == 0:
                    if subnet == None:
                        ### No need to change subnet, since the new IP in the same subnet
                        ssh_conn_child.sendline("\r")
                    else:
                        ssh_conn_child.sendline(subnet)

                    ssh_conn_index = ssh_conn_child.expect([GATEWAY_PROMPT, SUBNETMASK_PROMPT])
                    if ssh_conn_index == 0:
                        if gateway == None:
                            ### No need to change gateway, since the new IP uses the same gateway
                            ssh_conn_child.sendline("\r")
                        else:
                            ssh_conn_child.sendline(gateway)

                        ssh_conn_index = ssh_conn_child.expect([DHCP_PROMPT, GATEWAY_PROMPT, ])
                        if ssh_conn_index == 0:
                            ssh_conn_child.sendline("\r")
                            ssh_conn_index = ssh_conn_child.expect([CHANGE_IPADDR_CMD, switch_admin, pexpect.TIMEOUT ])
                            if ssh_conn_index == 0:
                                logging.info("%s::IP address is being changed...Done. new IP address: %s subnetmask%s and new Gateway: %s",_METHOD_, new_address, subnet, gateway)
                                ssh_conn_child.send("exit")
                                return (0)
                            elif ssh_conn_index == 1:
                                logging.info ("%s::IP address has not been changed. Old and new IP addresses are identical.",_METHOD_) 
                                return (0)
                            elif ssh_conn_index == 2:
                                logging.info ("%s:: IP address is being changed. Please verify it", _METHOD_)
                                return (0) 
                        elif ssh_conn_index == 1:
                            logging.error ("%s::Invalid gateway format or value: %s ", _METHOD_, gateway)
                            return (6)
                    elif ssh_conn_index == 1:
                        logging.error("%s:: Invalid subnetmake format or value: %s, the IP configuration failed", _METHOD_, subnet)
                        return (6)
                    ssh_conn_child.send("exit")
                    return (0)
                elif ssh_conn_index == 1:
                    logging.error("%s:: Invlaid IP address format or value: %s ", _METHOD_, new_address)
                    return (6)
            elif ssh_conn_index == 1:
                logging.error("%s::userid/password combination not valid. address=%s userid=%s", _METHOD_, address, userid)
                return (2)
            elif ssh_conn_index == 2:
                logging.warning("%s::Device is not a brocade switch. address=%s userid=%s", _METHOD_, address, userid) 
                return (3)
        else:
            logging.error("%s::Connection timed out. Address=%s",_METHOD_,address)
            return (1)

    except Exception as e:
        #print("%s:: exception error", _METHOD_+"::"+str(e))
        logging.error("%s:: exception error", _METHOD_+"::"+str(e))
        return (6)
        
    finally:
        ssh_conn_child.close()
           
def get_version(address, userid, password):
     """
     get_version will return: (return code, version) for rc = 0
     Return 0 - Success, version retrieved
     Return 1 - failed to connect
     Return 2 - userid/password invalid
     Return 11 - Failed to retrieve version
     """
     _METHOD_ = "manage_brocade.get_version"

     logging.info("ENTER %s::address=%s userid=%s",_METHOD_,address,userid)

     try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(address, username=userid,
                       password=password, timeout=30)
        (stdin, stdout, stderr) = client.exec_command(GET_VERSION_COMMAND)
        stdin.close()
        for line in stdout.read().decode('ascii').splitlines():
            #Parse the output for version
             if CURRENT_VERSION_TAG in line:
                 version=line.split(':')[1]
                 return (0, version.strip())
        logging.warning("%s:Could not retrieve version", _METHOD_)
        return (11, None)

     except paramiko.AuthenticationException:
         logging.error("%s::userid/password combination not valid. address=%s userid=%s",
                 _METHOD_,address,userid)
         return (2, None)
     except socket.timeout:
         logging.error("%s::Connection timed out. Address=%s",_METHOD_,address)
         return (1, None)
     finally:
         client.close()

