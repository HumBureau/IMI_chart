#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# данный скрипт: 


## - осуществляет парсинг ежедневных чартов
### - через selenium: VK


## - должен запускаться каждый день один раз в сутки. Самое раннее - в 03:45 утра.
## Справка: время обновления исходных чартов.

### VK: 2:45 a.m Москва



## - на выходе:
### - обновляет all_vk.csv


# In[ ]:


import pandas as pd
import re
import requests
from bs4 import BeautifulSoup
from time import sleep
from random import randint
from datetime import datetime
from dateutil.relativedelta import relativedelta
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager
import pickle 
import json


# In[ ]:


# задаем команду для получения даты
currentDT = datetime.now() 


# In[ ]:


def get_genre_streams(item):
    
    streams = None # видимо, бывает так, что никакой инфы про прослушивания нет вообще (а аутпут все равно нужен)
    l_w_album_path = json.loads(BeautifulSoup(str(item).split(">")[0]+">", "lxml").div["data-audio"])[-7]
    if l_w_album_path!=False:
        id_alb_p = "_".join([str(i) for i in l_w_album_path])
        alb_l = "https://vk.com/music/album/"+id_alb_p
        br.get(alb_l) 
        sleep(randint(4,5))
        soup = BeautifulSoup(br.page_source, features="lxml")
        l = soup.findAll('div', attrs={'class':"AudioPlaylistSnippet__info"})
        for i in l:
            # эти элементы быват двух видов. в одном кол-во прослушиваний, в другом - жанр
            if "прослушивани" in i.get_text():
                if "1 аудиозапись" in i.get_text():
                    if "M" in i.get_text():
                        streams = float(i.get_text().split("M")[0].strip()) *1000000
                    if "K" in i.get_text():
                        streams = float(i.get_text().split("K")[0].strip()) *1000        
                elif "аудиозапис" in i.get_text():
                    streams = None
                    # отсеиваем (настоящие) альбомы
                    pass

                else:
                    if "M" in i.get_text():
                        streams = float(i.get_text().split("M")[0].strip()) *1000000
                    if "K" in i.get_text():
                        streams = float(i.get_text().split("K")[0].strip()) *1000

            else:
                genre = i.get_text().split("·")[0].strip()
    else:
        genre = None
        streams = None
        print("no album page found for a track ", json.loads(BeautifulSoup(str(item).split(">")[0]+">", "lxml").div["data-audio"])[3])
            
    return genre, streams


# ### VK 

# In[ ]:


# запускаем селениум и получаем страницу с чартом 

options = Options()
options.add_argument('-headless')
br = webdriver.Firefox(executable_path=GeckoDriverManager().install(), options = options)
url='https://vk.com'
br.get(url)
for cookie in pickle.load(open("vkcooks.pkl", "rb")): 
    br.add_cookie(cookie) 
br.get(url)

if br.current_url == "https://vk.com/feed":
    print(datetime.now(), ": great, cookies worked for no-login authorisation")
    url = "https://vk.com/audios528693184?block=tracks_chart&section=explore"
    #url = "https://vk.com/audios8910036?block=tracks_chart&section=explore"
    br.get(url)
    # now we proceed with scraping
    #button2 = br.find_element_by_xpath('//*[@id="l_aud"]/a')
    #button2.click()
    #sleep(randint(4,5))
    #button3 = br.find_element_by_css_selector('div#content li._audio_section_tab__explore > a')
    #button3 = br.find_element_by_xpath("//a[normalize-space()='Обзор']")
    #button3.click()
    #sleep(randint(4,5))
    #button4 = br.find_element_by_css_selector('div#content div.CatalogBlock__recoms_top_audios_global_header.CatalogBlock__header > div > a')
    #button4.click()
    #sleep(randint(10,11))
    soup = BeautifulSoup(br.page_source, features="lxml")
    #br.quit()
else:
    print("ERROR: please do manual login")


# In[ ]:


# работаем с html

songs = soup.findAll('span', attrs={'class':"audio_row__title_inner _audio_row__title_inner"})
artists = soup.findAll('div', attrs={'class':"audio_row__performers"})

# получаем жанры и (общее) кол-во прослушиваний
for_albums = soup.findAll('div', attrs={'onclick':"return getAudioPlayer().toggleAudio(this, event)"})
genres_streams = [get_genre_streams(i) for i in for_albums]

br.quit()


# In[ ]:


songs_clean = [i.get_text() for i in songs]
artists_clean = [i.get_text() for i in artists]
cols = ['rank', 'title', 'artist', "genre", "comp_streams"]
data = dict(zip(cols, [[i for i in range(1, len(songs_clean)+1)], songs_clean, artists_clean, [i[0] for i in genres_streams],[i[1] for i in genres_streams] ])) 
vk_music_top_100_daily = pd.DataFrame(data)
# дата = предыдущий день (относительно дня скрейпинга)
date = currentDT - relativedelta(days=+1)
vk_music_top_100_daily["date"] = datetime.strftime(date,"%d/%m/%Y")  


# In[ ]:


# берем имеющийся csv файл и обновляем его

all_vk = pd.read_csv("all_vk.csv")
all_vk = all_vk.drop(all_vk.columns[[0]], axis=1) # удаляем получающуюся после импорта лишнюю колонку 

now = datetime.now()

# проверяем, не сохраняли ли мы уже данные за этот день:
if datetime.strftime(date, "%d/%m/%Y") in set(all_vk["date"]):
    print(now, ": this date's VK data is already saved. Not saving new data.")
else:
    print(now, ": this date's VK chart is not in our data yet. I proceed to save it and export to csv.")
    frames = [all_vk, vk_music_top_100_daily]
    all_vk = pd.concat(frames, sort=False)
    all_vk.reset_index(inplace=True)
    all_vk.drop(all_vk.columns[[0]], axis=1, inplace=True)
    all_vk.to_csv("all_vk.csv", encoding = "utf-8")

