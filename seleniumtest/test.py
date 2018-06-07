#coding:utf-8

import time
from selenium import webdriver

#手动进行chromedriver驱动路径添加
# googledriver = "D:/googleDriver/chromedriver.exe"
# os.environ["webdriver.chrome.driver"] = googledriver

#调用python-scripts中的Googledriver驱动
# driver = webdriver.Chrome()

driver = webdriver.PhantomJS()

driver.get("https://baidu.com")
print(driver.page_source)
time.sleep(5)
driver.quit()