from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait 
import time
import random
import sys,re

driver = webdriver.Firefox()

driver.get("http://tinyurl.com/2bp99mm")
inputElement = driver.find_element_by_name( "QUERY" )
inputElement.send_keys("EWQLVLNVWGKVEADIPGHGQEVLIRLFKGHPETLEKFDKFKHLKSEDEMKASEDLKKHGATVLTALGGILKKKGHHEAEIKPLAQSHATKHKIPVKYLEFISECIIQVLQSKHPGDFGADAQGAMNKALELFRKDMASNYKELGFQG")##str(seq2))

inputElement.submit()
# the page is ajaxy so the title is originally this:
print(driver.title)

driver.implicitly_wait(30)

click_event = driver.find_element_by_link_text("3RGK_A")
click_event.click()
