#!/usr/bin/env python
# coding: utf-8

# In[19]:


#данный скрипт:

## парсит чарт Deezer (https://www.deezer.com/en/playlist/1116189381)
## периодичность - 20 минут 
### все это нужно потому, что чарт не обновляется в известное фиксированное время

# Время запуска скрипта: 00:01 каждый день

#на выходе:
## если находит новый чарт, обновляет csv all_deezer


# In[5]:


import pandas as pd
import re
import requests
from bs4 import BeautifulSoup
from time import sleep
from random import randint
from dateutil.relativedelta import relativedelta
from datetime import datetime


# In[ ]:


#грузим данные за предыдущий день
all_deezer = pd.read_csv("all_deezer.csv")
all_deezer = all_deezer.drop(all_deezer.columns[[0]], axis=1) #удаляем получающуюся после импорта лишнюю колонку 
old_df=all_deezer[-100:]
o_l = list(old_df["title"])
    
    
    #базовая ссылка на последний актуальный ежедневный чарт по России
request_deezer = requests.get('https://api.deezer.com/playlist/1116189381') #ссылка на постоянный плейлист
deezer_chart_json = request_deezer.json() #через API получаем json 
new_df = pd.DataFrame(deezer_chart_json['tracks']['data']) #выбираем только список треков
artists_deezer_top = [] #поскольку имена артистов "запакованы", осуществляем распаковку через цикл и заново приклеиваем к датафрейму
for i in range(0, 100):
    artists_deezer_top.append(deezer_chart_json['tracks']['data'][i]['artist']['name'])
new_df['artist'] = artists_deezer_top
new_df['rank'] = new_df.reset_index().index +1 
new_df = new_df[['rank', 'title', 'artist']]
    
n_l = list(new_df["title"])   
        
        #новый ли тот чат, который мы запарсили?
if o_l != n_l:           
            
    # задаем дату
    date = datetime.now() 
    new_df["date"] = datetime.strftime(date,"%d/%m/%Y")  
            
            #вписываем данные в csv
    frames = [all_deezer, new_df]
    all_deezer = pd.concat(frames, sort=False)
    all_deezer.to_csv("all_deezer.csv", encoding = "utf-8")
    
    print("New Deezer chart is found. No more scraping for today!")
            
else:
    print("Keep scraping. No chart found yet.")
            

