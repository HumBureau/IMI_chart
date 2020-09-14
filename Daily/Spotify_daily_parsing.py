#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# данный скрипт:

# парсит ежедневный чарт Спотифай 200
# это нужно для оценки популярности песен, не попавших в другие ежедневные чарты в некоторые дни недели
# речь идет других о ежедневных чартах (Apple Music, VK, Deezer) и о рассчитывании их еженедельных чартов
# причина - в спотифае есть 200 строк, а в вышеупомянутых - 100.

## - должен запускаться каждый день один раз в сутки в 15:40 по мск. 

#на выходе:
## обновляет all_daily_spotify.csv
### затем этот файл используется в Make_daily_charts.py


# In[1]:


import pandas as pd
import re
import requests
from bs4 import BeautifulSoup
from time import sleep
from random import randint
from datetime import datetime, date, time, timezone
from dateutil.relativedelta import relativedelta


# In[2]:


#задаем команду для получения даты
currentDT = datetime.now() 


# In[3]:


#базовая ссылка на последний актуальный еженедельный чарт по России
base_url = 'https://spotifycharts.com/regional/ru/daily/latest'
r = requests.get(base_url)
#на всякий случай поставим на паузу
sleep(randint(1,3))
soup = BeautifulSoup(r.text, 'html.parser')
chart = soup.find('table', {'class': 'chart-table'})
tbody = chart.find('tbody')
all_rows = []


#сам скрэйпинг
for tr in tbody.find_all('tr'):
    #позиция трека
    rank_text = tr.find('td', {'class': 'chart-table-position'}).text
    #артист
    artist_text = tr.find('td', {'class': 'chart-table-track'}).find('span').text
    artist_text = artist_text.replace('by ','').strip()
    #название трека
    title_text = tr.find('td', {'class': 'chart-table-track'}).find('strong').text
    #кол-во стримов для трека
    streams_text = tr.find('td', {'class': 'chart-table-streams'}).text
    #cборка таблицы (цикл на случай парсинга нескольких чартов)
    all_rows.append( [rank_text, title_text, artist_text, streams_text] )
    
#создаем читаемый датафрейм в pandas
daily_spotify_top_200 = pd.DataFrame(all_rows, columns =['rank','title', "artist",'streams'])
#записываемая дата = предыдущий день! (как и значится в самом спотифае)
date = currentDT - relativedelta(days=+1)
daily_spotify_top_200["date"] = datetime.strftime(date,"%d/%m/%Y")  


# In[4]:


#берем имеющийся csv файл и обновляем его

all_daily_spotify = pd.read_csv("all_daily_spotify.csv")
all_daily_spotify = all_daily_spotify.drop(all_daily_spotify.columns[[0]], axis=1) #удаляем получающуюся после импорта лишнюю колонку 
frames = [all_daily_spotify, daily_spotify_top_200]
all_daily_spotify = pd.concat(frames, sort=False)
all_daily_spotify.to_csv("all_daily_spotify.csv", encoding = "utf-8")


# In[ ]:




