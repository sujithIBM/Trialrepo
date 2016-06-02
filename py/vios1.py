
import paramiko
import constants
import logging
import paramiko
import pexpect
import socket
import os
import time

IOSLEVEL_COMMAND="ioscli ioslevel"
INTERIM_COMMAND = "emgr -l"
SET_ENV="oem_setup_env"

viosdict={}

def get_version(address, userid, password,COMMAND):
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
        (stdin, stdout, stderr) = client.exec_command(COMMAND)
        stdin.close()
        if stdout.channel.recv_exit_status() == 0:
            version = stdout.read().decode('ascii').strip()
            return (0, version)
        else:
            logging.warning(
                "%s::Failed to retrieve version of vios. address=%s userid=%s"
                ,_METHOD_,address,userid)
            return (11, None)
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
def get_interim(address, userid, password,command,command1):
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
        (stdin, stdout, stderr) = client.exec_command(command)
        stdin.write(command1)
        stdin.write("\n")
        stdin.flush()            
        stdin.close()
        if stdout.channel.recv_exit_status() == 0:
            interim_op = stdout.readlines()
            ifix_info = interim_op[2][2]
            return (0, ifix_info)
        else:
            logging.warning(
                "%s::Failed to retrieve version of vios. address=%s userid=%s"
                ,_METHOD_,address,userid)
            return (11, None)
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
        
vios_version = get_version(address, userid, password,IOSLEVEL_COMMAND)


def get_servicepack(vios_version):
    try:
        print("getting the service pack information from the  version");
        sp = vios_version.split('.')
        return (0,sp[len(sp)-1])
    except Exception as e:
        logging.error("%s::Exception : %s",_METHOD_,e)
        return (1, None)

def get_Fixpack(vios_version):
    try:
        logger.info("gettinf the fix pack information form the isolevel command");
        fp =vios_version.split()[0].split('-')
        fpinfo = fp[1]+ '-' +fp[2]
        return (0,fpinfo)
    except Exception as e:
        logging.error("%s::Exception : %s",_METHOD_,e)
        return (1, None)
    
viosdict["version"]= vios_version
viosdict["Interim_Fixes"]=get_interim(address, userid, password,SET_ENV,INTERIM_COMMAND)
viosdict["service_pack"] = get_servicepack(vios_version)
viosdict["Fix_pack"] = get_Fixpack(vios_version)
print(viosdict)


