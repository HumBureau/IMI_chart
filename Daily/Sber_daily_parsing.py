#!/usr/bin/env python
# coding: utf-8

# In[8]:


# Данный скрипт ежедневно скрейпит топ 100 Сберзвука

# время запуска: 18:25 МСК
# ВАЖНО: записываемая дата = день скрейпинга


# In[97]:


import pandas as pd
import re
import requests
from bs4 import BeautifulSoup
from time import sleep
from random import randint
from datetime import datetime
from dateutil.relativedelta import relativedelta
from os import path


# In[98]:


currentDT = datetime.now() 


# In[99]:


base_url = 'https://sber-zvuk.com/top100'
r = requests.get(base_url)

soup = BeautifulSoup(r.text, 'html.parser')
s = str(soup)
songs = [i.strip('"') for i in re.findall(r'"title":\s*(.*?)\s*\,', s)[1:101] ]
songs = [" ".join(i.split("\xa0")) for i in songs]
songs = [" & ".join(i.split(" \\u0026 ")) for i in songs]

artists = [i.strip('"') for i in re.findall(r'(?<="credits":")(.*?)(?=",)', s)[:100] ]
artists = [" & ".join(i.split(" \\u0026 ")) for i in artists]


data = {"rank": [i for i in range(1, len(songs)+1)], "title": songs, "artist":artists}
sber = pd.DataFrame(data)


# In[100]:


date = currentDT 
sber["date"] = datetime.strftime(date,"%d/%m/%Y")  


# In[102]:


# берем имеющийся csv файл и обновляем его
if path.exists("all_sber.csv") == True:
    all_sber = pd.read_csv("all_sber.csv")
    all_sber = all_sber.drop(all_sber.columns[[0]], axis=1) # удаляем получающуюся после импорта лишнюю колонку 
    
    # чистим дубликаты (опыт показал, что они бывают)
    all_sber.drop_duplicates(inplace= True)
    all_sber.reset_index(inplace=True)
    all_sber.drop(all_sber.columns[[0]], axis=1, inplace=True)
    
    if datetime.strftime(date, "%d/%m/%Y") in set(all_sber["date"]):
        print("this date's SBER chart is already in the data. I expect the new scrip to be superior so I am overwriting the old data.")
        all_sber = all_sber[all_sber["date"]!=datetime.strftime(date,"%d/%m/%Y")]
    else:
        print("this date's SBER chart is not in our data yet. I proceed to save it.")
    
    frames = [all_sber, sber]
    all_sber = pd.concat(frames, sort=False)
    all_sber.to_csv("all_sber.csv", encoding = "utf-8")
else:
    sber.to_csv("all_sber.csv", encoding = "utf-8")


# In[ ]:




