#!/usr/bin/env python
# coding: utf-8

# In[1]:


import re
import requests
from time import sleep
from random import randint
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options


# In[ ]:


### MANUAL ONE-TIME LOGIN ###
chrome_options = Options()
chrome_options.add_argument("--user-data-dir=chrome-data")
driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
chrome_options.add_argument("user-data-dir=chrome-data") 
driver.get('https://www.vk.com')
sleep(30)  # Time to enter credentials
driver.quit()

