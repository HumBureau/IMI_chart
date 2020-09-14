#!/usr/bin/env python
# coding: utf-8

# ### Yandex Music - внутридневной парсинг чарта

# In[ ]:


#данный скрипт:

## парсит чарт яндекса весь день с периодичностью в полчаса

# Время запуска скрипта: 00:30.

#на выходе:
#1) после каждого парсинга обновляет внутридневные данные -- all_yandex_intra_daily.csv
#2) в полночь создает чарт яндекса за прошедший день и обновляет all_yandex.csv


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


# In[ ]:


#базовая ссылка на последний актуальный ежедневный чарт по России
base_url = 'https://music.yandex.ru/chart'

#создаем внутридневную базу данных
yandex_music_top_100_daily = pd.DataFrame(columns=["rank", "title", "artist"])

#парсинг:
today = datetime.strftime(datetime.now(),"%d/%m/%Y")
end_time = datetime.strptime(today+ " 23:59", "%d/%m/%Y %H:%M")

n_of_scrapes =0 #счетчик 

while datetime.now() <= end_time:
    
    r = requests.get(base_url)
#на всякий случай поставим на паузу
    sleep(3)
#находим в верстке сайта интересующие нас части
    soup = BeautifulSoup(r.text, 'html.parser')
    songs = soup.findAll('div', attrs={'class':'d-track__name'})
    artists = soup.findAll('span', attrs={'class':'d-track__artists'})
    full_id = [j+i for i in songs for j in artists]
#делаем список вторичных названий песен (слов вроде remix, cover, и тд), чтобы они не сливались с названиями 
    sec_titles = soup.findAll('span', attrs={'class':'d-track__version deco-typo-secondary'})
    sec_titles_clean = [i.get_text() for i in sec_titles]
    sec_titles_clean = sorted(sec_titles_clean, reverse=True, key=len)

#чистим названия песен и артистов
    songs_clean = [i.get_text() for i in songs]
    new_l=[]
    for i in songs_clean:
        for j in sec_titles_clean:
            if j in i:
                v = i.replace(j, " ("+j+")")
                break
            else:
                v = i
        new_l.append(v)
    songs_clean = new_l
    artists_clean = [i.get_text() for i in artists]

    yandex_music_top_100_daily_now = pd.DataFrame()
    yandex_music_top_100_daily_now['title'] = songs_clean
    yandex_music_top_100_daily_now['artist'] = artists_clean
    yandex_music_top_100_daily_now['rank'] = yandex_music_top_100_daily_now.reset_index().index +1
    yandex_music_top_100_daily_now= yandex_music_top_100_daily_now[['rank', 'title', 'artist']]
    yandex_music_top_100_daily_now["time"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    yandex_music_top_100_daily = yandex_music_top_100_daily.append(yandex_music_top_100_daily_now, ignore_index = True)
    n_of_scrapes +=1 
    sleep(1800) #засыпаем на полчаса - примерная периодичность обновления чарта    


# In[ ]:


#сохраняем внутридневные данные
yandex_music_top_100_daily.to_csv("all_yandex_intra_daily.csv", mode='a', encoding = "utf-8")


# In[ ]:


#усредняем данные за день и получаем чарт дня 

yandex_daily_avg = pd.DataFrame(columns = ['raw_rank', 'title', 'artist', "date"])

df = pd.read_csv("all_yandex_intra_daily.csv") 
df["full_id"] = df["title"]+"#bh#_#bh#"+df["artist"] #кодируем песню, чтобы избежать путаницы с одинаковыми названиями

for i in set(list(df["full_id"])):
    s_df = df[df["full_id"]==i] #таблица с одной песней
    l_w_ranks = list(s_df["rank"])    
    delta = n_of_scrapes - len(s_df) 
    for i in range(0,delta):
        l_w_ranks.append(101) #присуждаем песне 101-ю строчку в те моменты, когда она не попала в чарт 
        
    avg_rank = sum(l_w_ranks)/n_of_scrapes #считаем среднюю строку песни 
    add_df = pd.DataFrame() 
    add_df["raw_rank"] = [avg_rank]
    add_df["title"] = i.split("#bh#_#bh#")[0]
    add_df["artist"] = i.split("#bh#_#bh#")[1]
    add_df["date"] = list(s_df["time"])[0].split(" ")[0] #записываем день
    yandex_daily_avg = yandex_daily_avg.append(add_df, ignore_index=True)

yandex_daily_avg.sort_values(by=['raw_rank'], inplace=True)
yandex_daily_avg['rank'] = yandex_daily_avg.reset_index().index +1
yandex_daily_avg.reset_index(inplace=True)
yandex_daily_avg.drop(yandex_daily_avg.columns[[0]], axis=1) #удаляем старый индекс
yandex_daily_avg.drop(yandex_daily_avg.columns[[0]], axis=1) #удаляем raw_rank
yandex_daily_avg=yandex_daily_avg[["rank", 'title', 'artist', "date"]]


# In[ ]:


#сохраняем чарт дня, обновляя базу all_yandex 
yandex_daily_avg.to_csv("all_yandex.csv", mode='a', encoding = "utf-8")

