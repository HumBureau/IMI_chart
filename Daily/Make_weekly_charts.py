#!/usr/bin/env python
# coding: utf-8

# In[1]:


# данный скрипт:
## - высчитывает еженедельные чарты стримингов, усредняя ежедневные чарты за 7 дней 
## - стриминги: Apple Music, VK, Deezer, Yandex
## - должен запускаться один раз в неделю утром пятницы после Youtube_parsing и Spotify_parsing

## соединяет получающиеся чарты в единый html файл для публикации на сайте (включая "настоящие" еженедельные чарты)

# на выходе:
## - обновляет csv файлы с соответствующими еженедельными чартами 4-x стримингов
## - сохраняет 4 html файла с новыми еженедельными чартами
## - сохраняет 4 json файла с новыми недельными чартами


# In[18]:


import pandas as pd
import re
import requests
from bs4 import BeautifulSoup
from time import sleep
from random import randint
import datetime
from datetime import datetime, date, time, timezone
from dateutil.relativedelta import relativedelta


# In[20]:


# задаем команду для получения даты
currentDT = datetime.now() 


# In[3]:


# загружаем полные базы данных по всем ежедневным чартам
all_yandex = pd.read_csv("all_yandex.csv")
all_deezer = pd.read_csv("all_deezer.csv")
all_apple = pd.read_csv("all_apple.csv")



# удаляем получающуюся после импорта лишнюю колонку 
all_charts= [all_apple, all_deezer, all_yandex]
for i in all_charts:
    i.drop(i.columns[[0]], axis=1, inplace=True)


# In[ ]:


# сделаем вспомогательные объекты для работы с датами
all_dates = []
for i in range(1,8):
    k = currentDT - relativedelta(days=+i)
    all_dates.append(datetime.strftime(k, "%d/%m/%Y"))

date_start = currentDT - relativedelta(days=+7)
date_end = currentDT - relativedelta(days=+1)


# In[4]:


# функция для получения недельного чарта через усреднение ежедневных
# только для apple, deezer, VK


def average(df):
  
    df['Datetime'] = [datetime.strptime(i, "%d/%m/%Y") for i in df["date"]]
    
    # take last week only

    last_week_df = df[date_start <= df["Datetime"]]
    df = last_week_df
    
    raw_rank = []
    songs =[]
    artists = []
    for i in list(set(df["title"])):
        newdf = df[df["title"]==i]
        for j in list(set(newdf["artist"])):
            one_track_df = newdf[newdf["artist"]==j]
            # how many dates are missing? 
            not_missing_dates = list(one_track_df["date"])
            n_of_m_days = 7 - len(not_missing_dates)            
            # добавляем rank = 101 для отсутствующих дней
            average_rank = (sum(one_track_df["rank"]) + (101*n_of_m_days)) / 7  
            songs.append(i)
            artists.append(j)
            raw_rank.append(average_rank)

    data = {"raw_rank": raw_rank, "title": songs, "artist": artists}        
    new_chart = pd.DataFrame(data)
    new_chart.sort_values(by=['raw_rank'], inplace=True)

    new_chart['rank'] = new_chart.reset_index().index +1
    new_chart.reset_index(inplace=True)
    week = datetime.strftime(date_start,"%d/%m/%y") + " - " + datetime.strftime(date_end,"%d/%m/%y")
    new_chart["week"] = week
    
    new_chart = new_chart[['rank', 'title', 'artist', "week", "raw_rank"]]
    
    # округляем raw_rank
    new_chart["raw_rank"] = round(new_chart["raw_rank"], 3)
    
    return new_chart


# In[ ]:


# функция для получения недельного чарта через усреднение ежедневных
# только для yandex


def average_ya(df):  
    df['Datetime'] = [datetime.strptime(i, "%d/%m/%Y") for i in df["date"]]
    
    # take last week only

    last_week_df = df[date_start <= df["Datetime"]]
    last_week_df = last_week_df[last_week_df["Datetime"] <  datetime.strptime(datetime.strftime(currentDT, "%d/%m/%Y"), "%d/%m/%Y")]
    df = last_week_df
    
    raw_rank = []
    songs =[]
    artists = []
    for i in list(set(df["title"])):
        newdf = df[df["title"]==i]
        for j in list(set(newdf["artist"])):
            one_track_df = newdf[newdf["artist"]==j]
            # what dates are missing? 
            not_missing_dates = list(one_track_df["date"])
            missing_days = list(set(all_dates) - set(not_missing_dates))
            # добавляем rank равный строчке после последней видимой 
            added_ranks = []
            for day in missing_days:
                one_day_df = df[df["date"] == day]
                added_ranks.append(len(one_day_df) + 1)  
            # считаем среднюю строку за неделю    
            average_rank = (sum(one_track_df["rank"]) + sum(added_ranks)) / 7  
            songs.append(i)
            artists.append(j)
            raw_rank.append(average_rank)

    data = {"raw_rank": raw_rank, "title": songs, "artist": artists}        
    new_chart = pd.DataFrame(data)
    new_chart.sort_values(by=['raw_rank'], inplace=True)

    new_chart['rank'] = new_chart.reset_index().index +1
    new_chart.reset_index(inplace=True)
    week = datetime.strftime(date_start,"%d/%m/%y") + " - " + datetime.strftime(date_end,"%d/%m/%y")
    new_chart["week"] = week
    
    new_chart = new_chart[['rank', 'title', 'artist', "week", "raw_rank"]]
    
    # округляем raw_rank
    new_chart["raw_rank"] = round(new_chart["raw_rank"], 3)
    
    return new_chart


# In[5]:


# просто техническая функция для отображения изначальных имен чартов
def name_of_global_obj(xx):
    return [objname for objname, oid in globals().items()
            if id(oid)==id(xx)][0]


# In[9]:


# считаем недельные чарты для VK, Apple, Deezer
# выполняем функцию average и обновляем имеющиеся еженедельные чарты из csv в корне

all_simple_charts = [all_apple, all_deezer]

for c in all_simple_charts:
    
    output_chart = average(c)
    name_of_chart = str(name_of_global_obj(c)) 
   

    # обновляем csv c предыдущими еженедельными чартами
    name_of_weekly_chart = name_of_chart +"_weekly.csv"
    old_csv = pd.read_csv(name_of_weekly_chart)
    
    old_csv = old_csv.drop(old_csv.columns[[0]], axis=1) # удаляем получающуюся после импорта лишнюю колонку 
    frames = [old_csv, output_chart]
    new_csv = pd.concat(frames, sort=False)
    new_csv.to_csv(name_of_weekly_chart, encoding = "utf-8") 
    
# для Yandex    
# выполняем функцию average_ya

output_chart = average_ya(all_yandex)
old_csv = pd.read_csv("all_yandex_weekly.csv")
old_csv = old_csv.drop(old_csv.columns[[0]], axis=1) # удаляем получающуюся после импорта лишнюю колонку 
frames = [old_csv, output_chart]
new_csv = pd.concat(frames, sort=False)
new_csv.to_csv("all_yandex_weekly.csv", encoding = "utf-8") 


# ### Добавление колонок, отвечающих за динамику показателей

# In[10]:


# загружаем все чарты, агрегированные за неделю
all_yandex_weekly = pd.read_csv("all_yandex_weekly.csv")
all_deezer_weekly = pd.read_csv("all_deezer_weekly.csv")
all_apple_weekly = pd.read_csv("all_apple_weekly.csv")

# чистим колонки для удобства
all_weekly_charts= [all_apple_weekly, all_deezer_weekly, all_yandex_weekly]
for i in all_weekly_charts:
    try:
        i.drop(i.columns[[0]], axis=1, inplace=True)
        #for h in ["weeks_in_chart", "best_pos", "full_id", "delta_rank"]:
            #i[h] = None
    except:
        6+8
    i.drop_duplicates(inplace=True)


# In[2]:


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


# In[12]:


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


# In[13]:


#count all new metrics

apple_curr_week = metrics_delta(all_apple_weekly)
deezer_curr_week = metrics_delta(all_deezer_weekly)
yandex_curr_week = metrics_delta(all_yandex_weekly)


# ### ЭКСПОРТ

# In[14]:


apple_curr_week.name ="apple"
deezer_curr_week.name ="deezer"
yandex_curr_week.name ="yandex"


# In[15]:


### EXPORT TO JSON, HTML, CSV 
all_curr_week_charts = [apple_curr_week, deezer_curr_week, yandex_curr_week]

for ch in all_curr_week_charts:
    
    name_of_chart = ch.name
    
    ## EXPORT TO JSON ##
    
    with open("current_" +name_of_chart+"_json.json", 'w', encoding='utf-8') as file:
        ch.to_json(file, force_ascii=False)
    
    ## EXPORT TO CSV (i.e. MAIN DATABASE) ##

    name_of_weekly_chart = "all_"+ name_of_chart +"_weekly.csv" 
    old_csv = pd.read_csv(name_of_weekly_chart)    # загружаем старые данные 
    old_csv = old_csv.drop(old_csv.columns[[0]], axis=1) # удаляем получающуюся после импорта лишнюю колонку 
    
    old_csv = old_csv[:-len(ch)] # ВАЖНО: удаляем чарт этой недели, в котором еще нет новых метрик
    
    frames = [old_csv, ch]
    new_csv = pd.concat(frames, sort=False)
    new_csv.to_csv(name_of_weekly_chart, encoding = "utf-8")
    
    ## EXPORT TO HTML ##
    # пишем красивые названия колонок
    ch_html = ch.drop("raw_rank", 1)
    ch_html=ch_html[["rank", "delta_rank", "best_pos", "title", "artist", "weeks_in_chart", "week"]]
    ch_html.columns = ["Позиция", "Изменение позиции", "Лучшая позиция", "Название", "Артист", "Недель в чарте", "Неделя"]           
    
    html_name = "current_"+name_of_chart+"_html.html"
    ch_html.to_html(html_name, encoding = "utf-8")

