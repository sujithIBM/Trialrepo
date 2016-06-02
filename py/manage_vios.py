#!/usr/local/bin/python3.4
# Licensed Materials - Property of IBM
#
# (C) Copyright IBM Corp. 2015 All Rights Reserved
#
# US Government Users Restricted Rights - Use, duplicate or
# disclosure restricted by GSA ADP Schedule Contract with
# IBM Corp.

import constants
import logging
import paramiko
import pexpect
import socket
import os
import time

IOSLEVEL_COMMAND="ioscli ioslevel"
IFIXES_COMMAND= 'emgr -l'
vios={}

def getType():
    return constants.device_type.VIOS

def getManagementType():
    return constants.management_type.Hardware

def getWebURL(address):
    return None

def validate(address, userid, password):
    """returns return code 0 if the device is
    a vios and access info is valid. A VIOS
    doesn't have a machine type model or 
    serial number
    Return 0 - Success
    Return 1 - failed to connect
    Return 2 - userid/password invalid
    Return 3 - not vios
    """

    _METHOD_="manage_vios.validate"
    logging.info("ENTER %s::address=%s userid=%s",_METHOD_,address,userid)
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(address, username=userid, 
                       password=password, timeout=30)
        (stdin, stdout, stderr) = client.exec_command(IOSLEVEL_COMMAND)
        stdin.close()
        if stdout.channel.recv_exit_status() == 0:
            version = stdout.read().decode('ascii').strip()
            logging.info("%s::Device is a VIOS. version=%s",_METHOD_,version)
            return (0, None, None, version, None)
        else:
            logging.warning(
                "%s::Device is not a vios. address=%s userid=%s"
                ,_METHOD_,address,userid)
            return (3, None, None, None, None)
    except paramiko.AuthenticationException:
        logging.error("%s::userid/password combination not valid. address=%s userid=%s",
                _METHOD_,address,userid)
        return (2, None, None, None, None)
    except socket.timeout:
        logging.error("%s::Connection timed out. Address=%s",_METHOD_,address)
        return (1, None, None, None, None)
    finally:
        client.close()

def subscribe(address,userid,password,receiver_address):
    _METHOD_="manage_vios.subscribe"


    #check if the file exists to change the gateway
    #that could not be changed during network reconfiguration
    filename =  "/opt/ibm/puremgr/data/." + address + "_vios"
    file = None
    client = None
    
    try:
        if os.path.isfile(filename):
            logging.debug("%s::File found %s", _METHOD_, filename)
            file = open(filename,'r')
            (interface,gateway) = file.readline().split()

            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(address, username=userid,
                   password=password, timeout=30)

            oldgateway = None    
            CMD = "ioscli netstat -routinfo | grep default"
            (stdin, stdout, stderr) = client.exec_command(CMD)
            rc = stdout.channel.recv_exit_status()
            if (rc == 0):
                oldgateway = stdout.read().decode('ascii').split()[1]

            CMD = "ioscli chtcpip"
            CMD += " -interface " + interface
            CMD += " -gateway "
            CMD += " -add " + gateway
            if oldgateway is not None:
                CMD += " -remove " + oldgateway
            (stdin, stdout, stderr) = client.exec_command(CMD)
            rc = stdout.channel.recv_exit_status()
            if rc == 0:
                logging.info("%s::%s completed without error.",_METHOD_,CMD)
                os.remove(filename)
                logging.debug("%s::File removed %s", _METHOD_, filename)
            else:
                err = stdout.read().decode('ascii')
                logging.warning("%s::Failure to update the network gateway: %s. Will attempt after next puremgr restart.",_METHOD_,err)
    except Exception as e:
        logging.warning("%s::Exception during file %s operation : %s ", _METHOD_, filename, e)
    finally:
        if file != None:
            file.close()
        if client != None:
            client.close()

    return 0

def unsubscribe(address,userid,password,receiver_address):
    return 0

def get_version(address, userid, password):
    """
    get_version will return: (return code, version) for rc = 0 
    Return 0 - Success, version retrieved
    Return 1 - failed to connect
    Return 2 - userid/password invalid
    Return 11 - Failed to retrieve version
    """
    _METHOD_ = "manage_vios.get_version"

    logging.info("ENTER %s::address=%s userid=%s",_METHOD_,address,userid)
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(address, username=userid, 
                       password=password, timeout=30)
        (stdin, stdout, stderr) = client.exec_command(IOSLEVEL_COMMAND)
        stdin.close()
        if stdout.channel.recv_exit_status() == 0:
            version1= stdout.readlines()
            version = version1.decode('ascii').strip()
            return (0, version)
            VIOS1['installed_version']=version
        else:
            logging.warning(
                "%s::Failed to retrieve version of vios. address=%s userid=%s"
                ,_METHOD_,address,userid)
            return (11, None)
        (stdin, stdout, stderr) = client.exec_command('oem_setup_env')
        (stdin, stdout, stderr) = client.exec_command(IFIXES_COMMAND)
        if stdout.channel.recv_exit_status() == 0:
            interim_op = stdout.readlines()
            ifix_info = interim_op[2][2]
            return (0, ifix_info)
            VIOS1['fixes']={}
            if ifix_info != 0:
                VIOS1['fixes']['iFixes']=ifix_info
        else:
            logging.warning(
                "%s::Failed to retrieve version of vios. address=%s userid=%s"
                ,_METHOD_,address,userid)
            return (11, None)
            VIOS1['fixes']={}

        sp = version1.split('.')
        VIOS1['service_pack'] = sp[len(sp)-1]
        
        fp =version1.split()[0].split('-')
        if fp[1]!=0 & fp[2]!=0:
            fpinfo = fp[1]+ '-' +fp[2]
            VIOS1['fix_pack'] =fpinfo
        else :
            VIOS1['fix_pack']={}
        
    except paramiko.AuthenticationException:
        logging.error("%s::userid/password combination not valid. address=%s userid=%s",
                _METHOD_,address,userid)
        return (2, None)
    except socket.timeout:
        logging.error("%s::Connection timed out. Address=%s",_METHOD_,address)
        return (1, None)
    except Exception as e:
        logging.error("%s::Exception : %s",_METHOD_,e)
        return (1, None)
    finally:
        client.close()


def change_device_network(address, userid, password, new_address, subnet, gateway, additional_interfaces=None, interface=None, hostname=None):
    """This function is to update the network configuration for an HMC
    if interface is not specified it will change the interface used by current address
    if hostname is not specified it will keep the current hostname
    Return 0 - Success
    Return 1 - failed to connect
    Return 2 - userid/password invalid
    Return 6 - Network change failed
    """
    _METHOD_ = "manage_vios.change_device_network"
    LIST_INTERFACES="ioscli lstcpip -interfaces"
    HOSTNAME="ioscli hostname"
    MKTCPIP="ioscli mktcpip -start"
    logging.info("ENTER %s::address=%s userid=%s new_address=%s subnet=%s gateway=%s interface=%s hostname=%s" \
            , _METHOD_, address, userid, new_address, subnet, gateway, interface, hostname)
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(address, username=userid,
                       password=password, timeout=30)
        if interface is None:
            #find the interface for the current ip
            (stdin, stdout, stderr) = client.exec_command(LIST_INTERFACES)
            stdin.close()
            results = stdout.read().decode('ascii')
            for line in results.splitlines()[3:]:
                value = line.split()[1]
                if value == address:
                    interface = line.split()[0]
                    break
            if interface is None:
                logging.error("%s::Unable to find the interface associated with the ip address: %s", _METHOD_,address)
                return 6

        if hostname is None:
            #get the current hostname
            (stdin, stdout, stderr) = client.exec_command(HOSTNAME)
            stdin.close()
            hostname = stdout.read().decode('ascii').strip()
            if hostname is None:
                logging.error("%s::Unable to find the hostname associated with the ip address: %s", _METHOD_,address)
                return 6

        if gateway is not None:
            oldgateway = None
            CMD = "ioscli netstat -routinfo | grep default"
            (stdin, stdout, stderr) = client.exec_command(CMD)
            rc = stdout.channel.recv_exit_status()
            if (rc == 0):
                oldgateway = stdout.read().decode('ascii').split()[1]

            CMD = "ioscli chtcpip"
            CMD += " -interface " + interface
            CMD += " -gateway "
            CMD += " -add " + gateway
            if oldgateway is not None:
                CMD += " -remove " + oldgateway
            logging.info("%s::Invoking commands: %s", _METHOD_,CMD)
            (stdin, stdout, stderr) = client.exec_command(CMD)
            rc = stdout.channel.recv_exit_status()
            if (rc != 0):
                err = stderr.read().decode('ascii')
                logging.error("%s::Failure to update the network gateway. Will attempt after puremgr restart: %s",_METHOD_,err)
                writeGatewayHack(new_address, interface, gateway)


        CMD = MKTCPIP
        CMD += " -hostname " + hostname
        CMD += " -interface " + interface
        CMD += " -inetaddr " + new_address
        if subnet is not None:
            CMD += " -netmask " + subnet
        logging.info("%s::Invoking commands: %s", _METHOD_,CMD)
        (stdin, stdout, stderr) = client.exec_command(CMD)
        #if network changed work recv_exit_status will hang
        #so sleep and only call it if it is ready
        time.sleep(10)
        if stdout.channel.exit_status_ready():
            rc = stdout.channel.recv_exit_status()
            if (rc != 0):
                err = stderr.read().decode('ascii')
                logging.error("%s::Failure to update the network interface: %s",_METHOD_,err)
                return 6
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


def change_device_password(address, userid, password, newPassword):
    """This function is to update the password of the user on the VIOS
    Return 0 - Success
    Return 1 - failed to connect
    Return 2 - userid/password invalid
    Return 7 - password changed failed
    """
    _METHOD_ = "manage_vios.change_device_password"
    NEW_PASSWD_PROMPT = "New password:"
    NEW_PASSWD_CONFIRM_PROMPT = "Enter the new password again:"
    CHANGE_PASSWD_CMD = "passwd"
    logging.info("ENTER %s::address=%s userid=%s", _METHOD_, address, userid)
    ssh_conn_cmd = "ssh -o StrictHostKeyChecking=false -l " + userid + " " + address
    try:
        ssh_conn_child = pexpect.spawn(ssh_conn_cmd)
        ssh_conn_index = ssh_conn_child.expect(["password:", pexpect.EOF, pexpect.TIMEOUT])
        if ssh_conn_index == 0: 
            ssh_conn_child.sendline(password)
            #if shell prompts for password again, the password / user combination wrong
            ssh_conn_index = ssh_conn_child.expect(["\$","password: "])
            if ssh_conn_index == 0:
                ssh_conn_child.sendline(CHANGE_PASSWD_CMD)
                ssh_conn_child.expect(NEW_PASSWD_PROMPT)
                ssh_conn_child.sendline(newPassword)
                ssh_conn_index = ssh_conn_child.expect([NEW_PASSWD_CONFIRM_PROMPT, NEW_PASSWD_PROMPT])
                if ssh_conn_index == 0:
                    ssh_conn_child.sendline(newPassword)
                    ssh_conn_child.expect("\$")
                    ssh_conn_child.send("exit")
                    return 0
                elif ssh_conn_index == 1:
                    return 7
            else:
                logging.error("%s::userid/password combination not valid. address=%s userid=%s", _METHOD_, address, userid)
                return 2
        else:
            logging.error("%s::Connection timed out. Address=%s",_METHOD_,address)
            return 1
    except Exception as e:
        logging.error("%s::exception error: %s",_METHOD_,str(e))
        return 7
    finally:
        ssh_conn_child.close()

def writeGatewayHack(new_ip_address, interface, gateway):
    _METHOD_ = "manage_vios.writeGatewayHack"
    filename = "/opt/ibm/puremgr/data/." + new_ip_address + "_vios"
    file = None
    try:
        file = open(filename,'w')   # Trying to create a new file or open one
        logging.debug("%s::File created %s", _METHOD_, filename)
        file.write(interface + " " + gateway)
        logging.debug("%s::Interface:%, gateway %s added to file.", _METHOD_, interface, gateway)
    except Exception as e:
        logging.warning("%s::Exception during file creation/updating %s : %s", _METHOD_, filename, e)
    finally:
        if file != None:
            file.close()
