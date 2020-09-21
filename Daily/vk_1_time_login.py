#!/usr/bin/env python
# coding: utf-8

# In[1]:


import re
import requests
from time import sleep
from selenium import webdriver
from webdriver_manager.firefox import GeckoDriverManager
import pickle 


# In[ ]:


### MANUAL ONE-TIME LOGIN ###
options = Options()
options.add_argument('-headless')
browser = webdriver.Firefox(executable_path=GeckoDriverManager().install())
browser.get('http://vk.com/')
sleep(30)  # Time to enter credentials
pickle.dump(browser.get_cookies() , open("vkcooks.pkl","wb")) 
browser.quit()

