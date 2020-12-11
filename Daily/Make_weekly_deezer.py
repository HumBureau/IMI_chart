#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# данный скрипт:
## - высчитывает еженедельные чарты стримингов, усредняя ежедневные чарты за 7 дней 
## - стриминги: Deezer
## - должен запускаться один раз в неделю утром пятницы после Spotify_parsing

## соединяет получающиеся чарты в единый html файл для публикации на сайте (включая "настоящие" еженедельные чарты)

# на выходе:
## - обновляет csv файл со всеми недельными чартами Deezer
## - сохраняет новый html и json с актуальным недельным чартом


# In[ ]:


import pandas as pd
import re
import requests
from bs4 import BeautifulSoup
from time import sleep
from random import randint
import datetime
from datetime import datetime, date, time, timezone
from dateutil.relativedelta import relativedelta
import heapq
from Make_weekly_charts_functions import average


# In[ ]:


# загружаем полные базы данных по всем ежедневным чартам

all_deezer = pd.read_csv("all_deezer.csv")


# удаляем получающуюся после импорта лишнюю колонку 
all_charts= [all_deezer]
for i in all_charts:
    i.drop(i.columns[[0]], axis=1, inplace=True)


# In[ ]:


# просто техническая функция для отображения изначальных имен чартов
def name_of_global_obj(xx):
    return [objname for objname, oid in globals().items()
            if id(oid)==id(xx)][0]


# In[ ]:


# считаем недельные чарты для Deezer
# выполняем функцию average и обновляем имеющиеся еженедельные чарты из csv в корне

all_simple_charts = [all_deezer]

for c in all_simple_charts:
    
    output_chart = average(c)
    name_of_chart = str(name_of_global_obj(c)) 
   

    # обновляем csv c предыдущими еженедельными чартами
    name_of_weekly_chart = "all_deezer_weekly.csv"
    old_csv = pd.read_csv(name_of_weekly_chart)
    
    old_csv = old_csv.drop(old_csv.columns[[0]], axis=1) # удаляем получающуюся после импорта лишнюю колонку 
    frames = [old_csv, output_chart]
    new_csv = pd.concat(frames, sort=False)


# ### Добавление колонок, отвечающих за динамику показателей

# In[ ]:


all_deezer_weekly = new_csv


# In[ ]:


# функция для подсчета количества недель, которые песня держится в чарте

def weeks_in_chart(weekly_charts):
    
    df = weekly_charts
    df["title"] = df["title"].astype(str)
    df["artist"] = df["artist"].astype(str)
    df["full_id"] = df["title"]+"#bh#_#bh#"+df["artist"] # кодируем песню, чтобы избежать путаницы с одинаковыми названиями

    return_df = pd.DataFrame(columns = ['title', 'artist', "weeks_in_chart"])

    for i in set(list(df["full_id"])):
        s_df = df[df["full_id"]==i] # таблица с одной песней
        n_of_w = len(s_df)
        add_df = pd.DataFrame()
        add_df["weeks_in_chart"] = [n_of_w]
        add_df["title"] = i.split("#bh#_#bh#")[0]
        add_df["artist"] = i.split("#bh#_#bh#")[1]
        return_df=return_df.append(add_df, ignore_index=True)
        
    return return_df


# In[ ]:


# пишем функцию, которая считает best position in chart, weeks in chart, change in rank [vs previous week]

def metrics_delta(chart):
    
    #### best position
    chart["rank"] = chart["rank"].astype(int)
    best_pos = pd.DataFrame(chart.groupby(['title', 'artist']).agg({'rank' : 'min'}))
    best_pos.reset_index(inplace=True)
    best_pos.columns = ['title', 'artist', 'best_pos']
    best_pos["best_pos"] = best_pos["best_pos"].astype('Int64') 
    
    
    
    #### change in rank vs previous week
    
    chart_last_week = chart.loc[chart['week'] == chart['week'].values[-1]] # назначаем  последнюю неделю
    chart_dropped  = chart.drop(chart[chart['week'] == chart['week'].values[-1]].index)
    
    # назначаем предыдущую неделю
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
    
    
    # присоединяем данные о best_pos 
    chart_upd.drop("best_pos", 1, inplace=True)
    new_chart = pd.merge(chart_upd, best_pos, how='left', on=['title', 'artist'])
    chart_last_week = new_chart.loc[new_chart['week'] == new_chart['week'].values[-1]]
    
    # чистим
    chart_last_week = chart_last_week.rename(columns={'rank_x': 'rank'})
    chart_last_week.drop('rank_y', 1, inplace=True)
    
    
    return chart_last_week


# In[ ]:


#count all new metrics
deezer_curr_week = metrics_delta(all_deezer_weekly)


# ### ЭКСПОРТ

# In[ ]:


deezer_curr_week.name ="deezer"


# In[ ]:


### EXPORT TO JSON, HTML, CSV 
all_curr_week_charts = [deezer_curr_week]

for ch in all_curr_week_charts:
    
    name_of_chart = ch.name
    
    ## EXPORT TO JSON ##
    
    with open("current_" +name_of_chart+"_json.json", 'w', encoding='utf-8') as file:
        ch.to_json(file, force_ascii=False)
    
    ## EXPORT TO CSV (i.e. MAIN DATABASE) ##

    name_of_weekly_chart = "all_"+ name_of_chart +"_weekly.csv" 
    old_csv = pd.read_csv(name_of_weekly_chart)    # загружаем старые данные
    old_csv = old_csv.drop(old_csv.columns[[0]], axis=1) # удаляем получающуюся после импорта лишнюю колонку 
    
    frames = [old_csv, ch]
    new_csv = pd.concat(frames, sort=False)
    new_csv.reset_index(inplace= True)
    new_csv = new_csv.drop(new_csv.columns[[0]], axis=1) 
    new_csv.to_csv(name_of_weekly_chart, encoding = "utf-8")
    
    print("Exported the new weekly Deezer chart. Length: ", len(ch))
    
    ## EXPORT TO HTML ##
    # пишем красивые названия колонок
    ch_html = ch.drop("raw_rank", 1)
    ch_html=ch_html[["week", "rank", "delta_rank", "best_pos", "title", "artist", "genre", "weeks_in_chart", "label"]]
    ch_html.columns = ["Неделя", "Позиция", "Изменение позиции vs прошлая неделя", "Лучшая позиция с начала наблюдений (18/09/20 - 24/09/20)", "Название", "Артист", "Жанр", "Недель в чарте с начала наблюдений (18/09/20 - 24/09/20)", "Лейбл"]                     
    
    html_name = "current_"+name_of_chart+"_html.html"
    ch_html.to_html(html_name, encoding = "utf-8")


# In[ ]:




