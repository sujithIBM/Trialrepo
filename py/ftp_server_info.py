import ftplib

#Open ftp connection
ftp = ftplib.FTP('ftp.novell.com', 'anonymous',
'bwdayley@novell.com')

#List the files in the current directory
print("File List:")
files = ftp.dir()
print(files)

