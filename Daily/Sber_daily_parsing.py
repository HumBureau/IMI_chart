#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# Данный скрипт ежедневно скрейпит топ 100 Сберзвука

# время запуска: 18:25 МСК
# ВАЖНО: записываемая дата = день скрейпинга


# In[ ]:


import pandas as pd
import re
import requests
from bs4 import BeautifulSoup
from time import sleep
from random import randint
from datetime import datetime
from dateutil.relativedelta import relativedelta
from os import path
import json


# In[ ]:


def get_genre_label(url):
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser') 
    nd = soup.findAll('script', attrs={'id':'__NEXT_DATA__'})[0]
    textValue = nd.contents[0]
    jsonValue = '{%s}' % (textValue.partition('{')[2].rpartition('}')[0],)
    value = json.loads(jsonValue)
    genre = ", ".join([i['name'] for i in value['props']['pageProps']['release']['genres']])
    label = value['props']['pageProps']['release']['label']['title']
    
    return genre, label


# In[ ]:


currentDT = datetime.now() 


# In[ ]:


base_url = 'https://sber-zvuk.com/top100'
r = requests.get(base_url)

soup = BeautifulSoup(r.text, 'html.parser')
s = str(soup)
nd = soup.findAll('script', attrs={'id':'__NEXT_DATA__'})[0]
textValue = nd.contents[0]
jsonValue = '{%s}' % (textValue.partition('{')[2].rpartition('}')[0],)
value = json.loads(jsonValue)

# некрасивая и хрупкая строчка вызвана тем, что в словаре чарт лежит под ключом равным (возможно изменяемому) id плейлиста
full_chart_data_list = list(value['props']['pageProps']['grid']['playlists'].items())[0][1]["tracks"]

songs = [i["title"] for i in full_chart_data_list]
artists = [i["credits"] for i in full_chart_data_list]
release_ids = [str(i['release_id']) for i in full_chart_data_list]

genres = []
labels = []
for i in release_ids:
    url= 'https://sber-zvuk.com/release/'+i
    outp = get_genre_label(url)
    genres.append(outp[0])
    labels.append(outp[1])

cols = ["rank", "title", "artist", 'date', 'genre', 'label']

data = dict(zip(cols, [[i for i in range(1, len(songs)+1)], songs, artists, [datetime.strftime(currentDT,"%d/%m/%Y") for i in range(1, len(songs)+1)],genres,labels]))
sber = pd.DataFrame(data)


# In[ ]:


date = currentDT 

# берем имеющийся csv файл и обновляем его
if path.exists("all_sber.csv") == True:
    all_sber = pd.read_csv("all_sber.csv")
    all_sber = all_sber.drop(all_sber.columns[[0]], axis=1) # удаляем получающуюся после импорта лишнюю колонку 
    
    # чистим дубликаты (опыт показал, что они бывают)
    all_sber.drop_duplicates(inplace= True)
    all_sber.reset_index(inplace=True)
    all_sber.drop(all_sber.columns[[0]], axis=1, inplace=True)
    
    if datetime.strftime(date, "%d/%m/%Y") in set(all_sber["date"]):
        print(date, ": this date's SBER chart is already in the data. I expect the new script to be superior so I am overwriting the old data.")
        all_sber = all_sber[all_sber["date"]!=datetime.strftime(date,"%d/%m/%Y")]
    else:
        print(date, ": this date's SBER chart is not in our data yet. I proceed to save it.")
    
    frames = [all_sber, sber]
    all_sber = pd.concat(frames, sort=False, ignore_index=True)
    all_sber.to_csv("all_sber.csv", encoding = "utf-8")
else:
    sber.to_csv("all_sber.csv", encoding = "utf-8")

