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


# In[ ]:


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
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager
from selenium import webdriver
from bs4 import BeautifulSoup as bs
import spotipy
import spotipy.util as util
from selenium.webdriver.common.action_chains import ActionChains

currentDT = datetime.now() 


# In[ ]:


# авторизуемся в API спотифая

client_id = 'ab06777876f4480c945208f0d0d16160'
client_secret = 'e02805f2372249f1afe66ec7b3d6e20a'
username = "11158413093"
scope = "playlist-modify-public"
playlist_id = "6n485XL3OjM56Lwax8LVQb"
redirect_uri='http://localhost:8080'
CACHE = '.spotipyoauthcache'


### SP - это объект, который занимается авторизацией
SP = spotipy.oauth2.SpotifyPKCE(client_id=client_id, redirect_uri=redirect_uri, scope=scope, username=username, cache_path = CACHE, proxies=None, requests_timeout=None, requests_session=True, open_browser=False)


### смело пробуем получить новый access token просто через refresh token, лежащий в кэше
# 1 берем refresh token 
refr_t = SP.get_cached_token()["refresh_token"]
# 2 рефрешим access token
try:
    SP.refresh_access_token(refresh_token=refr_t)
    print(datetime.now(), ": ", "Refreshed access token OK.")
except Exception as e:
    print(datetime.now(), ": ", e)

### sp - это объект, который занимается управлением (редактированием плейлистов и т.д.)
sp = spotipy.Spotify(auth = SP.get_access_token())


# In[ ]:


# функция, которая собирает данные из spotifycharts, включая ссылки на треки
def scrape(d):
############################## Сам парсинг #############################

    # базовая ссылка на последний актуальный еженедельный чарт по России
    base_url = 'https://spotifycharts.com/regional/ru/weekly/'+d
    r = requests.get(base_url)
    # на всякий случай поставим на паузу
    sleep(2)
    soup = BeautifulSoup(r.text, 'html.parser')
    chart = soup.find('table', {'class': 'chart-table'})
    wt = 2
    
    # цикл на случай, если не загрузилось
    while len(chart) == 0:
        wt = wt+2
        r = requests.get(base_url)
        sleep(wt)
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
    #rus_spotify_top_200["date"] = currentDT.strftime("%d/%m/%Y")  

    # записываем неделю 
    #date_start = currentDT - relativedelta(days=+7)
    #date_end = currentDT - relativedelta(days=+1)
    #week = datetime.strftime(date_start,"%d/%m/%y") + " - " + datetime.strftime(date_end,"%d/%m/%y")
    week = d
    rus_spotify_top_200["week"] = week


    now = datetime.now()

    print(now, ": scraped the new chart. length of data:", len(rus_spotify_top_200))
    
    return rus_spotify_top_200


# In[ ]:


def get_25_artists(I):


    url = "https://open.spotify.com/playlist/"+I


    options = Options()
    options.add_argument('-headless')

    profile = webdriver.FirefoxProfile()
    profile.set_preference('intl.accept_languages', 'rus-RUS, ru')
    profile.set_preference('media.gmp-manager.updateEnabled', True)

    br = webdriver.Firefox(executable_path=GeckoDriverManager().install(), firefox_profile=profile, options = options)

    br.get(url)


    sleep(5)

    soup = bs(br.page_source, parser = "lxml")
    
    H = soup.find_all("span", {"class":"_966e29b71d2654743538480947a479b3-scss"})
    i_l = []
    for h in H:
        i_l.append(h.get_text())
    
    br.quit()
        
    return i_l


# In[ ]:


# создаем ссылку на нужную неделю

# дата начала 
cor_m_dates = [datetime(2020, 7, 10, 0, 0)]

while cor_m_dates[-1] +relativedelta(days = +7) <= datetime.now():
    cor_m_dates.append(cor_m_dates[-1] +relativedelta(days = +7))

if cor_m_dates[-1] +relativedelta(days = +7) > datetime.now():
    cor_m_dates=cor_m_dates[:-1]
    
curr_date_start = cor_m_dates[-1]
w_f_link = datetime.strftime(curr_date_start, "%Y-%m-%d")+"--"+datetime.strftime(curr_date_start+relativedelta(days = +7), "%Y-%m-%d")


# In[ ]:


full_df = pd.DataFrame(columns = ["rank", "title", "artist", "streams", "week", "link"])


# In[ ]:


# сбор имен артистов через добавление треков из топ-200 в плейлист партиями по 25 треков


while True:
    try:
        # скрейпим spotifycharts
        curr_df = scrape(w_f_link)
        links = list(curr_df["link"])
        id_list=[]
        A_L = []
        for L in links:
            id_list.append(L.split("/")[-1])
            if len(id_list) == 25:
                #print(id_list)
                sp.user_playlist_add_tracks(username, playlist_id = playlist_id, tracks = id_list, position=None)
                A_L.extend(get_25_artists(playlist_id))
                # clear playlist
                sp.user_playlist_remove_all_occurrences_of_tracks(username, playlist_id=playlist_id, tracks = id_list, snapshot_id=None)
                # clear list 
                s_id_list = id_list
                id_list = []
                #print(len(A_L), A_L)

        curr_df["artist"] = A_L
        print(datetime.now(), ": Added correct artist names")

        curr_df=curr_df[["rank", "title", "artist", "streams", "week", "link"]]

        frames = [full_df, curr_df]
        full_df=pd.concat(frames, sort=False)

        full_df.reset_index(inplace=True)
        full_df.drop(full_df.columns[[0]], axis=1, inplace=True)
        break
    except Exception as e:
        print(datetime.now(), ": ", e)
        sp.user_playlist_remove_all_occurrences_of_tracks(username, playlist_id=playlist_id, tracks = s_id_list, snapshot_id=None)
        sleep(3600)
        token = util.prompt_for_user_token(username,scope,client_id=client_id,client_secret=client_secret,redirect_uri='http://localhost/') 
        sp = spotipy.Spotify(auth = token)


# In[ ]:


# удаляем запятые в числах

n_s = []
for i in full_df["streams"]:
    h = int("".join(i.split(",")))
    n_s.append(h)

full_df["streams"] = n_s


# ### ФОРМИРУЕМ ПОЛНЫЙ ЧАРТ

# In[ ]:


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


# In[ ]:


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


# In[ ]:


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
    #chart_upd["streams_y"].fillna(0, inplace=True)
    chart_upd['delta_streams'] = (chart_upd['streams_x'] - chart_upd['streams_y']).astype('Int64')
    chart_upd = chart_upd[['title', 'artist', 'delta_streams']]
    
    return chart_upd


# In[ ]:


if os.path.exists("all_spotify.csv") == False:
    df = pd.DataFrame(columns=['rank', 'title', 'artist', 'date', 'streams', 'week',
                               'delta_rank', 'weeks_in_chart', 'best_pos', 'delta_streams', 'full_id', "week_f_show"])
    df.to_csv("all_spotify.csv", encoding="utf-8")

# соединяем старые данные с новыми (но пока без экспорта)

all_spotify = pd.read_csv("all_spotify.csv")

all_spotify = all_spotify.drop(all_spotify.columns[[0]], axis=1) # удаляем получающуюся после импорта лишнюю колонку 


# In[ ]:


frames = [all_spotify, curr_df]
all_spotify = pd.concat(frames, sort=False) 


# In[ ]:


# подсчитываем все дополнительные показатели
sp1 = streams_delta_spot(all_spotify) # count delta_streams
spotify_curr_week = metrics_delta(all_spotify) # count other metrics
spotify_curr_week.drop("delta_streams", 1, inplace=True) # drop so that columns don't duplicate

# merge delta_streams and other metrics
spotify_curr_week = pd.merge(spotify_curr_week, sp1, how='left', on=['title', 'artist'])


# In[ ]:



# добавляем настоящие названия недель (а не те, что в ссылках)

w = spotify_curr_week["week"][0]
ed = datetime.strptime(w[-10:], "%Y-%m-%d") - relativedelta(days=+1)
sd = datetime.strptime(w[:10], "%Y-%m-%d") 
w_f_show = datetime.strftime(sd,  "%d/%m/%y")+" - "+datetime.strftime(ed,  "%d/%m/%y")
spotify_curr_week["week_f_show"] = w_f_show


# In[ ]:


# добавляем сумму всех стримов за неделю (для чарта ИМИ)

spotify_curr_week["s_streams"] =  sum(spotify_curr_week["streams"])


# ### ЭКСПОРТ 

# In[ ]:


### EXPORT TO JSON
with open('current_spotify_json.json', 'w', encoding='utf-8') as file:
    spotify_curr_week.to_json(file, force_ascii=False)


# In[ ]:


### EXPORT TO HTML
# сохраняем html для использования на сайте (т.е. через Make_weekly_charts.py впоследствии)
spotify_curr_week_html=spotify_curr_week[["rank", "delta_rank", "best_pos", "title", "artist", "streams", "delta_streams", "weeks_in_chart", "week_f_show"]]
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

