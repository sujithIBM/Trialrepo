import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
target_host = '127.0.0.1'
target_port = 22
target_port = 22
pwd = 'password'
un = 'root'
ssh.connect( hostname = target_host , username = un, password = pwd )
stdin, stdout, stderr = ssh.exec_command('ls -1 /root|head -n 5')
print("STDOUT:\n%s\n\nSTDERR:\n%s\n" %( stdout.read(), stderr.read() ))
