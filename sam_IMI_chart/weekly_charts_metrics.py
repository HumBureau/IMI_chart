

# In[1]:


# этот скрипт НЕ следует использовать для яндекс музыки.


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
from os import path
import heapq


# In[8]:


# сделаем вспомогательные объекты для работы с датами
def week_dates(currentDT):
    global date_start, date_end, all_dates
    all_dates = []
    for i in range(1,8):
        k = currentDT - relativedelta(days=+i)
        all_dates.append(datetime.strftime(k, "%d/%m/%Y"))

    date_start = currentDT - relativedelta(days=+7)
    date_end = currentDT - relativedelta(days=+1)
    
    return all_dates


# In[9]:


# функция для получения недельного чарта через усреднение ежедневных


def average(df):
    
    df['Datetime'] = [datetime.strptime(i, "%d/%m/%Y") for i in df["date"]]
    
    # take last week only

    last_week_df = df[date_start <= df["Datetime"]]
    last_week_df = last_week_df[last_week_df["Datetime"] <= date_end ]
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
            missing_days = list(set(all_dates) - set(not_missing_dates))
            
            # определяем, нет ли песни в чарте за день потому, что вообще чарта для этого дня нет
            denominator = 7            
            added_ranks = []
            for day in missing_days:
                # выясняем длину чарта в тот день (и сохранен ли он вообще!)
                one_DAY_df = df[df["date"] == day]
                if len(one_DAY_df) >0:
                    # добавляем rank равный строчке после последней видимой 
                    added_ranks.append(len(one_DAY_df) + 1)  
                else:
                    # сокращаем делитель на 1 (т.к. такого дня нет в данных вообще)
                    print("No chart for this day. Will change the demominator in the average rank formula.")
                    print("Day: ", day)
                    denominator = denominator - 1
                    
                
            full_ranks = added_ranks
            full_ranks.extend(list(one_track_df["rank"]))
            
            # наконец считаем среднюю строку за неделю    
            if len(full_ranks) > denominator:
                # рангов больше чем делитель. так бывает, если в чарте есть и сингл, и альбом
                print("Found a song with more appearances than # of saved charts in this week (including added added 'n+1' ranks). Taking the highest # ranks only. ", i )
                average_rank = sum(heapq.nsmallest(7, full_ranks)) / denominator
            else:
                average_rank = (sum(full_ranks)) / denominator  
                 
            songs.append(i)
            artists.append(j)
            raw_rank.append(average_rank)

    data = {"raw_rank": raw_rank, "title": songs, "artist": artists, 'weeks_in_chart': None, 'best_pos':None, 'delta_rank':None}        
    new_chart = pd.DataFrame(data)
    
    ### Присуджаем "чистый" номер строчки 
    
    new_chart.sort_values(by=['raw_rank'], inplace=True)
    new_chart['rank'] = new_chart.reset_index().index +1
    
    # если raw_rank равен, уравняем rank тоже.
    prev_raw_r = 0
    prev_r = 0 
    for r in new_chart.iterrows():
        if r[1]["raw_rank"] == prev_raw_r:
            new_chart.at[r[0], "rank"]=prev_r
        else:
            # new "group". so update rank. 
            prev_r = r[1]["rank"]
        prev_raw_r = r[1]["raw_rank"]
    
    new_chart.reset_index(inplace=True)
    week = datetime.strftime(date_start,"%d/%m/%y") + " - " + datetime.strftime(date_end,"%d/%m/%y")
    new_chart["week"] = week
    
    new_chart = new_chart[['rank', 'title', 'artist', "week", "raw_rank", 'weeks_in_chart','best_pos', 'delta_rank']]
    
    # округляем raw_rank
    new_chart["raw_rank"] = round(new_chart["raw_rank"], 3)
    
    return new_chart


# In[10]:


# просто техническая функция для отображения изначальных имен чартов
def name_of_global_obj(xx):
    return [objname for objname, oid in globals().items()
            if id(oid)==id(xx)][0]


# In[11]:


# считаем недельные чарты для VK, Apple, Deezer
# выполняем функцию average и обновляем имеющиеся еженедельные чарты из csv в корне

def count_export():
    all_simple_charts = [g]

    for c in all_simple_charts:

        output_chart = average(c)
        #output_chart.drop(["Datetime"], axis = 1, inplace = True)


        # обновляем csv c предыдущими еженедельными чартами
        if path.exists(name_of_weekly_chart):
            old_csv = pd.read_csv(name_of_weekly_chart)
            old_csv = old_csv.drop(old_csv.columns[[0]], axis=1) # удаляем получающуюся после импорта лишнюю колонку 
            frames = [old_csv, output_chart]
            new_csv = pd.concat(frames, sort=False)
            new_csv.reset_index(inplace=True)
            new_csv.drop(new_csv.columns[[0]], axis=1, inplace=True)
        else:
            new_csv = output_chart
        new_csv.to_csv(name_of_weekly_chart, encoding = "utf-8")


# ### Добавление колонок, отвечающих за динамику показателей

# In[12]:


def start_add_columns():
    # загружаем все чарты, агрегированные за неделю
    global G
    G = pd.read_csv(name_of_weekly_chart)
    # чистим колонки для удобства
    G.drop(G.columns[[0]], axis=1, inplace=True)
    G.drop_duplicates(inplace=True, ignore_index=True)


# In[13]:


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


# In[14]:


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


# функция для подсчета изменения прослушиваний
def streams_delta(chart): 
    
    try:
        chart['streams'] = chart['streams'].astype(str).str.replace(",", "").astype(int)
    except:
        pass
        
    chart_last_week = chart[chart['week'] == chart['week'].values[-1]]
    chart_dropped  = chart.drop(chart[chart['week'] == chart['week'].values[-1]].index)
    if len(chart_dropped) == 0:
        chart_previous_week = chart.loc[chart['week'] == chart['week'].values[1]]
    else: 
        chart_previous_week = chart_dropped.loc[chart_dropped['week'] == chart_dropped['week'].values[-1]]
    chart_previous_week = chart_previous_week[['title', 'artist', 'streams']]
    chart_upd = pd.merge(chart_last_week, chart_previous_week, how='left', on=['title', 'artist'])
    #chart_upd["streams_y"].fillna(0, inplace=True)
    chart_upd['delta_streams'] = (chart_upd['streams_x'] - chart_upd['streams_y']).astype('Int64')
    chart_upd = chart_upd[['title', 'artist', 'delta_streams']]
    
    return chart_upd


# In[15]:


### EXPORT TO JSON, HTML, CSV 

def export():
    
    ## EXPORT TO JSON ##
    
    with open("current_" +name_of_chart+"_json.json", 'w', encoding='utf-8') as file:
        G.to_json(file, force_ascii=False)
    
    ## EXPORT TO CSV (i.e. MAIN DATABASE) ##

    old_csv = pd.read_csv(name_of_weekly_chart)    # загружаем старые данные
    old_csv = old_csv.drop(old_csv.columns[[0]], axis=1) # удаляем получающуюся после импорта лишнюю колонку 
    
    old_csv = old_csv[:-len(G)] # ВАЖНО: удаляем чарт этой недели, в котором еще нет новых метрик

    frames = [old_csv, G]
    new_csv = pd.concat(frames, sort=False)
    new_csv.reset_index(inplace= True)
    new_csv = new_csv.drop(new_csv.columns[[0]], axis=1) 
    
    new_csv.to_csv(name_of_weekly_chart, encoding = "utf-8")

    ## EXPORT TO HTML ##
    # пишем красивые названия колонок
    ch_html = G.drop("raw_rank", 1)
    ch_html=ch_html[["rank", "delta_rank", "best_pos", "title", "artist", "weeks_in_chart", "week"]]
    ch_html.columns = ["Позиция", "Изменение позиции", "Лучшая позиция", "Название", "Артист", "Недель в чарте", "Неделя"]           
    
    html_name = "current_"+name_of_chart+"_html.html"
    ch_html.to_html(html_name, encoding = "utf-8")


# In[ ]:




