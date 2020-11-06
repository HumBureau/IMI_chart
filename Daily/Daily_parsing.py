#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# данный скрипт: 


## - осуществляет парсинг ежедневных чартов
### - через API: Deezer
### - через requests: Apple Music
### - через selenium: VK
#### - нужен логин и пароль (а также - пока что - запуск браузера)

## - должен запускаться каждый день один раз в сутки. Самое раннее - в 11:30 утра.
## Справка: время обновления исходных чартов.

### Apple Music: 12 a.m. PST  =  10 a.m. Moscow (летом) = 11 a.m. Moscow (зимой)
#### => обновлять в 11:30 утра по Москве

### VK: 2:45 a.m Москва
### => обновлять вместе с Apple Music



## - на выходе:
### - обновляет уже хранящиеся данные в csv файлах каждого стриминга, лежащие в корневой директории


# In[1]:


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


# In[2]:


# задаем команду для получения даты
currentDT = datetime.now() 


# ### Apple Music

# In[3]:


base_url = 'https://music.apple.com/ru/playlist/top-100-russia/pl.728bd30a9247487c80a483f4168a9dcd'
r = requests.get(base_url)
sleep(randint(1,3))
soup = BeautifulSoup(r.text, 'html.parser')

all_texts = soup.findAll('div', attrs={'class':"song-name-wrapper"})

a_l=[]
s_l=[]

for i in all_texts:
    # check if empty artist name
    if len(i.findAll('div', attrs={'class':'by-line typography-caption'})) == 0:
        a = ""
        a_l.append(a)
    else:
        a = i.findAll('div', attrs={'class':'by-line typography-caption'})
        ar_l = [j.rstrip().lstrip() for j in a[0].get_text().rstrip().lstrip().split(",")]
        a = ", ".join(ar_l)
        a_l.append(a)
    s = i.findAll('div', attrs={'class':'song-name typography-label'})[0].get_text()
    s = s.replace("\n", "")
    s = s.replace("[", "")
    s = s.replace("]", "")
    s = s.strip(" ")
    s_l.append(s)    

apple_music_top_100_daily = pd.DataFrame()
apple_music_top_100_daily['title'] = s_l
apple_music_top_100_daily['artist'] = a_l
apple_music_top_100_daily['rank'] = apple_music_top_100_daily.reset_index().index +1
apple_music_top_100_daily = apple_music_top_100_daily[['rank', 'title', 'artist']]

# дата = предыдущий день (относительно дня скрейпинга)
date = currentDT - relativedelta(days=+1)
apple_music_top_100_daily["date"] = datetime.strftime(date,"%d/%m/%Y")  


# In[ ]:


# берем имеющийся csv файл и обновляем его

all_apple = pd.read_csv("all_apple.csv")
all_apple = all_apple.drop(all_apple.columns[[0]], axis=1) # удаляем получающуюся после импорта лишнюю колонку 
frames = [all_apple, apple_music_top_100_daily]
all_apple = pd.concat(frames, sort=False)
all_apple.to_csv("all_apple.csv", encoding = "utf-8")


# ### VK 

# In[ ]:


# selenium-часть
options = Options()
options.add_argument('-headless')
br = webdriver.Firefox(executable_path=GeckoDriverManager().install(), options = options)
url='https://vk.com'
br.get(url)
for cookie in pickle.load(open("vkcooks.pkl", "rb")): 
    br.add_cookie(cookie) 
br.get(url)

if br.current_url == "https://vk.com/feed":
    print("great, cookies worked for no-login authorisation")
    # now we proceed with scraping
    
    button2 = br.find_element_by_xpath('//*[(@id = "l_aud")]//*[contains(concat( " ", @class, " " ), concat( " ", "fl_l", " " ))]')
    button2.click()
    sleep(randint(4,5))
    button3 = br.find_element_by_css_selector('div#content li._audio_section_tab__explore > a')
    button3.click()
    sleep(randint(4,5))
    button4 = br.find_element_by_css_selector('div#content div.CatalogBlock__recoms_top_audios_global_header.CatalogBlock__header > div > a')
    button4.click()
    sleep(randint(10,11))
    soup = BeautifulSoup(br.page_source)
    br.quit()
else:
    print("ERROR: please do manual login")


# In[ ]:


# работаем с html

songs = soup.findAll('span', attrs={'class':"audio_row__title_inner _audio_row__title_inner"})
artists = soup.findAll('div', attrs={'class':"audio_row__performers"})

songs_clean = [i.get_text() for i in songs]
artists_clean = [i.get_text() for i in artists]

data = {"rank": [i for i in range(1, 101)], "title": songs_clean, "artist":artists_clean}
vk_music_top_100_daily = pd.DataFrame(data)
# дата = предыдущий день (относительно дня скрейпинга)
date = currentDT - relativedelta(days=+1)
vk_music_top_100_daily["date"] = datetime.strftime(date,"%d/%m/%Y")  


# In[ ]:


# берем имеющийся csv файл и обновляем его

all_vk = pd.read_csv("all_vk.csv")
all_vk = all_vk.drop(all_vk.columns[[0]], axis=1) # удаляем получающуюся после импорта лишнюю колонку 
frames = [all_vk, vk_music_top_100_daily]
all_vk = pd.concat(frames, sort=False)
all_vk.to_csv("all_vk.csv", encoding = "utf-8")

