import os
import sys
import getopt
import unittest
import logging
import common_function as cf
import get_configuration

import paramiko
import socket
import time

import pureresult
from pureresult import pureTestCase
import re


myfile = open ('c:\ListDevices.txt','r')
myfile.read()

match = re.search(arg, myfile)

match = re.search(r'(?:(\d+)\.)?(?:(\d+)\.)?(?:(\d+)\.)?(?:(\d+)\.)', myfile)
  if match:                      
    print 'found', match.group() 
  else:
    print 'did not find'
