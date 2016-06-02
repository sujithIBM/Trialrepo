#!/usr/local/bin/python3.4
# Licensed Materials - Property of IBM
#
# (C) Copyright IBM Corp. 2015 All Rights Reserved
#
# US Government Users Restricted Rights - Use, duplicate or
# disclosure restricted by GSA ADP Schedule Contract with
# IBM Corp.

import gettext
# establish _ in global namespace
gettext.install('puremgr', '/usr/share/locale')

import getopt
import getpass
import sys
import flrt_query
import update_mgr
import persistent_mgr
import logging
import utils

# Connection types
PPIM_ONLINE = _("online")   # PPIM can access internet
PPIM_PROXY = _("proxy")   # PPIM can access a remote/proxy machine through SSH and that remote machine can access internet
PPIM_OFFLINE = _("offline") # No access to internet. Not even through remote machine.


def set_compliance_config_help():
    msg = _('Usage:\n')
    msg += _('  set_compliance_config [-c|-i|-u]\n')
    msg += _('  Set configuration for querying PurePower stack definitions.\n\tInformation about stack definitions is used for assessing compliance \n\tof firmware or software versions installed in the devices.\n')
    msg += _('  set_compliance_config -c <connection-type>\n')
    msg += _('  Connection type can be %(type_online)s, %(type_proxy)s or %(type_offline)s\n') % {"type_online":PPIM_ONLINE, "type_proxy":PPIM_PROXY, "type_offline":PPIM_OFFLINE}
    msg += _('  set_compliance_config -i <proxy-machine-ip-address>\n')
    msg += _('  IP address of the proxy machine that is to be used to query\n\tonline tool to get PurePower stack definitions. This option\n\tis ignored if connection type is not %(type_proxy)s.\n') %{"type_proxy":PPIM_PROXY}
    msg += _('  set_compliance_config -u <remote-machine-userid>\n')
    msg += _('  Userid of the proxy machine that is to be used to query\n\tonline tool to get PurePower stack definitions. This option\n\tis ignored if connection type is not %(type_proxy)s.\n') % {"type_proxy":PPIM_PROXY}


    msg += _('  set_compliance_config -f <fixCentral_IBM_ID>\n')
    msg += _('  Fix central IBM ID that is to be used for authentication to download the update id \n\tonline tool to get PurePower stack definitions. This option\n\tis ignored if connection type is not %(type_proxy)s.\n') %{"type_proxy":PPIM_PROXY}
    msg += _('  set_compliance_config -d <download_location>\n')
    msg += _('  download location is to be used to tell the loaction of the updateId getting downloaded \n\tonline tool to get PurePower stack definitions. This option\n\tis ignored if connection type is not %(type_proxy)s.\n') % {"type_proxy":PPIM_PROXY}
    msg += _('  set_compliance_config -p <progress_refresh_interval>\n')
    msg += _('  progress_refresh_interval is to be used to know the download percent of updateId \n\tonline tool to get PurePower stack definitions. This option\n\tis ignored if connection type is not %(type_proxy)s.\n') % {"type_proxy":PPIM_PROXY}

    msg += _('  \n')
    msg += _('Options:\n')
    msg += _('  -c, --connectiontype type\tThe connection type of Pure Power Integrated Manager.\n\t\t\tThe value can only be one of the 3 values:\n\t\t\t\t%(type_online)s - PPIM has access to internet,\n\t\t\t\t%(type_proxy)s - PPIM has access to a proxy machine through SSH and the proxy machine has access to internet\n\t\t\t\t%(type_offline)s - no internet access at all\n') % {"type_online":PPIM_ONLINE,"type_proxy":PPIM_PROXY,"type_offline":PPIM_OFFLINE}
    msg += _('  -i, --ip ip address\tIP address of the proxy machine that is to be used to query\n\t\t\tonline tool to get PurePower stack definitions. This option\n\t\t\tis ignored if connection type is not %(type_proxy)s.\n') % {"type_proxy":PPIM_PROXY}
    msg += _('  -u, --userid userid\tUserid of the proxy machine that is to be used to query\n\t\t\tonline tool to get PurePower stack definitions. This option\n\t\t\tis ignored if connection type is not %(type_proxy)s.\n') % {"type_proxy":PPIM_PROXY}

    msg += _('  -f, --fixCentral_IBM_ID fixCentral_IBM_ID\t fix central ibm_id is used for authentication to download the update id\n\t\t\tonline tool to get PurePower stack definitions.   ')
    msg += _('  -d, --download_location download_location\t download_location is used for loacating the download \n\t\t\tonline tool to get PurePower stack definitions. ')
    msg += _('  -p, --progress_refresh_interval progress_refresh_interval\t progress indiactes the percentage of download done .\n\t\t\tonline tool to get PurePower stack definitions.   ')

    msg += _('  -h, --help\t\tDisplays this help message\n')
    msg += _('  Note: In the proxy mode, the set_compliance_config command retrieves PurePower stack definitions from Fix Level Recommendations Tool through the proxy machine.')
    return msg


def set_compliance_config_cli(argv):
    _METHOD_ = 'set_compliance_config.set_compliance_config_cli'
    SHORT_OPTIONS = "c:i:u:f:d:p:h"
    LONG_OPTIONS = ['connectiontype=', 'ip=', 'userid=', 'fixCentral_ibm_id= ' , 'download_location= ' , 'progress_refresh_interval', 'help']
    try:
        opts, args = getopt.getopt(argv, SHORT_OPTIONS, LONG_OPTIONS)
    except getopt.GetoptError as err:
        message = str(err)
        return -1, message

    # remote machine is proxy machine which has access to internet and thus access to FLRT
    connection_type = ''
    remote_machine_ip = None
    remote_machine_userid = None
    remote_machine_encrypted_password = None

    if args:
        return -1, set_compliance_config_help()
    for o, a in opts:
        if o in ('-h', '--help'):
            return -1, set_compliance_config_help()
        elif o in ('-c', '--connectiontype'):
            connection_type = a
        elif o in ('-i', '--ip'):
            remote_machine_ip = a
        elif o in ('-u', '--userid'):
            remote_machine_userid = a

    if connection_type:
        if connection_type != PPIM_ONLINE and connection_type != PPIM_OFFLINE and connection_type != PPIM_PROXY:
            msg = _("Wrong value for -c option given.\n\n")
            msg += set_compliance_config_help()
            return -2, msg

        rc = 0
        msg = _("Success")
        if connection_type == PPIM_PROXY:
            if remote_machine_ip == None or remote_machine_userid == None:
                msg = _("Missing argument(s): remote machine's  ip or userid. Use -i and -u options.\n\n")
                msg += set_compliance_config_help()
                return -3, msg
            # Ask for password and read it
            remote_machine_password = getpass.getpass(_("Remote machine's password:"))
            if not remote_machine_password:
                error_message = _("Please input a valid password and retry the command.")
                return -4, error_message
            remote_machine_encrypted_password = persistent_mgr.encryptData(remote_machine_password)

        # Set details in the config file
        rc, msg = update_mgr.set_compliance_config(connection_type, remote_machine_ip, remote_machine_userid, remote_machine_encrypted_password)

        if rc == 0 and connection_type == PPIM_PROXY:
            # Create package if not already there
            rc, local_path = update_mgr.get_offline_flrt_tarfile()
            if rc == 0:
                # Copy the package to the remote/online machine
                pkg_name = utils.get_filename_from_path(local_path)
                remote_path = "/tmp/" + pkg_name
                rc = utils.copyFileToRemoteMachine(remote_machine_ip, remote_machine_userid, remote_machine_password, local_path, remote_path)
                if rc == 0:
                    # Run script on the remote machine and the script generates the stack definitions file
                    rc = update_mgr.generate_stack_definition_remotely(remote_machine_ip, remote_machine_userid, remote_machine_password, remote_path)
                    if rc == 0:
                        # Copy the generated stack definitions file from the remote machine to puremgrVM
                        rc= utils.copyFileFromRemoteMachine(remote_machine_ip, remote_machine_userid, remote_machine_password, update_mgr.STACK_DEFINITIONS_PROXY_TMP_FILE, update_mgr.STACK_DEFINITIONS_TMP_FILE)
                        utils.change_file_ownership_and_permission(update_mgr.STACK_DEFINITIONS_PROXY_TMP_FILE)
                        if rc == 0:
                            rc, msg = update_mgr.backup_and_overwrite_stack_definition_file(update_mgr.STACK_DEFINITIONS_PROXY_TMP_FILE)
                            if rc == 0:
                                msg = _('Stack definition generated successfully in the remote machine')
                        else:
                             msg = _('Could not copy remote file to local machine')
                    else:
                        msg = _('Stack definition file could not be generated in the remote machine')
                else:
                    msg = _('Could not copy file to remote machine')
            else:
                msg = _('Tar file is not generated successfully')
        elif rc == 0 and connection_type == PPIM_OFFLINE:
            # Create package if not already there
            rc1, local_path = update_mgr.get_offline_flrt_tarfile()
            if rc1 != 0:
                logging.warning("%s:: Tar file is not generated successfully", _METHOD_)
    return rc, msg

if __name__ == '__main__':
    logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s",filename="/var/log/puremgr.log", level=logging.INFO)
    rc, message = set_compliance_config_cli(sys.argv[1:])
    if message:
        print(message)
    exit(rc)
