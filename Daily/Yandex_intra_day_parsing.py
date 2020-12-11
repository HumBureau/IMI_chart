#!/usr/bin/env python
# coding: utf-8

# ### Yandex Music - внутридневной парсинг чарта

# In[ ]:


# данный скрипт:

## парсит чарт яндекса весь день с периодичностью в полчаса

# Время запуска скрипта: 00:30.

# на выходе:
# 1) после каждого парсинга обновляет:
#  1.1) ВСЕ внутридневные данные -- all_yandex_intra_daily.csv
#  1.2) внутридневные данные данного дня -- yandex_intra_daily_today.csv
# 2) если это последний запуск (определяет по времени - если осталось меньше чем 30 минут до полуночи)...
### ... усредняет данные (из yandex_intra_daily_today.csv !) и создает чарт яндекса за прошедший день, затем обновляет all_yandex.csv


# In[ ]:


import pandas as pd
import re
import requests
from bs4 import BeautifulSoup
from time import sleep
from random import randint
import datetime
from datetime import datetime
from dateutil.relativedelta import relativedelta
from time import sleep
import os
import json


# In[ ]:


def avg():
    
# усредняем данные за день и получаем чарт дня 

    yandex_daily_avg = pd.DataFrame(columns = ['raw_rank', "title", "artist", "date", "genre", "label", "listeners"])

    df = pd.read_csv("yandex_intra_daily_today.csv") 
    df["full_id"] = df["title"]+"#bh#_#bh#"+df["artist"] # кодируем песню, чтобы избежать путаницы с одинаковыми названиями

    for i in set(list(df["full_id"])):
        s_df = df[df["full_id"]==i] # таблица с одной песней
        l_w_ranks = list(s_df["rank"])    
        delta = n_of_scrapes - len(s_df) 
        for j in range(0,delta):
            l_w_ranks.append(101) # присуждаем песне 101-ю строчку в те моменты, когда она не попала в чарт 

        avg_rank = sum(l_w_ranks)/n_of_scrapes # считаем среднюю строку песни 
        add_df = pd.DataFrame() 
        add_df["raw_rank"] = [avg_rank]
        add_df["title"] = i.split("#bh#_#bh#")[0]
        add_df["artist"] = i.split("#bh#_#bh#")[1]
        add_df["date"] = list(s_df["time"])[0].split(" ")[0] # записываем день
        yandex_daily_avg = yandex_daily_avg.append(add_df, ignore_index=True)

    yandex_daily_avg.sort_values(by=['raw_rank'], inplace=True)
    yandex_daily_avg['rank'] = yandex_daily_avg.reset_index().index +1
    yandex_daily_avg.reset_index(inplace=True)
    yandex_daily_avg.drop(yandex_daily_avg.columns[[0]], axis=1) # удаляем старый индекс
    yandex_daily_avg.drop(yandex_daily_avg.columns[[0]], axis=1) # удаляем raw_rank
    yandex_daily_avg=yandex_daily_avg[["rank", "title", "artist", "date", "genre", "label", "listeners"]]
    
    # сохраняем чарт дня, обновляя базу all_yandex 
    if os.path.exists("all_yandex.csv") == False:
        yandex_daily_avg.to_csv("all_yandex.csv", encoding = "utf-8")
    else:        
        old_csv = pd.read_csv("all_yandex.csv", encoding = "utf-8")
        old_csv = old_csv.drop(old_csv.columns[[0]], axis=1) # удаляем получающуюся после импорта лишнюю колонку 
        new_csv = pd.concat([old_csv,yandex_daily_avg], ignore_index=True, sort = False)
        new_csv.reset_index(inplace=True)
        new_csv.drop(new_csv.columns[[0]], axis=1, inplace=True)
        new_csv.to_csv("all_yandex.csv", encoding = "utf-8")


# In[ ]:


# создаем словарь жанров
try:
    from yandex_music.client import Client
    client = Client()
    client = Client.from_credentials('tegusigalpa444@yandex.ru', 'aintthateasy')

    gs = client.genres()

    keys=[]
    values = []

    # создаем полный словарь 
    for i in range(0, len(gs)):
        if len(gs[i].sub_genres) ==0:
            values.append(gs[i].titles["ru"]["title"])
            keys.append(gs[i].id)
        else:
            values.append(gs[i]["title"])   
            keys.append(gs[i].id)    
            for j in range (0,len(gs[i].sub_genres)):
                values.append(gs[i].sub_genres[j].titles["ru"]["title"])
                keys.append(gs[i].sub_genres[j].id)
    d_of_genres = dict(zip(keys, values))
    out_file = open("ya_genres_dict.json", "w", encoding='utf8') 
    json.dump(d_of_genres, out_file, ensure_ascii=False) 
    out_file.close() 
except:
    print("Error: failed to refresh genres with yandex_music.client. Using the old dictionary instead.")
    d_of_genres = json.load(open("ya_genres_dict.json", "r", encoding='utf8') )


# In[ ]:


### Get chart from API

request_ya = requests.get('https://api.music.yandex.net/landing3/chart/russia') # ссылка на постоянный плейлист
chart_json = request_ya.json() # через API получаем json 
df = pd.DataFrame(chart_json["result"]["chart"]["tracks"])

listeners = [int(i["listeners"]) for i in  df["chart"]]
artists = [", ".join([j["name"] for j in i.get("artists") or []]) for i in df["track"]]
labels = [", ".join(j.get("name") for j in i["albums"][0].get("labels") or []) for i in df["track"]] 
songs = [i["title"] for i in df["track"]]
genres = [(d_of_genres.get(i["albums"][0].get("genre")) or "") for i in df["track"]]
ranks = [int(i["position"]) for i in df["chart"] ]

# добавляем вторичные названия (remix, OST, etc)
add_titles = []
for i in df["track"]:
    try:
        add =  " ({})".format(i["version"])
    except:
        add = ""
    add_titles.append(add)
songs = list(map(lambda a,b: a+b,songs, add_titles))   

# Соединяем все данные в актуальный чарт
cols = ["rank", "title", "artist", "genre", "label", "listeners"]
DF = pd.DataFrame(dict(zip(cols, [ranks, songs, artists, genres, labels, listeners])))


# In[ ]:


### Экспорт 

#yandex_music_top_100_daily = pd.DataFrame(columns=["rank", "title", "artist"])

yandex_music_top_100_daily_now= DF
yandex_music_top_100_daily_now["time"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

# пополняем базу данных ВСЕХ внутридневных скрейпингов (просто чтобы было)
if os.path.exists("all_yandex_intra_daily.csv") == True:
    old_csv = pd.read_csv("all_yandex_intra_daily.csv")
    old_csv = old_csv.drop(old_csv.columns[[0]], axis=1) # удаляем получающуюся после импорта лишнюю колонку 
    new_csv = pd.concat([old_csv,yandex_music_top_100_daily_now], ignore_index=True, sort = False)
    new_csv.reset_index(inplace=True)
    new_csv.drop(new_csv.columns[[0]], axis=1, inplace=True)
    new_csv.to_csv("all_yandex_intra_daily.csv", encoding = "utf-8")
else:
    yandex_music_top_100_daily_now.to_csv("all_yandex_intra_daily.csv", header = None,  encoding = "utf-8")
    

### should we update or should we create a new csv file?

if os.path.exists("y_nofscrapes.txt") == True:
    fd = os.open( "y_nofscrapes.txt", os.O_RDWR)
    imp = os.read(fd,100)
    old_n_of_scrapes = int(str(imp)[2:-1])
    os.close( fd )
else:
    old_n_of_scrapes = 0
    file = open('y_nofscrapes.txt', 'w')
    file.write("0")
    file.close()    
    #fd = os.open( "y_nofscrapes.txt", os.O_CREAT)
    #os.write(fd, str.encode("0"))
    #os.close(fd)
    
# читаем сколько было скрейпингов уже   

now = datetime.now()

if old_n_of_scrapes == 0:
    # сохраняем новый файл внутридневной базы данных сегодняшнего дня
    yandex_music_top_100_daily_now.to_csv("yandex_intra_daily_today.csv", encoding = "utf-8")
    print(now, "created new file for today's intradaily scrapes. another scraping round is done. more to come today.")
    n_of_scrapes = 1
    fd = os.open( "y_nofscrapes.txt", os.O_RDWR|os.O_CREAT)
    os.write(fd, str.encode(str(n_of_scrapes)))  
    os.close(fd)
else:
    # обновляем имеющийся
    old_csv = pd.read_csv("yandex_intra_daily_today.csv")
    old_csv = old_csv.drop(old_csv.columns[[0]], axis=1) # удаляем получающуюся после импорта лишнюю колонку 
    new_csv = pd.concat([old_csv,yandex_music_top_100_daily_now], ignore_index=True, sort = False)
    new_csv.reset_index(inplace=True)
    new_csv.drop(new_csv.columns[[0]], axis=1, inplace=True)
    new_csv.to_csv("yandex_intra_daily_today.csv", encoding = "utf-8")
    
    #yandex_music_top_100_daily_now.to_csv("yandex_intra_daily_today.csv", mode="a", header = None, encoding = "utf-8")
    print(now, "updated today's intradaily scrapes.")
    # будет ли еще хотя бы один запуск скрипта сегодня?
    today = datetime.strftime(datetime.now(),"%d/%m/%Y")
    end_time = datetime.strptime(today+ " 23:30", "%d/%m/%Y %H:%M") 
    #fd = os.open( "y_nofscrapes.txt", os.O_RDWR)
    file = open('y_nofscrapes.txt', 'w')
    n_of_scrapes = old_n_of_scrapes + 1
    if datetime.now()>= end_time:
        print(now, ": no more scraping for today. I am averaging the intradaily data.")
        # обнуляем счетчик
        file.write("0")
        file.close()
        #os.write(fd, str.encode("0"))
        #os.close(fd)
        # запускаем функцию, которая усредняет все данные за день и сохраняет чарт дня
        avg()
        print(now, ": exported the new daily chart.")
    else:       
        print(now, ": another scraping round is done. more to come today.")
        file.write(str(n_of_scrapes))
        file.close()


# In[ ]:




