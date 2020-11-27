#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# этот скрипт запускается каждую неделю, чтобы сделать новый чарт ИМИ.

# запускать ПОСЛЕ match_songs_all_history.py


# In[ ]:


import pandas as pd
from time import sleep
import datetime
from datetime import datetime, date, time, timezone
from dateutil.relativedelta import relativedelta
import os
from os import path
import itertools
import numpy as np
import json


# In[ ]:


from make_1_imi_chart import make_1_chart, import_separate_charts
from weekly_charts_metrics import metrics_delta, streams_delta
from restore_imi_charts_functions import  beauty_cols, take_one_week, apply_coefs


# In[ ]:


all_charts_glued = import_separate_charts()


# In[ ]:


coef_vk = 19
coef_deezer = 1
coef_yandex = 19
coef_apple = 5
coef_sber = 5

d_coefs = {"vk": coef_vk, "deezer": coef_deezer, "yandex": coef_yandex, "apple": coef_apple, "sber": coef_sber}


# In[ ]:


history = pd.read_csv("all_imi_charts.csv")
history = history.drop(history.columns[[0]], axis = 1)


# In[ ]:


selected_w = datetime.strftime(datetime.now() - relativedelta(days= +7), "%d/%m/%y")+" - " + datetime.strftime(datetime.now() - relativedelta(days= +1), "%d/%m/%y")


# In[ ]:


selected_w = [selected_w]


# In[ ]:


# just an old name of the function
# we do not really "create" history but only work with it here (hence "history" name for pre-existing data)
def create_history(d_coefs, l_links):

    final_charts = history
    estimate_delta_rank = True
    for w in l_links:
        # шлем недельный слайс в make_1_chart
        d_one_track_dfs = make_1_chart(take_one_week(all_charts_glued, w), w)

        # умножаем стримы на коэффициенты
        for pl in d_coefs.keys():
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


# In[ ]:


final_charts = create_history(d_coefs=d_coefs, l_links=selected_w)


# ### EXPORT

# In[ ]:


final_charts.to_csv("all_imi_charts.csv", encoding = "utf-8")


# In[ ]:


#### to json and html  
# note: here we put "week" to the front. then beauty_cols function works with this order and puts "Неделя" first
final_charts_html=final_charts[["week", "rank", "delta_rank", "best_pos", "title", "artist", "streams", "delta_streams", "weeks_in_chart"]]

for i in selected_w:
    final_charts.loc[final_charts["week"]==i].to_json("imi_chart_{}.json".format("_".join("".join(i.split("/")).split(" - "))))
    beauty_cols(final_charts_html.loc[final_charts_html["week"]==i]).to_html("imi_chart_{}.html".format("_".join("".join(i.split("/")).split(" - "))), index = False)


# In[ ]:


selected_w = selected_w[0]


# In[ ]:


print(datetime.now(), " Exported new IMI chart to csv, json and html." )
print("Length of new data: ", len(final_charts_html.loc[final_charts_html["week"]==selected_w]))

