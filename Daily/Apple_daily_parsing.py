#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# данный скрипт: 


## - осуществляет парсинг ежедневных чартов
### - через requests: Apple Music

## - должен запускаться каждый день один раз в сутки. Самое раннее - в 11:30 утра.

## Справка: время обновления исходных чартов.
### Apple Music: 12 a.m. PST  =  10 a.m. Moscow (летом) = 11 a.m. Moscow (зимой)
#### => обновлять в 11:30 утра по Москве


## - на выходе:
### - обновляет all_apple.csv


# In[1]:


import pandas as pd
import re
import requests
from bs4 import BeautifulSoup
from time import sleep
from random import randint
from datetime import datetime
from dateutil.relativedelta import relativedelta


# In[2]:


# задаем команду для получения даты
currentDT = datetime.now() 


# ### Apple Music

# In[9]:


base_url = 'https://music.apple.com/ru/playlist/top-100-russia/pl.728bd30a9247487c80a483f4168a9dcd'
r = requests.get(base_url)
sleep(randint(3,5))
soup = BeautifulSoup(r.text, 'html.parser')

all_texts = soup.findAll('div', attrs={'class':"row track web-preview song"})
a_l=[]
s_l=[]
labels_l = []
genres_l = []

for i in all_texts:
    # check if empty artist name
    if len(i.findAll('div', attrs={'class':'by-line typography-caption'})) == 0:
        a = ""
        a_l.append(a)
    else:
        a = i.findAll('div', attrs={'class':'by-line typography-caption'})
        ar_l = [j.rstrip().lstrip() for j in a[0].get_text().rstrip().lstrip().split(",")]
        a = ", ".join(ar_l)
        a_l.append(a)
    s = i.findAll('div', attrs={'class':'song-name typography-label'})[0].get_text()
    s = s.replace("\n", "")
    s = s.replace("[", "")
    s = s.replace("]", "")
    s = s.strip(" ")
    s_l.append(s)
    
    ## get label and genre
    # для этого получаем ссылки на страницы с альбомами
    alb_link = i.findAll('div', attrs={'class':'song-album-wrapper'})[0].a["href"]
    r = requests.get(alb_link)
    soup = BeautifulSoup(r.text, 'html.parser')
    try:
        labels_l.append(soup.findAll('p', attrs={'class':'song-copyright typography-footnote-emphasized'})[0].get_text())
    except:
        print("label not found")
        labels_l.append("")
    try:
        g = soup.findAll('h3', attrs={'class':'product-meta typography-footnote-emphasized'})[0].get_text()
        genres_l.append(g.split("·")[0].strip())
    except:
        print("genre not found")
        genres_l.append("") 

apple_music_top_100_daily = pd.DataFrame()
apple_music_top_100_daily['title'] = s_l
apple_music_top_100_daily['artist'] = a_l
apple_music_top_100_daily['rank'] = apple_music_top_100_daily.reset_index().index +1
apple_music_top_100_daily = apple_music_top_100_daily[['rank', 'title', 'artist']]

apple_music_top_100_daily["genre"] = genres_l
apple_music_top_100_daily["label"] = labels_l

# дата = предыдущий день (относительно дня скрейпинга)
date = currentDT - relativedelta(days=+1)
apple_music_top_100_daily["date"] = datetime.strftime(date,"%d/%m/%Y")  


# In[ ]:


# берем имеющийся csv файл и обновляем его

all_apple = pd.read_csv("all_apple.csv")
all_apple = all_apple.drop(all_apple.columns[[0]], axis=1) # удаляем получающуюся после импорта лишнюю колонку 

# чистим дубликаты (опыт показал, что они бывают)
all_apple.drop_duplicates(inplace= True)
all_apple.reset_index(inplace=True)
all_apple.drop(all_apple.columns[[0]], axis=1, inplace=True)


now = datetime.now()

# проверяем, не сохраняли ли мы уже данные за этот день:
if datetime.strftime(date, "%d/%m/%Y") in set(all_apple["date"]):
    print(now, ": this date's Apple Music data is already saved. Not saving new data.")
else:
    print(now, ": this date's Apple Music chart is not in our data yet. I proceed to save it and export to csv.")
    frames = [all_apple, apple_music_top_100_daily]
    all_apple = pd.concat(frames, sort=False)
    all_apple.reset_index(inplace = True)
    all_apple = all_apple.drop(all_apple.columns[[0]], axis=1)  
    all_apple.to_csv("all_apple.csv", encoding = "utf-8")

