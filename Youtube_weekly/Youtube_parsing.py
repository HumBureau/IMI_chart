#!/usr/bin/env python
# coding: utf-8

# In[1]:


#данный скрипт: 

## - осуществляет парсинг еженедельного чарта Top Tracks Youtube 
### - через selenium

## время запуска: утро воскресенья
## период чарта: пятница-четверг

## - на выходе:
### - обновляет уже хранящиеся данные прошлых недель в csv 
### - сохраняет html файл актуального чарта для демонстрации на сайте


# In[2]:


import pandas as pd
import re
import requests
from bs4 import BeautifulSoup
from time import sleep
from random import randint
import datetime
from datetime import datetime, date, time, timezone
from dateutil.relativedelta import relativedelta
import csv 
import json 
currentDT = datetime.now() 


# In[3]:


#установка и импорт selenium
get_ipython().system('pip install selenium')
from selenium import webdriver as wb
get_ipython().system('pip install chromedriver')


# ### ПАРСИНГ: Youtube Top 100 Tracks Russia

# In[4]:


#selenium-код
url='https://charts.youtube.com/charts/TopSongs/ru?hl=ru'
br = wb.Chrome() 
br.get(url)
sleep(randint(3,4))
generated_html = br.page_source
br.quit()


# In[4]:


#работаем с html
soup = BeautifulSoup(generated_html, 'html.parser')

all_together = soup.findAll('span', attrs={'class':'ytmc-ellipsis-text style-scope'})
songs = all_together[2:][0::2]
artists = all_together[2:][1::2]

songs_clean = [i.get_text() for i in songs]
artists_clean = [i.get_text() for i in artists]


views = soup.findAll('span', attrs={'class':'style-scope ytmc-chart-table'})[4::5]
views_clean = [i.get_text() for i in views]

youtube_tracks_top_100 = pd.DataFrame()
youtube_tracks_top_100['title'] = songs_clean
youtube_tracks_top_100['artist'] = artists_clean
youtube_tracks_top_100['streams'] = views_clean
youtube_tracks_top_100['rank'] = youtube_tracks_top_100.reset_index().index +1
youtube_tracks_top_100= youtube_tracks_top_100[['rank', 'title', 'artist', 'streams']]
#date = дата скрейпинга!
youtube_tracks_top_100["date"] = currentDT.strftime("%d/%m/%Y")  

#записываем неделю 
date_start = currentDT - relativedelta(days=+7)
date_end = currentDT - relativedelta(days=+1)
week = datetime.strftime(date_start,"%d/%m/%y") + " - " + datetime.strftime(date_end,"%d/%m/%y")
youtube_tracks_top_100["week"] = week


# #### ФОРМИРУЕМ ПОЛНЫЙ ЧАРТ

# In[35]:


#функция для подсчета количества недель, которые песня держится в чарте

def weeks_in_chart(weekly_charts):
    
    df = weekly_charts
    df["full_id"] = df["title"]+"#bh#_#bh#"+df["artist"] #кодируем песню, чтобы избежать путаницы с одинаковыми названиями

    return_df = pd.DataFrame(columns = ['title', 'artist', "weeks_in_chart"])

    for i in set(list(df["full_id"])):
        s_df = df[df["full_id"]==i] #таблица с одной песней
        n_of_w = len(s_df)
        add_df = pd.DataFrame()
        add_df["weeks_in_chart"] = [n_of_w]
        add_df["title"] = i.split("#bh#_#bh#")[0]
        add_df["artist"] = i.split("#bh#_#bh#")[1]
        return_df=return_df.append(add_df, ignore_index=True)
        
    return return_df


# In[46]:


#пишем функцию, которая считает best position in chart, weeks in chart, change in rank [vs previous week]

def metrics_delta(chart):
    
    #### best position
    chart["rank"] = chart["rank"].astype(int)
    best_pos = pd.DataFrame(chart.groupby(['title', 'artist']).agg({'rank' : 'min'}))
    best_pos.reset_index(inplace=True)
    best_pos.columns = ['title', 'artist', 'best_pos']
    best_pos["best_pos"] = best_pos["best_pos"].astype('Int64') 
    
    
    
    #### change in rank vs previous week
    
    chart_last_week = chart.loc[chart['week'] == chart['week'].values[-1]] #назначаем  последнюю неделю
    chart_dropped  = chart.drop(chart[chart['week'] == chart['week'].values[-1]].index)
    
    #назначаем предыдущую неделю
    if len(chart_dropped) == 0:
        chart_previous_week = chart.loc[chart['week'] == chart['week'].values[1]]
    else: chart_previous_week = chart_dropped.loc[chart_dropped['week'] == chart_dropped['week'].values[-1]]
    
    
    chart_previous_week = chart_previous_week[['title', 'artist', 'rank']]
    # ! chart_upd - данные по последней неделе
    chart_upd = pd.merge(chart_last_week, chart_previous_week, how='left', on=['title', 'artist']) 
    chart_upd['delta_rank'] = (chart_upd['rank_y'] - chart_upd['rank_x']).astype('Int64') 

    
    
    
    #number of weeks in chart (use weeks_in_chart() function)
    chart_upd.drop("weeks_in_chart", 1, inplace = True) #avoid duplicates in columns
    chart_upd = pd.merge(chart_upd, weeks_in_chart(chart), how='left', on=['title', 'artist'])
    
    
    #присоединяем данные о best_pos 
    chart_upd.drop("best_pos", 1, inplace=True)
    new_chart = pd.merge(chart_upd, best_pos, how='left', on=['title', 'artist'])
    chart_last_week = new_chart.loc[new_chart['week'] == new_chart['week'].values[-1]]
    
    #чистим
    chart_last_week = chart_last_week.rename(columns={'rank_x': 'rank'})
    chart_last_week.drop('rank_y', 1, inplace=True)
    
    
    return chart_last_week


# In[34]:


def streams_delta_yout(chart):
    
    chart['streams'] = chart['streams'].replace({'K': '*1e3', 'M': '*1e6'}, regex=True).map(pd.eval).astype(int)
    chart_last_week = chart[chart['week'] == chart['week'].values[-1]]
    chart_dropped  = chart.drop(chart[chart['week'] == chart['week'].values[-1]].index)
    
    if len(chart_dropped) == 0:
        chart_previous_week = chart.loc[chart['week'] == chart['week'].values[1]]
    else: chart_previous_week = chart_dropped.loc[chart_dropped['week'] == chart_dropped['week'].values[-1]]
        
    chart_previous_week = chart_previous_week[['title', 'artist', 'streams']]
    chart_upd = pd.merge(chart_last_week, chart_previous_week, how='left', on=['title', 'artist'])
    chart_upd["streams_y"].fillna(0, inplace=True)
    chart_upd['delta_streams'] = (chart_upd['streams_x'] - chart_upd['streams_y']).astype('Int64')
    chart_upd = chart_upd[['title', 'artist', 'delta_streams']]
    
    return chart_upd


# In[72]:


#соединяем старые данные с новыми
all_youtube = pd.read_csv("all_youtube.csv")
all_youtube = all_youtube.drop(all_youtube.columns[[0]], axis=1) #удаляем получающуюся после импорта лишнюю колонку 
frames = [all_youtube, youtube_tracks_top_100] 
all_youtube = pd.concat(frames, sort=False)     


# In[76]:


#count change in streams
y1 = streams_delta_yout(all_youtube)

#считаем остальные доп показатели
youtube_curr_week = metrics_delta(all_youtube)

youtube_curr_week.drop("delta_streams", 1, inplace=True) #drop so that columns don't duplicate
#merge delta_streams and other metrics
youtube_curr_week = pd.merge(youtube_curr_week, y1, how='left', on=['title', 'artist'])


# ### ЭКСПОРТ

# In[86]:


### EXPORT TO JSON
with open('current_youtube_json.json', 'w', encoding='utf-8') as file:
    youtube_curr_week.to_json(file, force_ascii=False)


# In[87]:


### EXPORT TO HTML
#сохраняем html для использования на сайте (т.е. через Make_weekly_charts.py впоследствии)
youtube_curr_week_html=youtube_curr_week[["rank", "delta_rank", "best_pos", "title", "artist", "streams", "delta_streams", "weeks_in_chart", "week"]]
youtube_curr_week_html.columns = ["Позиция", "Изменение позиции", "Лучшая позиция", "Название", "Артист", "Прослушивания", "Динамика прослушиваний", "Недель в чарте", "Неделя"]
youtube_curr_week_html.to_html("current_youtube_html.html", encoding = "utf-8")


# In[83]:


### EXPORT TO CSV - (i.e. TO THE MAIN DATABASE)
#берем имеющийся в корневой директории csv файл и обновляем его

all_youtube = pd.read_csv("all_youtube.csv")
all_youtube = all_youtube.drop(all_youtube.columns[[0]], axis=1) #удаляем получающуюся после импорта лишнюю колонку 
frames = [all_youtube, youtube_curr_week]
all_youtube = pd.concat(frames, sort=False)
all_youtube.to_csv("all_youtube.csv", encoding = "utf-8")

