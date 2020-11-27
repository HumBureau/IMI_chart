#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# Этот скрипт считает все чарты ИМИ (с момента появления СберЗвука в данных )


# In[ ]:


import pandas as pd
from time import sleep
import datetime
from datetime import datetime, date, time, timezone
from dateutil.relativedelta import relativedelta
from os import path
import itertools
import numpy as np
import json


# In[ ]:


from make_1_imi_chart import make_1_chart
from weekly_charts_metrics import metrics_delta 


# In[ ]:


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


# In[ ]:


def take_one_week(df,  w):
    return df[df["week"] == w]


# In[ ]:


def apply_coefs(di, pl, d_coefs):
    for k,v in di.items():
        v.loc[v["platform"] == pl, "streams"] = v.loc[v["platform"] == pl, "streams"]*d_coefs.get(pl)






# In[1]:

#note: start_df = стартовые данные. 
## для полного подсчета истории (в т.ч. в кастомных чартах) нужно послать сюда empty_df. 
## для подсчета свежего чарта – all_imi_charts.csv 

def create_history(d_coefs, l_links, all_charts_glued, start_df):
    final_charts = start_df
    if len(start_df)>0:
        estimate_delta_rank = True
    else:
        estimate_delta_rank = False
        
    for w in l_links:
        # шлем недельный слайс в make_1_chart
        d_one_track_dfs = make_1_chart(take_one_week(all_charts_glued, w), w)
        

        # умножаем стримы на коэффициенты
        for pl in d_coefs.keys():
            if pl != "spotify":
                apply_coefs(d_one_track_dfs, pl, d_coefs)

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
        
        print(new_chart)

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
        print(new_chart_w_metrics)
        final_charts = pd.concat([final_charts, new_chart_w_metrics], ignore_index=True)

        estimate_delta_rank = True #сигнал, что в следующую неделю можно считать delta_rank
    
    return final_charts



# In[ ]:


def beauty_cols(c):
    c.columns = ["Неделя", "Позиция", "Изменение позиции vs прошлая неделя", "Лучшая позиция с начала наблюдений (23/10/20-29/10/20)", "Название", "Артист", "Наша оценка прослушиваний", "Динамика прослушиваний vs прошлая неделя", "Недель в чарте"]
    c.reset_index(inplace = True, drop = True)
    return c



