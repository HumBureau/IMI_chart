#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# этот скрипт будет функцией make_1_chart

# INPUTS:
## tracks_dict.json
## regression_fitted_values.npy
## Week 
## data for the week
##


# In[32]:


import pandas as pd
import datetime
from datetime import datetime, date, time, timezone
from dateutil.relativedelta import relativedelta
import os
#from os import path
import itertools
import numpy as np
import json


# идея функции:
## проходимся по айди новых данных. находим их в словаре. 
## создаем новый датафрейм или присоединяем к имеющемуся (если нашли не первый раз). 

def make_onetrackdf(glued_charts_df, tracks_dict):
    d_one_track_dfs = {}
    for i in glued_charts_df.iterrows():
        # встречаем первое упоминание песни в glued_charts_df. определяем таблицу в словаре с этой песней.
        found_recs = [k for k, v in tracks_dict.items() if i[1]["full_id"] in list(v["full_id"].values())]
        #print(found_recs)
        # берем оттуда айди всех остальных песен. 
        full_ids_list = list(tracks_dict[found_recs[0]]["full_id"].values())
        # находим их в glued_charts_df
        one_tr_df = glued_charts_df[glued_charts_df["full_id"].isin(full_ids_list)]
        # назначаем общее имя.
        nom = found_recs[0] # тут записан full_id из общего словаря
        # СУММУ НЕ СЧИТАЕМ пока
        d_one_track_dfs[nom] = one_tr_df
        
    return d_one_track_dfs


# In[ ]:


def make_1_chart(data, week):
    
    # 1 send week to the regression
    from imi_regression import get_fitted_values
    fv = get_fitted_values(week)
    
    # 2 "fit" the values for every chart
    for ch in list(set(data["platform"])):
        #ch["s_streams"] = sum(ch["streams"])
        if ch != "spotify":
            data.loc[data['platform'] == ch, 'streams'] = fv[data[data["platform"] == ch]["rank"] - 1]  # note the -1 subtraction!
    
    
    # 3 collect same tracks together
    with open("tracks_dict.json", "r") as outfile:
        td = json.load(outfile)
        
    all_charts_glued = data
    all_charts_glued = all_charts_glued[["title", "artist", "platform", "streams"]]
    all_charts_glued.reset_index(inplace = True, drop = True)
    all_charts_glued["full_id"] = all_charts_glued["title"] +"#bh#" + all_charts_glued["artist"]
    
    d_one_track_dfs = make_onetrackdf(all_charts_glued, td)
    
    return d_one_track_dfs

######## ФУНКЦИЯ КОТОРАЯ "НАХОДИТ" ДОРОГУ К JSON ФАЙЛАМ 
def get_paths():
    p = "/".join(os.getcwd().split("/")[:-1])+"/"
    pd = p+ "Daily/"
    ps = p+ "Spotify_weekly/"
    return (pd,ps)
    


def import_separate_charts():

    # import all weekly charts
    platforms = ["vk", "deezer", "apple", "yandex", "sber"]
    d = {name: pd.read_json(get_paths()[0]+"current_"+name+"_json.json") for name in platforms}
    d["spotify"] = pd.read_json(get_paths()[1]+"current_spotify_json.json")
    d["spotify"]["week"] = d["spotify"]["week_f_show"]

    all_charts_glued = pd.DataFrame()

    for i in d.items():
        i[1]["platform"] = i[0]
        d[i[0]] = i[1].drop(i[1].columns[[0]], axis = 1)
        all_charts_glued = all_charts_glued.append(i[1])
    return all_charts_glued
