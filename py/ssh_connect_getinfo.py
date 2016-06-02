import paramiko

sftpURL   =  'ftp.novell.com'
sftpUser  =  'anonymous'
sftpPass  =  'bwdayley@novell.com'

ssh = paramiko.SSHClient()
# automatically add keys without requiring human intervention
ssh.set_missing_host_key_policy( paramiko.AutoAddPolicy() )

ssh.connect(sftpURL, username=sftpUser, password=sftpPass)

ftp = ssh.open_sftp()
files = ftp.listdir()
print(files)
