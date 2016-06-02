import paramiko
print("4")
client = paramiko.SSHClient()
print("5")
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
print("6")
client.connect('9.12.33.102', username='padmin', password='eserve1a')
#client.connect('9.12.32.204', username='padmin', password='eserve1a')
print("2")
stdin, stdout, stderr = client.exec_command('ls')

#stdin, stdout, stderr = client.exec_command('oem_setup_env')
#print("1")
#stdin, stdout, stderr = client.exec_command('emgr -l')
#print("3")
output = stdout.readlines()
print(output)
client.close()

                                            
