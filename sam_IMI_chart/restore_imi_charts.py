#!/usr/bin/env python
# coding: utf-8

# In[1]:


# Этот скрипт считает все чарты ИМИ (с момента появления СберЗвука в данных )


# In[2]:


import pandas as pd
from time import sleep
import datetime
from datetime import datetime, date, time, timezone
from dateutil.relativedelta import relativedelta
from os import path
import itertools
import numpy as np
import json


# In[1]:


from make_1_imi_chart import make_1_chart
from weekly_charts_metrics import metrics_delta, streams_delta
from restore_imi_charts_functions import beauty_cols


# In[4]:


def take_one_week(df,  w):
    return df[df["week"] == w]


# In[5]:


def apply_coefs(di, pl):
    for k,v in di.items():
        v.loc[v["platform"] == pl, "streams"] = v.loc[v["platform"] == pl, "streams"]*d_coefs.get(pl)


# In[6]:


# create list with correct dates for weekly charts creating (basically a list of Fridays)
### NOTE: we start from when we first had SberZvuk!

cor_m_dates = [datetime(2020, 10, 23, 0, 0)]
while cor_m_dates[-1] +relativedelta(days = +7) <= datetime.now():
    cor_m_dates.append(cor_m_dates[-1] +relativedelta(days = +7))

l_links = []
for day in cor_m_dates[:-1]:
    w_f_link = datetime.strftime(day, "%d/%m/%y")+" - "+datetime.strftime(day+relativedelta(days = +6), "%d/%m/%y")
    #print(w_f_link)
    l_links.append(w_f_link)


# In[7]:


l_links= l_links[:-1]
l_links


# In[8]:


# delete the old data with weekly charts
empty_df = pd.DataFrame(columns = ['rank', 'title', 'artist', "week", "raw_rank", 'weeks_in_chart','best_pos', 'delta_rank'])
empty_df.to_csv("all_imi_charts.csv", encoding = "utf-8")


# In[9]:


# import all weekly charts
platforms = ["vk", "deezer", "apple", "yandex", "sber"]
d = {name: pd.read_csv("all_"+name+"_weekly.csv") for name in platforms}
d["spotify"] = pd.read_csv("all_spotify.csv")
d["spotify"]["week"] = d["spotify"]["week_f_show"]

all_charts_glued = pd.DataFrame()

for i in d.items():
    i[1]["platform"] = i[0]
    d[i[0]] = i[1].drop(i[1].columns[[0]], axis = 1)
    all_charts_glued = all_charts_glued.append(i[1])


# In[10]:


coef_vk = 19
coef_deezer = 1
coef_yandex = 19
coef_apple = 5
coef_sber = 5

d_coefs = {"vk": coef_vk, "deezer": coef_deezer, "yandex": coef_yandex, "apple": coef_apple, "sber": coef_sber}


# In[11]:


def create_history(d_coefs, l_links):

    final_charts = empty_df
    estimate_delta_rank = False
    for w in l_links:
        # шлем недельный слайс в make_1_chart
        d_one_track_dfs = make_1_chart(take_one_week(all_charts_glued, w), w)

        # умножаем стримы на коэффициенты
        for pl in d_coefs.keys():
            apply_coefs(d_one_track_dfs, pl)

        # считаем сумму
        d_final = d_one_track_dfs
        chart = pd.DataFrame()
        chart["title"] = [i.split("#bh#")[0] for i in list(d_final.keys())]
        chart["artist"] = [i.split("#bh#")[1] for i in list(d_final.keys())]
        chart["streams"] = [round(sum(d_final[i]["streams"]), 0) for i in list(d_final.keys())]
        chart.sort_values(by = "streams", ascending = False, inplace = True)
        chart.reset_index(inplace=True, drop = True)
        chart.reset_index(inplace=True)
        chart["rank"] = chart[chart.columns[[0]]] + 1
        chart["week"] = w

        new_chart = chart.drop(chart.columns[[0]], axis = 1)

        # склеиваем с предыдущими ИМИ чартами для подсчета метрик
        working_all_charts = pd.concat([final_charts, new_chart], ignore_index=True)

        if estimate_delta_rank == False:
            new_chart_w_metrics = working_all_charts
            #new_chart_w_metrics["delta_rank"] = None
        else:

            df_streams = streams_delta(working_all_charts) # count delta_streams
            df_metrics = metrics_delta(working_all_charts) # count other metrics
            if "delta_streams" in df_metrics.columns:
                df_metrics.drop("delta_streams", 1, inplace=True) # drop so that columns don't duplicate

            # merge delta_streams and other metrics
            new_chart_w_metrics = pd.merge(df_metrics, df_streams, how='left', on=['title', 'artist'])

        final_charts = pd.concat([final_charts, new_chart_w_metrics], ignore_index=True)

        estimate_delta_rank = True #сигнал, что в следующую неделю можно считать delta_rank
    
    return final_charts


# In[12]:


final_charts = create_history(d_coefs, l_links)


# ### Export

# In[17]:


final_charts.to_csv("all_imi_charts.csv", encoding = "utf-8")


# In[20]:


#### to json and html  
# note: here we put "week" to the front. then beauty_cols function works with this order and puts "Неделя" first
final_charts_html=final_charts[["week", "rank", "delta_rank", "best_pos", "title", "artist", "streams", "delta_streams", "weeks_in_chart"]]

for i in set(final_charts["week"]):
    final_charts.loc[final_charts["week"]==i].to_json("imi_chart_{}.json".format("_".join("".join(i.split("/")).split(" - "))))
    beauty_cols(final_charts_html.loc[final_charts_html["week"]==i]).to_html("imi_chart_{}.html".format("_".join("".join(i.split("/")).split(" - "))), index = False)

