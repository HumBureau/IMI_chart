#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# данный скрипт:


# - осуществляет парсинг ежедневных чартов
# - через API: Deezer
# - через requests: Apple Music
# - через selenium: VK
# - нужен логин и пароль (а также - пока что - запуск браузера)

# - должен запускаться каждый день один раз в сутки. Самое раннее - в 11:30 утра.
# Справка: время обновления исходных чартов.

# Apple Music: 12 a.m. PST  =  10 a.m. Moscow (летом) = 11 a.m. Moscow (зимой)
# => обновлять в 11:30 утра по Москве

# VK: 2:45 a.m Москва
# => обновлять вместе с Apple Music


# - на выходе:
# - обновляет уже хранящиеся данные в csv файлах каждого стриминга, лежащие в корневой директории


# In[3]:


import pandas as pd
import re
import requests
from bs4 import BeautifulSoup
from time import sleep
from random import randint
from datetime import datetime
from dateutil.relativedelta import relativedelta

from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options


# In[5]:


# задаем команду для получения даты
currentDT = datetime.now()


# ### Apple Music

# In[6]:


base_url = 'https://music.apple.com/us/playlist/top-100-russia/pl.728bd30a9247487c80a483f4168a9dcd'
r = requests.get(base_url)
sleep(randint(1, 3))
soup = BeautifulSoup(r.text, 'html.parser')
table = soup.findAll('div', attrs={'class': 'header-and-songs-list'})
songs = soup.findAll('div', attrs={'class': 'song-name typography-label'})
artists = soup.findAll('div', attrs={'class': 'by-line typography-caption'})

# чистим названия треков
songs_clean = BeautifulSoup(str(songs), "lxml").text.split(", \n")
new_l = []
for i in songs_clean:
    v = i.replace("\n", "")
    v = v.replace("[", "")
    v = v.replace("]", "")
    v = v.strip(" ")
    new_l.append(v)
songs_clean = new_l


# чистим названия артистов
artists_clean = BeautifulSoup(str(artists), "lxml").text.split("\n, \n")
new_l = []
for i in artists_clean:
    v = i.replace("\n", "")
    v = v.replace("[", "")
    v = v.replace("]", "")
    v = v.strip(" ")
    new_l.append(v)
artists_clean = new_l

apple_music_top_100_daily = pd.DataFrame()
apple_music_top_100_daily['title'] = songs_clean
apple_music_top_100_daily['artist'] = artists_clean

apple_music_top_100_daily['rank'] = apple_music_top_100_daily.reset_index().index + 1
apple_music_top_100_daily = apple_music_top_100_daily[['rank', 'title', 'artist']]

# дата = предыдущий день (относительно дня скрейпинга)
date = currentDT - relativedelta(days=+1)
apple_music_top_100_daily["date"] = datetime.strftime(date, "%d/%m/%Y")


# In[7]:


# берем имеющийся csv файл и обновляем его

all_apple = pd.read_csv("all_apple.csv")
all_apple = all_apple.drop(all_apple.columns[[0]], axis=1)  # удаляем получающуюся после импорта лишнюю колонку
frames = [all_apple, apple_music_top_100_daily]
all_apple = pd.concat(frames, sort=False)
all_apple.to_csv("all_apple.csv", encoding="utf-8")


# ### VK

# In[ ]:


# selenium-часть
chrome_options = Options()
chrome_options.add_argument("--user-data-dir=chrome-data")
br = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
url = 'https://vk.com'
br.get(url)
sleep(randint(2, 4))

if br.current_url == "https://vk.com/feed":
    print("great, cookies worked for no-login authorisation")
    # now we proceed with scraping

    button2 = br.find_element_by_xpath(
        '//*[(@id = "l_aud")]//*[contains(concat( " ", @class, " " ), concat( " ", "fl_l", " " ))]')
    button2.click()
    sleep(randint(4, 5))
    button3 = br.find_element_by_css_selector('div#content li._audio_section_tab__explore > a')
    button3.click()
    sleep(randint(4, 5))
    button4 = br.find_element_by_css_selector(
        'div#content div.CatalogBlock__recoms_top_audios_global_header.CatalogBlock__header > div > a')
    button4.click()
    sleep(randint(10, 11))
    soup = BeautifulSoup(br.page_source, "lxml")
    br.quit()
else:
    print("ERROR: please do manual login")
    br.quit()

# TODO: ensure br.quit() done if any errors occure

# In[ ]:


# работаем с html

songs = soup.findAll('span', attrs={'class': "audio_row__title_inner _audio_row__title_inner"})
artists = soup.findAll('div', attrs={'class': "audio_row__performers"})

songs_clean = [i.get_text() for i in songs]
artists_clean = [i.get_text() for i in artists]

data = {"rank": [i for i in range(1, 101)], "title": songs_clean, "artist": artists_clean}
vk_music_top_100_daily = pd.DataFrame(data)
# дата = предыдущий день (относительно дня скрейпинга)
date = currentDT - relativedelta(days=+1)
vk_music_top_100_daily["date"] = datetime.strftime(date, "%d/%m/%Y")


# In[ ]:


# берем имеющийся csv файл и обновляем его

all_vk = pd.read_csv("all_vk.csv")
all_vk = all_vk.drop(all_vk.columns[[0]], axis=1)  # удаляем получающуюся после импорта лишнюю колонку
frames = [all_vk, vk_music_top_100_daily]
all_vk = pd.concat(frames, sort=False)
all_vk.to_csv("all_vk.csv", encoding="utf-8")
