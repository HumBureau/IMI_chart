#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# данный скрипт: 

## - осуществляет парсинг еженедельного чарта Spotify Top 200 Russia

## время запуска: утро пятницы
## период чарта: пятница-четверг

## - на выходе:
### - обновляет уже хранящиеся данные прошлых недель в csv 
### - сохраняет html файл актуального чарта для демонстрации на сайте
### - сохраняет json актуального чарта


# In[33]:


import os
import pandas as pd
import re
import requests
from bs4 import BeautifulSoup
from time import sleep
from random import randint
import datetime
from datetime import datetime, date, time, timezone
from dateutil.relativedelta import relativedelta
currentDT = datetime.now() 

from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager
from selenium import webdriver

from bs4 import BeautifulSoup as bs

import pickle


# ### ПАРСИНГ: SPOTIFY WEEKLY TOP 200 RUSSIA

# In[118]:


############################## Сам парсинг #############################

# базовая ссылка на последний актуальный еженедельный чарт по России
base_url = 'https://spotifycharts.com/regional/ru/weekly/latest'
r = requests.get(base_url)
# на всякий случай поставим на паузу
sleep(randint(1,3))
soup = BeautifulSoup(r.text, 'html.parser')
chart = soup.find('table', {'class': 'chart-table'})
tbody = chart.find('tbody')
all_rows = []


# сам скрэйпинг
for tr in tbody.find_all('tr'):
    # позиция трека
    rank_text = tr.find('td', {'class': 'chart-table-position'}).text
    # ссылка на трек
    link_text = tr.a.get("href")
    # название трека
    title_text = tr.find('td', {'class': 'chart-table-track'}).find('strong').text
    # кол-во стримов для трека
    streams_text = tr.find('td', {'class': 'chart-table-streams'}).text
    #cборка таблицы (цикл на случай парсинга нескольких чартов)
    all_rows.append( [rank_text, link_text, title_text, streams_text] )
    
# создаем читаемый датафрейм в pandas
rus_spotify_top_200 = pd.DataFrame(all_rows, columns =['rank','link', "title",'streams'])

#date = дата скрейпинга!
rus_spotify_top_200["date"] = currentDT.strftime("%d/%m/%Y")  

# записываем неделю 
date_start = currentDT - relativedelta(days=+7)
date_end = currentDT - relativedelta(days=+1)
week = datetime.strftime(date_start,"%d/%m/%y") + " - " + datetime.strftime(date_end,"%d/%m/%y")
rus_spotify_top_200["week"] = week


now = datetime.now()

print(now, ": scraped the new chart. length of data:", len(rus_spotify_top_200))


# ### СКРЕЙПИНГ КИРИЛЛИЧЕСКИХ НАЗВАНИЙ АРТИСТОВ

# In[166]:


def get_artist_names(l, title):
    br.get(l)
    # подгружаем куки
    for cookie in pickle.load(open("spotify.pkl", "rb")): 
        br.add_cookie(cookie) 
    #br.get(l)
    sleep(5)
    
    # кликаем на кнопку с динамиком, чтобы (1)убрать зеленую полоску снизу (2) активировать возможность грузить новую песню
    but_sound = br.find_element_by_xpath("//*[contains(@aria-label, 'Выключить звук')]")    
    but_sound.click()
    
    
    # button = br.find_element_by_xpath('//*[@id="main"]/div/div[2]/div[3]/footer/div/div[2]/div/div[1]/div[3]/button')
    # button.click()
    
    # загружаем новую песню
    br.get(l)

    #sleep(5)
    # проверяем, появилась ли песня в now playing bar
    np_found = False
    N=0
    while np_found == False :
        soup = bs(br.page_source, features="lxml")
        artists = soup.find('div', {'class': 'now-playing'})
        if title in str(artists):
            np_found = True
            print("good: song is in the now-playing bar")
        else:
            N+=1
            print("waiting attempt #: ", N)
            sleep(2)
            if N>5:
                print("last big wait, 20 seconds")
                br.get(l)
                sleep(20)
                soup = bs(br.page_source, features="lxml")
                artists = soup.find('div', {'class': 'now-playing'})
                break 

    
    a_l = []
    for j in artists.find_all("a"):
        if "/artist/" in str(j):
            a_l.append(j.text)
    print("success. artists scraped: ", a_l)

    return a_l


# In[177]:


# проходимся по ссылкам на каждую песню из топа и берем с ее страницы "русские" названия артистов


def artists_scraping():
    global br
    options = Options()
    options.add_argument('-headless')

    profile = webdriver.FirefoxProfile()
    profile.set_preference('intl.accept_languages', 'rus-RUS, ru')
    profile.set_preference('media.gmp-manager.updateEnabled', True)

    br = webdriver.Firefox(executable_path=GeckoDriverManager().install(), firefox_profile=profile, options = options)


    A_L = []
    for i in rus_spotify_top_200.iterrows():
        print("working on the title: ", (i[1]["title"]))
        try:
            A_L.append(", ".join(get_artist_names(i[1]["link"], i[1]["title"])))
        except:
            print("issue with webdriver. reloading and continuing from where I stopped")
            br.quit()

            # перезапускаем вебдрайвер

            options = Options()
            options.add_argument('-headless')

            profile = webdriver.FirefoxProfile()
            profile.set_preference('intl.accept_languages', 'rus-RUS, ru')
            profile.set_preference('media.gmp-manager.updateEnabled', True)  

            br = webdriver.Firefox(executable_path=GeckoDriverManager().install(), firefox_profile=profile, options = options)
            A_L.append(", ".join(get_artist_names(i[1]["link"], i[1]["title"])))

    br.quit()
    
    return A_L
    

    
    # останавливаем трек, чтобы следующий URL запустил новый трек
    #button = br.find_element_by_xpath('//*[@id="main"]/div/div[2]/div[3]/footer/div/div[2]/div/div[1]/div[3]/button')

    #while str(button.get_attribute("data-testid")) == "control-button-pause":
    #    button.click()
    #    sleep(2)
    #    button = br.find_element_by_xpath('//*[@id="main"]/div/div[2]/div[3]/footer/div/div[2]/div/div[1]/div[3]/button')

    #if str(button.get_attribute("data-testid")) == "control-button-play":
        #print("good, track is stopped. now can load next one")
    #else:
        #print("ERROR, could not stop the track")


# In[178]:


a_scrp = False

while a_scrp == False:
    A_L_export = artists_scraping()
    if len(A_L_export) == len(rus_spotify_top_200):
        rus_spotify_top_200["artist"] = A_L_export
        a_scrp = True
        print("Artists scraping: success.")
        break
    else:
        print("Error: list of artists is not complete. I am repeating scraping.")
    
rus_spotify_top_200 = rus_spotify_top_200[["rank", "title", "artist", "streams", "week"]]    


# In[180]:





# In[ ]:





# In[ ]:





# ### ФОРМИРУЕМ ПОЛНЫЙ ЧАРТ

# In[3]:


# функция для подсчета количества недель, которые песня держится в чарте

def weeks_in_chart(weekly_charts):
    
    df = weekly_charts
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


# In[4]:


# пишем функцию, которая считает best position in chart, weeks in chart, change in rank [vs previous week]

def metrics_delta(chart):
    
    chart.reset_index(inplace=True)
    chart.drop("index", axis = 1, inplace = True)
    
    #### best position
    chart["rank"] = chart["rank"].astype(int)
    best_pos = pd.DataFrame(chart.groupby(['title', 'artist']).agg({'rank' : 'min'}))
    best_pos.reset_index(inplace=True)
    best_pos.columns = ['title', 'artist', 'best_pos']
    best_pos["best_pos"] = best_pos["best_pos"].astype('Int64') 
    
    
    
    #### change in rank vs previous week
    # назначаем  последнюю (т.е. актуальную) неделю
    
    chart_last_week = chart.loc[chart['week'] == chart['week'].values[-1]] 
    chart_dropped  = chart.drop(chart[chart['week'] == chart['week'].values[-1]].index)
    
    # назначаем предпоследнюю (т.е. предыдущую) неделю
    if len(chart_dropped) == 0:
        chart_previous_week = chart.loc[chart['week'] == chart['week'].values[1]]
    else: 
        chart_previous_week = chart_dropped.loc[chart_dropped['week'] == chart_dropped['week'].values[-1]]
    chart_previous_week = chart_previous_week[['title', 'artist', 'rank']]
    
    # ! chart_upd - это датафрейм, который мы строим
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


# In[5]:


# функция для подсчета изменения прослушиваний
def streams_delta_spot(chart): 
    
    try:
        chart['streams'] = chart['streams'].astype(str).str.replace(",", "").astype(int)
    except:
        5+3
        
    chart_last_week = chart[chart['week'] == chart['week'].values[-1]]
    chart_dropped  = chart.drop(chart[chart['week'] == chart['week'].values[-1]].index)
    if len(chart_dropped) == 0:
        chart_previous_week = chart.loc[chart['week'] == chart['week'].values[1]]
    else: 
        chart_previous_week = chart_dropped.loc[chart_dropped['week'] == chart_dropped['week'].values[-1]]
    chart_previous_week = chart_previous_week[['title', 'artist', 'streams']]
    chart_upd = pd.merge(chart_last_week, chart_previous_week, how='left', on=['title', 'artist'])
    chart_upd["streams_y"].fillna(0, inplace=True)
    chart_upd['delta_streams'] = (chart_upd['streams_x'] - chart_upd['streams_y']).astype('Int64')
    chart_upd = chart_upd[['title', 'artist', 'delta_streams']]
    
    return chart_upd


# In[6]:


if os.path.exists("all_spotify.csv") == False:
    df = pd.DataFrame(columns=['rank', 'title', 'artist', 'date', 'streams', 'week',
                               'delta_rank', 'weeks_in_chart', 'best_pos', 'delta_streams', 'full_id'])
    df.to_csv("all_spotify.csv", encoding="utf-8")

# соединяем старые данные с новыми (но пока без экспорта)

all_spotify = pd.read_csv("all_spotify.csv")

all_spotify = all_spotify.drop(all_spotify.columns[[0]], axis=1) # удаляем получающуюся после импорта лишнюю колонку 

frames = [all_spotify, rus_spotify_top_200]
all_spotify = pd.concat(frames, sort=False) 


# In[7]:


# подсчитываем все дополнительные показатели
sp1 = streams_delta_spot(all_spotify) # count delta_streams
spotify_curr_week = metrics_delta(all_spotify) # count other metrics
spotify_curr_week.drop("delta_streams", 1, inplace=True) # drop so that columns don't duplicate

# merge delta_streams and other metrics
spotify_curr_week = pd.merge(spotify_curr_week, sp1, how='left', on=['title', 'artist'])


# In[184]:


rus_spotify_top_200


# ### ЭКСПОРТ 

# In[ ]:


### EXPORT TO JSON
with open('current_spotify_json.json', 'w', encoding='utf-8') as file:
    spotify_curr_week.to_json(file, force_ascii=False)


# In[ ]:


### EXPORT TO HTML
# сохраняем html для использования на сайте (т.е. через Make_weekly_charts.py впоследствии)
spotify_curr_week_html=spotify_curr_week[["rank", "delta_rank", "best_pos", "title", "artist", "streams", "delta_streams", "weeks_in_chart", "week"]]
spotify_curr_week_html.columns = ["Позиция", "Изменение позиции", "Лучшая позиция", "Название", "Артист", "Прослушивания", "Динамика прослушиваний", "Недель в чарте", "Неделя"]
spotify_curr_week_html.to_html("current_spotify_html.html", encoding = "utf-8")


# In[ ]:


### EXPORT TO CSV - (i.e. TO THE MAIN DATABASE)
# берем имеющийся в корневой директории csv файл и обновляем его

all_spotify = pd.read_csv("all_spotify.csv")
all_spotify = all_spotify.drop(all_spotify.columns[[0]], axis=1) # удаляем получающуюся после импорта лишнюю колонку 
frames = [all_spotify, spotify_curr_week]
all_spotify = pd.concat(frames, sort=False)
all_spotify.drop_duplicates(inplace = True) 
all_spotify.reset_index(inplace=True)
all_spotify.drop(all_spotify.columns[[0]], axis=1, inplace=True)

all_spotify.to_csv("all_spotify.csv", encoding = "utf-8")

now = datetime.now()
print(now, ": updated all_spotify.csv with this week's chart.")

