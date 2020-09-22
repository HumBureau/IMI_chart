#!/usr/bin/env python
# coding: utf-8

# In[1]:


from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from time import sleep
from webdriver_manager.firefox import GeckoDriverManager
import pickle
import re
import requests


# In[ ]:


### MANUAL FIRST-TIME LOGIN ###
options = Options()
browser = webdriver.Firefox(executable_path=GeckoDriverManager().install())
browser.get('http://vk.com/')
sleep(30)  # Time to enter credentials
pickle.dump(browser.get_cookies(), open("vkcooks.pkl", "wb"))
browser.quit()
