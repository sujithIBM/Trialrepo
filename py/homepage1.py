data=[['Filter'],
['Label', 'Type', 'Rack - EIA Location', 'Machine Type/Model', 'IP Address', 'Installed Version'],
['puremgr4', 'Nagios Core', '4 - U6', 'KVM', '9.3.46.208', '1.2.0'],
['Total: 1'],
['Filter'],
['Label', 'Type', 'Rack - EIA Location', 'Machine Type/Model', 'IP Address', 'Installed Version'],
['powervc4', 'PowerVC', '4 - U6', 'KVM', '9.3.46.210', '1.2.3.1'],
['Total: 1'],
['Filter'],
['Label', 'Type', 'Rack - EIA Location', 'Machine Type/Model', 'IP Address', 'Installed Version'],
['IBM_Switch1', 'Lenovo OEM Switch', 'z - loc', '7120-48E', '9.114.200.99', '7.11.2'],
['Mellanox1', 'Mellanox Switch', '4 - U20', 'MSX1710', '192.168.93.37', '3.4.1120'],
['PDU1', 'Power Distribution Unit', '4 -', '00FW789', '192.168.93.25', ' '],
['V7K4', 'V7000', '4 - U12', '2076-524', '192.168.93.8', '7.4.0.5'],
['VIOS1', 'Virtual I/O Server', '4 - U2', ' ', '192.168.93.89', '2.2.3.52'],
['hmc', 'Hardware Management Console', '4 -', '8374-01M', '9.3.46.190', '8.3.0'],
['Total: 9'],
['Filter'],
['Label', 'Type', 'Rack - EIA Location', 'Machine Type/Model', 'IP Address', 'Installed Version'],
['hmc4-imm', 'Integrated Management Module', '4 - U7', '837401M', '9.3.46.189', '4.56'],
['purekvm4-imm', 'Integrated Management Module', '4 - U6', '7914AC1', '9.3.46.206', '4.56'],
['Total: 2']]

converged=[]
virtual=[]
hardware=[]
unmonitored=[]

print(len(data))

i=0
while i<len(data):
    if i>1 and i<3:
        converged.append(data[i])
    elif i>5 and i<7:
        virtual.append(data[i])
    elif i>9 and i<16:
        hardware.append(data[i])
    elif i>18 and i<21:
        unmonitored.append(data[i])
    i+=1
print(converged)
print(hardware)
print(virtual)
print(unmonitored)
