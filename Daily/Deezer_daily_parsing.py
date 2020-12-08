#!/usr/bin/env python
# coding: utf-8

# In[31]:


import pandas as pd
import re
import requests
from bs4 import BeautifulSoup
from time import sleep
from random import randint
from dateutil.relativedelta import relativedelta
from datetime import datetime
from os import path


# In[54]:


def get_new_chart(js):
    
    # грузим данные за предыдущие дни
    all_deezer = pd.read_csv("all_deezer.csv")
    all_deezer = all_deezer.drop(all_deezer.columns[[0]], axis=1) # удаляем получающуюся после импорта лишнюю колонку 

    # на всякий случай чистим от дублей
    #all_deezer = all_deezer.drop_duplicates()
    #all_deezer.reset_index(inplace=True) 
    #all_deezer.drop(all_deezer.columns[[0]], axis=1, inplace=True)
    

    new_df = pd.DataFrame(js['tracks']['data']) # выбираем только список треков

    # Находим имена ВСЕХ артистов для каждого трека через API трека

    A_l = []
    L_l = []
    G_l = []
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
        
        # get label and genres from album API
        api_album = "https://api.deezer.com/album/"+str(json["album"]["id"])
        request_deezer = requests.get(api_album) 
        json = request_deezer.json()
        try:
            label = json["label"]
        except:
            print("no label found")
            label =""
        L_l.append(label)
        
        try:
            genre = ", ".join([i["name"] for i in json["genres"]["data"]])
        except:
            print("no genres found")
            genre =""
        G_l.append(genre)
    
    ## формируем все колонки
    cols = ['title', 'artist', "genre", "label"]
    new_df = pd.DataFrame(dict(zip(cols, [list(pd.DataFrame(js["tracks"]["data"])["title"]),A_l,G_l,L_l])))
    new_df['rank'] = new_df.reset_index().index +1 
    new_df = new_df[['rank', 'title', 'artist', "genre", "label"]]       
    # задаем дату
    date = datetime.now() 
    new_df["date"] = datetime.strftime(date,"%d/%m/%Y")  
            
    # вписываем данные в старый csv
    frames = [all_deezer, new_df]
    all_deezer = pd.concat(frames, sort=False)
    
    # чистим
    all_deezer.reset_index(inplace=True) 
    all_deezer.drop(all_deezer.columns[[0]], axis=1, inplace=True)
    all_deezer.to_csv("all_deezer.csv", encoding = "utf-8")
    
    print(date, ": New Deezer chart is saved to data. Length of data: ", len(new_df))


# In[156]:


# базовая ссылка на последний актуальный ежедневный чарт по России
request_deezer = requests.get('https://api.deezer.com/playlist/1116189381') # ссылка на постоянный плейлист
deezer_chart_json = request_deezer.json() # через API получаем json 
check_df = pd.DataFrame(deezer_chart_json['tracks']['data'])[["id"]]

now = datetime.now()

# проверяем, есть ли в API новые данные

if path.exists("deezer_check_df.csv"):
    old_check_df = pd.read_csv("deezer_check_df.csv")
    old_check_df = old_check_df.drop(old_check_df.columns[[0]], axis=1) 
    
    if check_df.equals(old_check_df):
        print(now, ": Deezer chart API has not been updated yet. Will try again in 1 hour.")
    else:
        print(now, ": Found new chart in Deezer API.")
        check_df.to_csv("deezer_check_df.csv")
        
        get_new_chart(deezer_chart_json)
        
        
else:
    check_df.to_csv("deezer_check_df.csv")
    print(now, ": No deezer_check_df.csv found. Created new one.")
    
    get_new_chart(deezer_chart_json)

