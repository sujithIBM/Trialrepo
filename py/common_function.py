#!/usr/local/bin/python3.4
import sys, os, string, time
import getopt
import logging
import random
import subprocess
import pexpect
import time
from paramiko import SSHClient
from paramiko import AutoAddPolicy
import paramiko

devicelist = []
CMD_ADD_DEVICE = '/opt/ibm/puremgr/bin/add_device'
CMD_LIST_DEVICES = '/opt/ibm/puremgr/bin/list_devices'
CMD_REMOVE_DEVICE = '/opt/ibm/puremgr/bin/remove_device'
CMD_PUREMGR_SERVICE = '/usr/sbin/service'
CMD_REMOTE_ACCESS = '/opt/ibm/puremgr/bin/remote_access'
CMD_SET_SNMP_PROXY = '/opt/ibm/puremgr/bin/set_snmp_proxy'
CMD_CHANGE_DEVICE = '/opt/ibm/puremgr/bin/change_device'

HELP_OPTION = ['-h', '--help']
ADD_LABEL_OPTION = ['-l', '--label']
ADD_DEVICE_TYPE_OPTION = ['-t', '--type']
ADD_USER_OPTION = ['-u', '--user']
ADD_PASSWORD_OPTION = ['-p', '--password']
ADD_RACK_ID_OPTION = ['--rackid']
ADD_RACK_LOCATION_OPTION = ['--rack-location']
ADD_IPV4_ADDRESS_OPTION = []

CHANGE_LABEL_OPTION = ['-l', '--label']
CHANGE_USER_OPTION = ['-u', '--user']
CHANGE_PASSWORD_OPTION = ['-p', '--password']
CHANGE_PROMPT_OPTION = ['-P', '--prompt-password']
CHANGE_NEW_LABEL_OPTION = ['--new-label']
CHANGE_RACK_ID_OPTION = ['--rackid']
CHANGE_RACK_LOCATION_OPTION = ['--rack-location']


LIST_BRIEFLY_OPTION = ['-b', '--briefly']
LIST_LABEL_OPTION = ['-l', '--label']
LIST_TYPE_OPTION = ['-t', '--type']
LIST_SUPP_OPTION = ['--supported']


SNMP_NAME_OPTION = ['-n']
SNMP_CMTYV1V3_OPTION = ['-t']
SNMP_CMTYV1_OPTION = ['-T']
SNMP_CMTY_OPTION = ['-c']
SNMP_IP_OPTION = ['-i']
SNMP_VERSION_OPTION = ['-v']
SNMP_SECURITY_NAME_OPTION = ['-u']
SNMP_AUTH_PROTOCOL_OPTION = ['-a']
SNMP_AUTH_PASSWORD_OPTION = ['-A']
SNMP_PRIV_PROTOCOL_OPTION = ['-x']
SNMP_PRIV_PASSWORD_OPTION = ['-X']
SNMP_SECURITY_LEVEL_OPTION = ['-l']

KEYS_SNMP = ['name', 'cmtyV1V3', 'cmtyV1', 'ip', 'version', 'security_name', 'auth_protocol', 'auth_password', 'priv_protocol', 'priv_password', 'security_level']
KEYS_SNMPGET = ['name', 'cmty', 'version', 'security_name', 'auth_protocol', 'auth_password', 'priv_protocol', 'priv_password', 'security_level']
KEYS_DEVICE = ['label', 'rack_id', 'rack_location', 'device_type', 'user', 'password', 'ipv4_address']
KEYS_CHANGE_DEVICE=['label', 'new_label', 'rack_id', 'rack_location']  #Do not add 'user', 'password'
KEY_LABEL = 'label'
KEY_VERSION = 'version'

'''logging.basicConfig(format= '%(asctime)-12s [%(filename)-10s] %(levelname)s %(message)s', level=logging.DEBUG)
'''
logger = logging.getLogger(__name__)


def usage():
    print('Usage: {0} -f <file name> '.format(sys.argv[0]))
    sys.exit()

'''get option randomly, for example, any of ['-h', '--help']'''
def _get_option(opts):
  if len(opts) ==0:
    return None
  e = len(opts)-1
  i = random.randint(0, e)
  return opts[i]

def _combine_option(paras, keys, prefix):
    cmd = []
    for s in keys:
      try:
        if paras[s] is None:
          continue
        v = str(paras[s])
        if len(v)>0:
          opt = prefix + s.upper() + '_OPTION'
          logger.info('Get option ##: ' + opt)
          r = _get_option(globals()[opt])
          if r is not None:
            cmd.append(_get_option(globals()[opt]))
          cmd.append(v)
      except KeyError as err:
        logger.info('No option for: ' + s)
        continue
    return cmd

def _combine_add_option(paras):
    logger.info('Get valid options for add_device')
    cmd = _combine_option(paras, KEYS_DEVICE, 'ADD_')
    '''if paras['ipv4_address'] is not None:
      cmd.append(paras['ipv4_address'])'''
    return cmd

def _combine_snmp_option(paras):
    logger.info('Get valid options for set_snmp_proxy')
    cmd = _combine_option(paras, KEYS_SNMP, 'SNMP_')
    return cmd

def _combine_change_option(paras):
    logger.info('Get valid options for set_snmp_proxy')
    cmd = _combine_option(paras, KEYS_CHANGE_DEVICE, 'CHANGE_')
    return cmd

'''add prefix p to string s'''
def _add_str_prefix(p, s):
  if p is None:
    return s
  if s is None:
    return p+'None'
  else:
    return p+s

'''get the device confifiguration, add 'test_' as prefix
   to original label, rackid and rack-location
    return {'label':'test_xxx', 'rackid':'test_xxx', 'rack_location':'test'}
'''
def get_change_device_config(paras):
    newparas=paras.copy()
    newparas['new_label'] = _add_str_prefix('test_', newparas['label'])
    newparas['rack_id']= 'z'
    #puremgr add limit to the length of _add_str_prefix('test_', newparas['rack_id'])
    newparas['rack_location']= 'loc'
    #puremgr add limit to the length _add_str_prefix('test_', newparas['rack_location'])

    return newparas


'''paras: command and it's parameters
    return [output, returncode]
'''
def get_cmd_output(paras):
    child = subprocess.Popen(paras, stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    (s, e) = child.communicate()
    result = ((s.decode()).strip()).splitlines()
    logger.info('get_cmd_output' + str(result))
    return (result, child.returncode)


''' paras: configuration for the device
    output:  the output from CMD list_device
example:
    paras = {'label':'rack_switch', 'user':'admin', 'password':'admin', ....}
    output = ['label,rack id,rack location,machine type model,serial number,ipv4 address,userid,device type',
              'rack_switch,,,G8264,MY2120014Y,9.114.200.97,admin,IBM Switch',]
'''
def verify_list_devices(paras, output):
   k = paras[KEY_LABEL]
   item = []
   for s in output:
      t = s.split(',')
      if t[0] == k:
         item = t
         break
   if (len(item) == 0):
      logger.error("No device found for specified label" + paras[KEY_LABEL])
      return 1
   return 0

''' paras should be a key/value paairs,
for example: {'label':'rack_switch', 'user':'admin', 'password':'admin', .....]
'''
def call_add_device_happy(paras):
  logger.info('call command call_add_device_happy()')
  cmd = _combine_add_option(paras)
  cmd.insert(0, CMD_ADD_DEVICE)
  logger.info(cmd)
  rc = subprocess.call(cmd)
  logger.info("command result is: " + str(rc))
  if rc != 0:
    return rc

  print('Wait puremgr service to restart...')
  cmd = [CMD_PUREMGR_SERVICE, 'puremgr', 'reload']
  (output,  rc) = get_cmd_output(cmd)
  return rc

def call_list_devices_happy(paras):
  logger.info('call command call_list_devices_happy()')
  cmd = [CMD_LIST_DEVICES, '-l', paras[KEY_LABEL]]
  logger.info(cmd)
  (result,rc )= get_cmd_output(cmd)
  logger.info("command result is: " + str(rc))
  if rc != 0:
     return rc   # failed to execute command

  rc = verify_list_devices(paras, result)
  return rc

'''verify configuration after change device'''
def verify_change_device(paras):
   cmd = [CMD_LIST_DEVICES]
   (result,rc )= get_cmd_output(cmd)
   k = paras[KEY_LABEL]
   item = []
   for s in result:
      t = s.split(',')
      if t[0] == 'test_'+ k:
         item = t
         break
   if (len(item) == 0):
      logger.error("No device found for changed label test_" + paras[KEY_LABEL])
      return 1

   if item[1] == 'z' and item[2] == 'loc':
      return 0
   else:
      return 1

'''if can't ssh  to the ip address, suppose it is avilable
   if the error is authentication error, suppose it is not available'''
def is_address_available(ip, p=22):
  rc=1
  client = SSHClient()
  client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

  try:
    client.connect(ip, port=p, username='admin', password='admin', timeout=30)
  except paramiko.ssh_exception.AuthenticationException as e:
    pass
  except OSError as e:
    rc=0
    logger.info(e.errno)
  return rc


def call_remove_device_happy(paras):
  logger.info('call command remove_device_happy()')
  cmd = [CMD_REMOVE_DEVICE, '-l', paras[KEY_LABEL]]
  logger.info(cmd)
  rc = subprocess.call(cmd)
  if rc != 0:  
    return rc

  print('Wait puremgr service to restart...')
  cmd = [CMD_PUREMGR_SERVICE, 'puremgr', 'reload']
  (output,  rc) = get_cmd_output(cmd)
  return rc


def call_remote_access_happy(paras):
    logger.info('call command remote_access_happy()')
    cmd = CMD_REMOTE_ACCESS +' -l '+  paras[KEY_LABEL]
    logger.info(cmd)
    try:
        child = pexpect.spawn(cmd)
        child.expect(['>','#'])
        child.sendline('exit')
        child.close()
    except pexpect.EOF:
        return 1
    except pexpect.TIMEOUT:
        return 2
    return 0

def call_set_snmp_proxy_happy(paras):
    logger.info('call command set_snmp_proxy_happy()')
    cmd = _combine_snmp_option(paras)
    cmd.insert(0, CMD_SET_SNMP_PROXY)
    logger.info(cmd)
    rc = subprocess.call(cmd)
    logger.info("command result is: " + str(rc))
    return rc

def call_change_device_password_happy(paras,new_password):
    logger.info('call command change_device() for password')
    cmd = [CMD_CHANGE_DEVICE,'-l',paras[KEY_LABEL],'-p',new_password]
    logger.info(cmd)
    rc = subprocess.call(cmd)
    return rc

def call_change_device_happy(paras):
  logger.info('call command remove_device_happy()')
  newparas = get_change_device_config(paras)
  cmd = _combine_change_option(newparas)
  cmd.insert(0, CMD_CHANGE_DEVICE)
  logger.info(cmd)
  rc = subprocess.call(cmd)
  if rc != 0:
      return rc
  rc = verify_change_device(newparas)

  '''begin restore original label'''
  t=newparas['label']
  newparas['label']=newparas['new_label']
  newparas['new_label']= t
  cmd = _combine_change_option(newparas)
  cmd.insert(0, CMD_CHANGE_DEVICE)
  subprocess.call(cmd)
  '''end restore original label'''
  return rc

def call_change_device_network_happy(paras,new_ip, new_mask=None, new_gateway=None):
    logger.info('call command change_device_network_happy')

    if new_ip is None:
      logger.error('No IP address was specified.')
      return 1
    rc = is_address_available(new_ip)
    if rc ==1:
      logger.error("The ip address is being used: " + new_ip)
      return 1

    cmd = [CMD_CHANGE_DEVICE, 'network','-l',paras[KEY_LABEL],new_ip]
    if new_mask is not None:
      cmd.append(new_mask)
      if new_gateway is not None:
        cmd.append(new_gateway)
    logger.info(cmd)
    rc = subprocess.call(cmd)
    if rc != 0:
      return rc
    rc = is_address_available(new_ip)
    return (rc^1)

def verify_logon_with_ssh(paras,new_password):
    logger.info('call command verify_logon_with_ssh()')
    try:
        ssh = SSHClient()
        ssh.set_missing_host_key_policy(AutoAddPolicy())
        ssh.connect(paras['ipv4_address'], username=paras['user'], password=new_password)
        logger.info('connect successfully.')
    except paramiko.AuthenticationException:
        logger.error('Authenticate failed')
        return 1#authenticate failed
    except paramiko.SSHException:
        return 2
    return 0

def verify_help_message(cmd, options, param='-h'):
    '''
    Parameter:
      cmd: command full path, e.g.: '/opt/ibm/puremgr/bin/add_device', common_function.CMD_ADD_DEVICE
      options: the options to be verified e.g.: ['-a', '-b', '-c', '-t, this is test', '-h, --help']
      param: parameter for the cmd, default '-h'
    Return: (outputString, returnCode)
      outputString: cmd output
      returnCode:
        0: correct
        1: no "Usage:"
        2: no "Options:"
        3: Options doesn't contains all keys
    '''
    logger.info('call command %s %s', cmd, param)
    if isinstance(param, list):
        param.insert(0, cmd)
        child = subprocess.Popen(param, stdout=subprocess.PIPE)
    else:
        child = subprocess.Popen([cmd, param], stdout=subprocess.PIPE)
    (s, rc) = child.communicate()
    s = s.decode().strip()
    result = s.splitlines()
    logger.info('get_cmd_output' + str(result))
    if "Usage:" not in result:
        logger.error('"Usage" not found in help message')
        return (s, 1)
    else:
        logger.debug('"Usage" found in help message')
    if "Options:" not in result:
        logger.error('"Options" not found in help message')
        return (s, 2)
    else:
        logger.debug('"Options" found in help message')
    iBegin = result.index("Options:")
    if options is None or len(options) == 0:
        logger.warn('No options to verify')
        return (s, 0)
    for opt in options:
        found = False
        for i in range(iBegin, len(result)):
            if (result[i].lstrip()).startswith(opt):
                found = True
                logger.debug('Option "%s" found in "%s"', opt, result[i])
                break
        if not found:
            logger.error('Option "%s" not found in help message', opt)
            return (s, 3)
    return (s, 0)

def verify_device_version(paras,version):
    k = paras[KEY_VERSION]
    if(k != version):
        logger.error("Version is not matched" + paras[KEY_VERSION])
        return 1
    return 0

def main(argv):
    print('Do nothing')

if __name__ == '__main__':
    main(sys.argv)
