#!/usr/bin/env python
# coding: utf-8

# In[1]:


# данный скрипт проходит СМС авторизацию ВК и сохраняет куки


# In[2]:


import re
import requests
from time import sleep
from random import randint
from selenium import webdriver
from webdriver_manager.firefox import GeckoDriverManager
import pickle
from selenium.webdriver.firefox.options import Options


# In[ ]:


# LOGIN WITH AUTH CODE
options = Options()
options.add_argument('-headless')
br = webdriver.Firefox(executable_path=GeckoDriverManager().install(), options=options)
br.get('http://vk.com/')
sleep(9)  # Time to enter credentials
e_mail_window = br.find_element_by_css_selector("#index_email")
password_window = br.find_element_by_css_selector("#index_pass")
login_vk = input('Введите логин: ')
password_vk = input('Введите пароль: ')
e_mail_window.send_keys(login_vk)
password_window.send_keys(password_vk)
button1 = br.find_element_by_xpath('//*[(@id = "index_login_button")]')
button1.click()

if br.current_url == "https://vk.com/login?act=authcheck":
    print("script is forced to go through SMS authorisation")
    code = input("enter authorisation code from SMS: ")
    code_window = br.find_element_by_css_selector("#authcheck_code")
    code_btn = br.find_element_by_css_selector("#login_authcheck_submit_btn")
    code_window.send_keys(code)
    code_btn.click()
    sleep(2)
    pickle.dump(br.get_cookies(), open("vkcooks.pkl", "wb"))
    print('cookies are saved to vkcooks.pkl')

else:
    print("don't know why, but no SMS authorisation this time")
    if br.current_url == "https://vk.com/feed":
        print("succesful login")
        sleep(2)
        pickle.dump(br.get_cookies(), open("vkcooks.pkl", "wb"))
        print('cookies are saved to vkcooks.pkl')
    else:
        print("unsuccesful login. reason unknown.")

br.quit()
