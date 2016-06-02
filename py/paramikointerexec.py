import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

ssh.connect('9.3.46.208',username = 'root',password='PASSW0RD')

stdin, stdout,stderr =ssh.exec_command('cd /opt/ibm/puremgr/etc')
stdin, stdout,stderr =ssh.exec_command('ll')

output= stdout.readlines()
print('\n'.join(output))
ssh.close

'''
channel = ssh.invoke_shell()
channel.recv(9999)
cahnnel.recv_ready()


whie True:
if channel.recv_ready():
cahnnel_data += channel.recv(9999)
else:
continue

if channel_data.endswith('
