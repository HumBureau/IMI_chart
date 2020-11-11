#!/usr/bin/env python
# coding: utf-8

# In[33]:


import pandas as pd
import re
import requests
from bs4 import BeautifulSoup
from time import sleep
from random import randint
from dateutil.relativedelta import relativedelta
from datetime import datetime
import json


# In[69]:



    
    
# базовая ссылка на последний актуальный ежедневный чарт по России
request_deezer = requests.get('https://api.deezer.com/playlist/1116189381') # ссылка на постоянный плейлист
deezer_chart_json = request_deezer.json() # через API получаем json 

now = datetime.now()

# проверяем, есть ли в API новые данные

old_json = json.load(open('deezer_old_json.json', 'r'))

if old_json["tracks"]["data"] == deezer_chart_json ["tracks"]["data"]:
    print(now, ": Deezer chart API has not been updated yet. Will try again in 1 hour.")
else:
    print(now, ": Found new chart in Deezer API.")
    
    # сохраняем новый json
    with open('deezer_old_json.json', 'w') as json_file:
        json.dump(old_json, json_file)
    
    # грузим данные за предыдущие дни
    all_deezer = pd.read_csv("all_deezer.csv")
    all_deezer = all_deezer.drop(all_deezer.columns[[0]], axis=1) # удаляем получающуюся после импорта лишнюю колонку 

    # на всякий случай чистим от дублей
    all_deezer = all_deezer.drop_duplicates()
    all_deezer.reset_index(inplace=True) 
    all_deezer.drop(all_deezer.columns[[0]], axis=1, inplace=True)

    new_df = pd.DataFrame(deezer_chart_json['tracks']['data']) # выбираем только список треков

    # Находим имена ВСЕХ артистов для каждого трека через API трека

    A_l = []
    for i in new_df["id"]:
        api_track = 'https://api.deezer.com/track/'+str(i)
        request_deezer = requests.get(api_track) 
        json = request_deezer.json()
        a_l = []
        for j in json["contributors"]:
            a_l.append(j["name"])
        g_a_l = [i for n, i  in enumerate(a_l) if i not in a_l[:n]] 
        artists = ", ".join(g_a_l) #  delete duplicate mentions
        A_l.append(artists)
    new_df["artist"] = A_l

    new_df['rank'] = new_df.reset_index().index +1 
    new_df = new_df[['rank', 'title', 'artist']]

    n_l = list(new_df["title"])   
        
    # задаем дату
    date = datetime.now() 
    new_df["date"] = datetime.strftime(date,"%d/%m/%Y")  
            
    # вписываем данные в csv
    frames = [all_deezer, new_df]
    all_deezer = pd.concat(frames, sort=False)
    # чистим
    all_deezer.drop_duplicates(inplace=True)
    all_deezer.reset_index(inplace=True) 
    all_deezer.drop(all_deezer.columns[[0]], axis=1, inplace=True)
    all_deezer.to_csv("all_deezer.csv", encoding = "utf-8")
    
    print(date, ": New Deezer chart is saved to data. Length of data: ", len(new_df))
        

