#//device_type: Brocade;PowerVC;Mellanox_Switch;HMC;RHEL;PDU;SVC;Nagios_core;VIOS;IBM_Switch

IBM_Switch:
  Device_01:
    InitSetting:
    - label: rack_switch
      rack_id: a
      rack_location: loc
      machine type model:
      serial_number:
      ipv4_address: 9.114.200.97
      user: admin
      password: admin
      device_type: IBM_Switch
    NewSetting:
    - label: new_rack
      rack_id: 9
      rack_location: 121
      ipv4_address: 9.114.200.99
      user:
      password: newPassw0rd
      netmask:
      gateway:

Mellanox_Switch:
  Device_01:
    InitSetting:
    - label: mellanox_switch
      rack_id: a
      rack_location: loc
      machine type model:
      serial_number:
      ipv4_address: 9.114.147.164
      user: admin
      password: admin
      device_type: Mellanox_Switch
    NewSetting:
    - label: new_mellanox
      rack_id:
      rack_location:
      ipv4_address:
      user:
      password: newPassw0rd
      netmask:
      gateway:

SVC:
  Device_01:
    InitSetting:
    - label: V7000
      rack_id: b
      rack_location: POK
      machine type model: 0000
      serial_number: 1234567
      ipv4_address: 9.114.44.11
      user: superuser
      password: stor1virt
      device_type: SVC
    NewSetting:
    - label: new_v7000
      rack_id:
      rack_location:
      ipv4_address:
      user:
      password: newPassw0rd
      netmask:
      gateway:

Brocade:
  Device_01:
    InitSetting:
    - label: san_switch
      rack_id: c
      rack_location: pok
      machine type model:
      serial_number:
      ipv4_address: 9.114.202.232
      user: USERID
      password: Passw0rd
      device_type: Brocade
    NewSetting:
    - label: new_Brocade
      rack_id:
      rack_location:
      ipv4_address:
      user:
      password: newPassw0rd
      netmask:
      gateway:

HMC:
  Device_01:
    InitSetting:
    - label: HMC_217
      rack_id: d
      rack_location: HMC
      machine type model: 0000
      serial_number: XXXX
      ipv4_address: 9.12.29.217
      user: hscroot
      password: abc1234
      device_type: HMC
      version: 8.2.0
    NewSetting:
    - label: new_HMC
      rack_id:
      rack_location:
      ipv4_address:
      user:
      password: newPassw0rd
      netmask:
      gateway:

RHEL:
  Device_01:
    InitSetting:
    - label: rhel7
      rack_id: e
      rack_location: rhe
      machine type model: 0000
      serial_number: XXXX
      ipv4_address: 9.114.104.234
      user: root
      password: d0ntknow
      device_type: RHEL
    NewSetting:
    - label: new_RHEL7
      rack_id:
      rack_location:
      ipv4_address:
      user:
      password: newPassw0rd
      netmask:
      gateway:

PDU:
  Device_01:
    InitSetting:
    - label: PDU3
      ipv4_address: 192.168.93.27
      rack_id:
      rack_location:      
      user: USERID
      password: passw0rd
      device_type: PDU
    NewSetting:
    - label: new_PDU
      rack_id:
      rack_location:
      ipv4_address:
      user:
      password: newPassw0rd
      netmask:
      gateway:

#Add pure power manager server configuration
Puremgr:
    - ipv4_address: 9.114.206.36
      user: root
      password: PASSW0RD
      version: 1.0.0
      build: 20150615-1330
      bsoid: isdsvt@us.ibm.com
      bsopw: Passw2rd

#Add Nagios server configuration
Nagiosmgr:
    - ipv4_address: 9.114.206.36
      user: nagiosadmin
      password: PASSW0RD
      bsoid: isdsvt@us.ibm.com
      bsopw: Passw2rd
