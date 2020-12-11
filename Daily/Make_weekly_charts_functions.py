#!/usr/bin/env python
# coding: utf-8

# In[7]:


import pandas as pd
import datetime
from datetime import datetime, date, time, timezone
from dateutil.relativedelta import relativedelta
import heapq


def w_e_s(list_):
    if len(list_) == 0:
        return ""
    else:
        return list_[0]


# функция для получения недельного чарта через усреднение ежедневных
# только для apple, deezer, VK


def average(df):
    
    # задаем команду для получения даты
    currentDT = datetime.now() 

    # округляем дату до ровно начала суток
    currentDT = datetime.strptime(datetime.strftime(currentDT, "%d/%m/%Y"), "%d/%m/%Y")

    # сделаем вспомогательные объекты для работы с датами
    all_dates = []
    for i in range(1,8):
        k = currentDT - relativedelta(days=+i)
        all_dates.append(datetime.strftime(k, "%d/%m/%Y"))

    date_start = currentDT - relativedelta(days=+7)
    date_end = currentDT - relativedelta(days=+1)
  
    df['Datetime'] = [datetime.strptime(i, "%d/%m/%Y") for i in df["date"]]
    
    # take last week only

    last_week_df = df[date_start <= df["Datetime"]]
    last_week_df = last_week_df[last_week_df["Datetime"] <= date_end ]
    df = last_week_df
    
    ### start averaging
    
    raw_rank, songs, artists, genres, labels = ([] for i in range(5))

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
                # выясняем длину чарта в тот день
                one_DAY_df = df[df["date"] == day]
                if len(one_DAY_df) >0:
                    # добавляем rank равный строчке после последней видимой
                    added_ranks.append(len(one_DAY_df) + 1)  
                    print("track ", i, "is not in chart on:", day)
                    print("I am assigning rank = ", len(one_DAY_df) + 1)
                else:
                    # сокращаем делитель на 1 (т.к. такого дня нет в данных вообще)
                    print("No chart for this day. Will change the demominator in the average rank formula.")
                    print("Day: ", day)
                    denominator = denominator - 1
            
            full_ranks = added_ranks
            full_ranks.extend(list(one_track_df["rank"]))
            
            # наконец считаем среднюю строку за неделю    
            if len(full_ranks) > denominator:
                # так бывает, если в чарте есть и сингл, и альбом
                print("Found a song with more appearances than # of saved charts in this week (including added added 'n+1' ranks). Taking the highest # ranks only. ", i )
                average_rank = sum(heapq.nsmallest(7, full_ranks)) / denominator
            else:
                average_rank = (sum(full_ranks)) / denominator  
                 
            songs.append(i)
            artists.append(j)
            raw_rank.append(average_rank)
            genres.append(w_e_s(one_track_df["genre"].dropna().unique().tolist()))
            labels.append(w_e_s(one_track_df["label"].dropna().unique().tolist()))
    
    # соединяем данные в новую таблицу
    cols = ['raw_rank', 'title', 'artist', "genre", "label"]
    data = dict(zip(cols, [raw_rank, songs, artists, genres, labels]))        
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
    
    new_chart = new_chart[['rank', 'title', 'artist', "week", "raw_rank", "genre", "label"]]
    
    # округляем raw_rank
    new_chart["raw_rank"] = round(new_chart["raw_rank"], 3)
    
    return new_chart

