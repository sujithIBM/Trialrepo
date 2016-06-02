from selenium import webdriver


driver = webdriver.Firefox()
'''driver.get("http://www.flipkart.com/programming-python-4th-e-d/p/itmczzj4gpfrr6bs?pid=9789350232873&icmpid=reco_pp_hSame_book_1")
data=[]
for tr in driver.find_elements_by_xpath('//table[@class="mprod-similar-prod-table"]//tr'):
  tds=tr.find_elements_by_tag_name('td')
  if tds: 
    data= [td.text for td in tds]
print "3730" in data[2] #or whatever is the current price
'''


url = "http://www.psacard.com/smrpriceguide/SetDetail.aspx?SMRSetID=1055"

driver.get(url)
driver.implicitly_wait(10)

SMRtable = browser.find_element_by_xpath('//*[@class="set-detail-table"]/tbody')

for i in SMRtable.find_element_by_xpath('.//tr'):
    print i.get_attribute('innerHTML')

browser.close()
