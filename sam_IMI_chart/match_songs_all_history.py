#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# Этот скрипт создает словарь соответствий между разными написаниями треков в разных сервисах

# Должен запускаться каждую неделю перед make_new_imi_chart.py


# In[ ]:


import pandas as pd
import datetime
from datetime import datetime, date, time, timezone
from dateutil.relativedelta import relativedelta
from os import path
import itertools
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import numpy as np
from transliterate import translit, get_available_language_codes
from unicodedata import normalize 
import json


# In[ ]:


# просто техническая функция для отображения изначальных имен объектов
def name_of_global_obj(xx):
    return [objname for objname, oid in globals().items()
            if id(oid)==id(xx)][0]

# форматирующие функции
def ch_yo(s):
    ss = "е".join(s.split("ё"))
    ss = "Е".join(ss.split("Ё"))
    return ss

def ch_n(s):
    ss = str(s)
    ss = "n***a".join(ss.lower().split("nigga"))
    return ss

def commas_no_ands(s):
    ss = ", ".join([i.rstrip().lstrip() for i in s.split("&")])
    ss = normalize("NFKC", ss)
    ss = ch_yo(ch_n(nsbr(ss)))
    return ss

def commas_no_ands_ser(ser):
    ss = pd.Series([ch_yo(ch_n(nsbr(normalize("NFKC", ", ".join([i.rstrip().lstrip() for i in s.split("&")]))))) for s in list(ser)], dtype="object")
    return ss

def f_feat(s):
    ss = ", ".join([i.rstrip().lstrip() for i in s.split("feat.")])
    return ss

def f_prod(s):
    ss = ", ".join([i.rstrip().lstrip() for i in s.split("prod.")])
    return ss

def f_Prod(s):
    ss = ", ".join([i.rstrip().lstrip() for i in s.split("Prod.")])
    return ss

def nsbr(s):
    ss = "(".join(s.split("["))
    ss = ")".join(ss.split("]"))
    
    return ss

def norm(s):
    ss = nsbr(ch_n(ch_yo(normalize("NFKC", s).lower())))
    return ss

def full_norm(s):
    ss = nsbr(f_feat(commas_no_ands(ch_n(ch_yo(s)))))
    ss = ss.lower()
    return ss


# In[3]:


def clean_keys(D):
    # чистим опустевшие ключи
    for i in list(D.keys()):
        if D[i] is None:
            D.pop(i, None)


# In[4]:


if path.exists("tracks_dict.json"):
    with open("tracks_dict.json", "r") as outfile:  
        d_basic = json.load(outfile)
        outfile.close()
else:
    d_basic = dict()
    
if path.exists("weeksin_tracks_dict.json"):
    with open("weeksin_tracks_dict.json", "r") as outfile:  
        weeksin_d_basic = json.load(outfile)["weeks"]
        outfile.close()
else:
    weeksin_d_basic = []


# In[5]:


# import all weekly charts
platforms = ["vk", "deezer", "apple", "yandex", "sber"]
d = {name: pd.read_csv("all_"+name+"_weekly.csv") for name in platforms}
d["spotify"] = pd.read_csv("all_spotify.csv")


# In[6]:


all_charts_glued = pd.DataFrame()

for i in d.items():
    i[1]["platform"] = i[0]
    all_charts_glued = all_charts_glued.append(i[1])


# In[7]:


all_charts_glued = all_charts_glued[["title", "artist", "platform", "week"]]


# In[8]:


all_charts_glued.reset_index(inplace=True, drop = True)


# In[9]:


# filter out weeks that are in d_basic
for i in weeksin_d_basic:
    all_charts_glued.drop(all_charts_glued[all_charts_glued["week"] == i].index, inplace=True)


# In[10]:


# записываем, какие новые недели войдут в апдейт словаря
new_weeks = list(set(list(all_charts_glued["week"])))


# In[ ]:





# In[12]:


all_charts_glued = all_charts_glued[["title", "artist", "platform"]]


# In[13]:


all_charts_glued["title"] = all_charts_glued["title"].astype(str)
all_charts_glued["artist"] = all_charts_glued["artist"].astype(str)


# In[ ]:


# 2.1 боремся с feat. в названиях треков
def step21(D):
    d1 = D
    d2 = d1.copy()

    for i in d1.items():
        t = i[0].split("#bh#")[0]
        for b_word in ["with", "With", "feat.", "Feat.", "- prod. by", "- Prod. by", "prod. by", "Prod. by", "- prod.", "- Prod.", "prod.", "Prod."]:
            if b_word in t:
                nf = t.split(b_word)[0]
                nf = nf.split("(")[0].split("[")[0]
                nf = nf.strip()
                print("WORK ON ", i[0])
                # (чтобы не искать среди списка, включающего сам элемент )
                d_c = d1.copy()
                key_old = i[0]
                d_c.pop(key_old, None)
                for k in d_c.items():

                    # раз совпадают названия, в которых есть feat. (или подобные слова из списка), нет причин не мэтчить
                    if norm(t) == norm(k[0].split("#bh#")[0]):
                            print("\ntitles match and include ", b_word, " matching.")
                            print(i[0])
                            print(k[0], "\n")
                            # соединяем таблицы в словаре
                            d2[k[0]] = pd.concat([d2[k[0]], pd.concat([k[1],i[1]])])
                            # удаляем старый ключ в словаре
                            #d2.pop(i[0], None)
                            d2[i[0]] = None

                    # мэтчим с названиями без feat. (и подобных слов из списка) (если есть)
                    elif norm(nf) == norm(k[0].split("#bh#")[0]): 
                        # создаем имена артиста.
                        if b_word in ["with", "With", "feat.", "Feat."]:
                            # искусственно создаем название артиста 
                            a_a = t.split(b_word)[1].split(")")[0].rstrip().lstrip() # featured artist
                            a_a_a = i[0].split("#bh#")[1]+", "+a_a #initial artists + featured artist 
                        else:
                            # когда в названии prod., не ожидаем продюсера в артистах 
                            a_a_a = i[0].split("#bh#")[1] #will just compare initial artists

                        if b_word in ["with", "With", "feat.", "Feat."]:
                            print(a_a)
                            # сначала пробуем найти артиста из названия в артистах другого трека
                            if commas_no_ands(ch_yo(a_a)) in commas_no_ands(ch_yo(k[0].split("#bh#")[1])):
                                print("\nfeat. artist is in the other track's artist's string. matching.")
                                print(k[0].split("#bh#")[1])
                                print(a_a, "\n")
                                # соединяем таблицы в словаре
                                d2[k[0]] = pd.concat([d2[k[0]], pd.concat([k[1],i[1]])])
                                # удаляем старый ключ в словаре
                                #d2.pop(i[0], None)
                                d2[i[0]] = None

                            elif fuzz.partial_token_sort_ratio(ch_yo(a_a_a), ch_yo(k[0].split("#bh#")[1])) > 80:
                                print("artists are close! matching.")
                                print(k[0].split("#bh#")[1])
                                print(a_a_a, "\n")
                                # соединяем таблицы в словаре
                                d2[k[0]] = pd.concat([d2[k[0]], pd.concat([k[1],i[1]])])
                                # удаляем старый ключ в словаре
                                #d2.pop(i[0], None)
                                d2[i[0]] = None

                            else:
                                print("artists are too different:")
                                print(k[0].split("#bh#")[1])
                                print(a_a_a, "\n")

                        elif fuzz.partial_token_sort_ratio(ch_yo(a_a_a), ch_yo(k[0].split("#bh#")[1])) > 80:
                            print("\nartists are close! matching.")
                            print(k[0].split("#bh#")[1])
                            print(a_a_a, "\n")
                            # соединяем таблицы в словаре
                            d2[k[0]] = pd.concat([d2[k[0]], pd.concat([k[1],i[1]])])
                            #print(d2[k[0]])
                            # удаляем старый ключ в словаре
                            #d2.pop(i[0], None)
                            d2[i[0]] = None
                        else:
                            print("artists are too different:")
                            print(k[0].split("#bh#")[1])
                            print(a_a_a, "\n")
                break
                print()

    return d2
    # ИТОГ: остались только ключи, у которых не было feat. в названии + те, у которых он есть, но нет аналогов


# In[ ]:


# 2.1 боремся с feat. в названиях треков
# d_old = old data (from d_basic)
# d_new = new data
def step21_full(d_old, d_new):
    for i in d_new.items():
        t = i[0].split("#bh#")[0]
        for b_word in ["with", "With", "feat.", "Feat.", "- prod. by", "- Prod. by", "prod. by", "Prod. by", "- prod.", "- Prod.", "prod.", "Prod."]:
            if b_word in t:
                nf = t.split(b_word)[0]
                nf = nf.split("(")[0].split("[")[0]
                nf = nf.strip()
                print("WORK ON ", i[0])
                # (чтобы не искать среди списка, включающего сам элемент )
                #d_c = d1.copy()
                #key_old = i[0]
                #d_c.pop(key_old, None) #  
                for k in d_old.items():
                    # раз совпадают названия, в которых есть feat. (или подобные слова из списка), нет причин не мэтчить
                    if norm(t) == norm(k[0].split("#bh#")[0]):
                            print("\ntitles match and include ", b_word, " matching.")
                            print(i[0])
                            print(k[0], "\n")
                            # соединяем таблицы в словаре
                            d_old[k[0]] = pd.concat([d_old[k[0]], i[1]])
                            # обнуляем ключ в новых данных
                            d_new[i[0]] = None

                    # мэтчим с названиями без feat. (и подобных слов из списка) (если есть)
                    elif norm(nf) == norm(k[0].split("#bh#")[0]): 
                        # создаем имена артиста.
                        if b_word in ["with", "With", "feat.", "Feat."]:
                            # искусственно создаем название артиста 
                            a_a = t.split(b_word)[1].split(")")[0].rstrip().lstrip() # featured artist
                            a_a_a = i[0].split("#bh#")[1]+", "+a_a #initial artists + featured artist 
                        else:
                            # когда в названии prod., не ожидаем продюсера в артистах 
                            a_a_a = i[0].split("#bh#")[1] #will just compare initial artists

                        if b_word in ["with", "With", "feat.", "Feat."]:
                            print(a_a)
                            # сначала пробуем найти артиста из названия в артистах другого трека
                            if commas_no_ands(ch_yo(a_a)) in commas_no_ands(ch_yo(k[0].split("#bh#")[1])):
                                print("\nfeat. artist is in the other track's artist's string. matching.")
                                print(k[0].split("#bh#")[1])
                                print(a_a, "\n")
                                # соединяем таблицы в словаре
                                d_old[k[0]] = pd.concat([d_old[k[0]], i[1]])
                                # обнуляем ключ в новых данных
                                d_new[i[0]] = None

                                
                            elif fuzz.partial_token_sort_ratio(ch_yo(a_a_a), ch_yo(k[0].split("#bh#")[1])) > 80:
                                print("\nartists are close! matching.")
                                print(k[0].split("#bh#")[1])
                                print(a_a_a, "\n")
                                # соединяем таблицы в словаре
                                d_old[k[0]] = pd.concat([d_old[k[0]], i[1]])
                                # обнуляем ключ в новых данных
                                d_new[i[0]] = None

                            else:
                                print("\nartists are too different:")
                                print(k[0].split("#bh#")[1])
                                print(a_a_a, "\n")

                        elif fuzz.partial_token_sort_ratio(ch_yo(a_a_a), ch_yo(k[0].split("#bh#")[1])) > 80:
                            print("\nartists are close! matching.")
                            print(k[0].split("#bh#")[1])
                            print(a_a_a, "\n")
                            # соединяем таблицы в словаре
                            d_old[k[0]] = pd.concat([d_old[k[0]], i[1]])
                            # обнуляем ключ в новых данных
                            d_new[i[0]] = None
                        else:
                            print("\nartists are too different:")
                            print(k[0].split("#bh#")[1])
                            print(a_a_a, "\n")
                break
                print()

    return (d_old, d_new)
    # ИТОГ: остались только ключи, у которых не было feat. в названии + те, у которых он есть, но нет аналогов


# In[ ]:


# 2.2 боремся с feat. в названиях артистов (когда в названии песни feat. нету!) 
# и прочими стандартными вещами -  &, запятыми и е/ё
def step22(D):
    d2 = D
    d22 = d2.copy()

    for i in d2.items():
        a = i[0].split("#bh#")[1]
        t = i[0].split("#bh#")[0]
        if "feat." in a:
            print("Working on ", i[0] )
            d_c = d2.copy()
            key_old = i[0]
            d_c.pop(key_old, None)
            for k in d_c.items():
                if norm(t) == norm(k[0].split("#bh#")[0]): # проверяем, что название совпадает
                    a_a = full_norm(a)
                    if  fuzz.partial_token_sort_ratio(full_norm(k[0].split("#bh#")[1]), a_a) > 80:
                        print("\nsame artists. matching.")
                        print(a)
                        print(k[0].split("#bh#")[1], "\n")
                        d22[k[0]] = pd.concat([d22[k[0]], pd.concat([k[1],i[1]])])
                        # удаляем старый ключ в словаре
                        #d22.pop(i[0], None)
                        d22[i[0]] = None
                    else:
                        print("\nartists are too different")
                        print(a)
                        print(k[0].split("#bh#")[1], "\n")
            print()
    return d22
                
# ИТОГ: остались только ключи, у которых не было feat. ни в названии, НИ в артистах + те, у которых это есть, но нет аналогов


# In[ ]:


# 2.2 боремся с feat. в названиях артистов (когда в названии песни feat. нету!) 
# и прочими стандартными вещами -  &, запятыми и е/ё
def step22_full(d_old, d_new):

    for i in d_new.items():
        a = i[0].split("#bh#")[1]
        t = i[0].split("#bh#")[0]
        if "feat." in a:
            print("Working on ", i[0] )
            #d_c = d2.copy()
            #key_old = i[0]
            #d_c.pop(key_old, None)
            for k in d_old.items():
                if norm(t) == norm(k[0].split("#bh#")[0]): # проверяем, что название совпадает
                    a_a = full_norm(a)
                    if  fuzz.partial_token_sort_ratio(full_norm(k[0].split("#bh#")[1]), a_a) > 80:
                        print("\nsame artists. matching.")
                        print(a)
                        print(k[0].split("#bh#")[1], "\n")
                        d_old[k[0]] = pd.concat([d_old[k[0]], i[1]])
                        # обнуляем ключ в новых данных
                        d_new[i[0]] = None
                        
                    else:
                        print("\nartists are too different")
                        print(a)
                        print(k[0].split("#bh#")[1], "\n")

            print()
    return (d_old, d_new)


# In[ ]:


# 3. мэтчим песни с одинаковыми названиями, но отличающимися написаниями артистов 
# Капс и прочее (скобки, слэши, запятые, начало слов с заглавной/строчной буквы)
def step3(D):
    d22 = D
    d3 = D.copy()


    for i in d22.items():
        a = i[0].split("#bh#")[1]
        t = i[0].split("#bh#")[0]

        d_c = d22.copy()
        key_old = i[0]
        d_c.pop(key_old, None)

        for k in d_c.items():
            if fuzz.token_sort_ratio(k[0].split("#bh#")[0], t) == 100:
                print()
                print(t)
                print(k[0].split("#bh#")[0])
                # сравниваем артистов
                if fuzz.token_sort_ratio(full_norm(a), full_norm(k[0].split("#bh#")[1]))>80:
                    d3[k[0]] = pd.concat([d3[k[0]], pd.concat([k[1],i[1]])])
                    d3[i[0]] =  None
                    print("\nartists are close! matching these together")
                    print(k[0].split("#bh#")[1])
                    print(a, "\n")
                elif fuzz.partial_token_sort_ratio(translit(full_norm(a), "ru"), translit(full_norm(k[0].split("#bh#")[1]), "ru"))>80:
                    d3[k[0]] = pd.concat([d3[k[0]], pd.concat([k[1],i[1]])])
                    d3[i[0]] =  None
                    print("\nartists are close! matching these together")
                    print(k[0].split("#bh#")[1])
                    print(a, "\n")
                else:
                    print("\nartists are too different:")
                    print(i[0])
                    print(k[0].split("#bh#")[1])
                    print(a, "\n")
    return d3


# In[ ]:


# 3. мэтчим песни с одинаковыми названиями, но отличающимися написаниями артистов 
# Капс и прочее (скобки, слэши, запятые, начало слов с заглавной/строчной буквы)
def step3_full(d_old, d_new):
    for i in d_new.items():
        a = i[0].split("#bh#")[1]
        t = i[0].split("#bh#")[0]
        #d_c = d22.copy()
        #key_old = i[0]
        #d_c.pop(key_old, None)
        for k in d_old.items():
            if fuzz.token_sort_ratio(k[0].split("#bh#")[0], t) == 100:
                print(t)
                print(k[0].split("#bh#")[0])
                # сравниваем артистов
                if fuzz.token_sort_ratio(full_norm(a), full_norm(k[0].split("#bh#")[1]))>80:
                    d_old[k[0]] = pd.concat([d_old[k[0]], i[1]])
                    # обнуляем ключ в новых данных
                    d_new[i[0]] = None
                    print("\nartists are close! matching these together")
                    print(k[0].split("#bh#")[1])
                    print(a, "\n")
                elif fuzz.partial_token_sort_ratio(translit(full_norm(a), "ru"), translit(full_norm(k[0].split("#bh#")[1]), "ru"))>80:
                    d_old[k[0]] = pd.concat([d_old[k[0]], i[1]])
                    # обнуляем ключ в новых данных
                    d_new[i[0]] = None
                    print("\nartists are close! matching these together")
                    print(k[0].split("#bh#")[1])
                    print(a, "\n")
                else:
                    print("\nartists are too different:")
                    print(i[0])
                    print(k[0].split("#bh#")[1])
                    print(a, "\n")
    return (d_old, d_new)


# In[ ]:


# ! convert values to pandas df before using this
# note that this clears keys in d2! (if they are matched)
def simple_match(d1,d2):
    for i in d1.keys():
        for j in d2.keys():
            if i == j:
                d1[i] = pd.concat([d1[i], d2[j]])
                d2[j] = None
    return d1


# In[ ]:


if len(all_charts_glued)>0:
    
    #### 0. группируем (в НОВЫХ данных) те песни, у кого идентичные артисты и названия (но в lowercase)
    d_new_only = {}
    all_charts_glued.reset_index(inplace = True, drop = True)
    all_charts_glued["full_id"] = all_charts_glued["title"] +"#bh#" + all_charts_glued["artist"]
    L = list(set(all_charts_glued["full_id"]))
    for i in L:
        one_id_df = all_charts_glued[commas_no_ands_ser(all_charts_glued["full_id"].str.lower()) == commas_no_ands(i.lower())]
        print(len(one_id_df), i)
        all_charts_glued = all_charts_glued.drop(all_charts_glued[commas_no_ands_ser(all_charts_glued["full_id"].str.lower()) == commas_no_ands(i.lower())].index)
        all_charts_glued.reset_index(inplace = True, drop = True)
        # ключи = full_id
        if len(one_id_df)>0:
            d_new_only[i]=one_id_df    
    
    #### 1.1. запускаем цикл на "сходимость" в НОВЫХ данных
    d_nnn = d_new_only.copy()

    while True:
        d_n = step21(d_nnn)
        clean_keys(d_n)
        d_nn = step22(d_n)
        clean_keys(d_nn)
        d_nnn = step3(d_nn)
        clean_keys(d_nnn)
        if len(d_nnn.keys()) == len(d_n.keys()):
            break
        else:
            print(len(d_nnn.keys()))
            
    ################1.2. Ask the editor about the uncertain cases            ###################
    ############################################################################################
    ############ MAKE THEM DIFFERENT FOREVER OR THE EDITOR WILL FREAK OUT ######################
    ############################################################################################
    d_nnn_c = d_nnn.copy()

    l_of_asked =[]

    for i in d_nnn_c.keys():
        d_c = d_nnn_c.copy()
        d_c.pop(i, None)
        for j in d_c.keys():
            if sorted([i, j]) in l_of_asked:
                pass
            else:
                if fuzz.ratio(i, j)>88:
                    print("\nitem 1: ", i)
                    print("item 2: ", j, "\n")
                    decision = input("Это один и тот же трек? (Y/N) ", )
                    if decision == "Y":
                        # внимание: здесь работаем не с копией, а с самим d_nnn
                        if len(str(i)) >= len(str(j)):
                            d_nnn[i] = pd.concat([d_nnn[i], d_nnn[j]])
                            d_nnn[j] = None
                        else:
                            d_nnn[j] = pd.concat([d_nnn[j], d_nnn[i]])
                            d_nnn[i] = None
                        clean_keys(d_nnn)
                    l_of_asked.append(sorted([i,j]))
                    
    # чистим от дубликатов и задаем свежий индекс
    for i in list(d_nnn.keys()):        
        d_nnn[i] = d_nnn[i].drop_duplicates()
        d_nnn[i].reset_index(drop="True", inplace = True)
        
                    
    #### 2.1. Запускаем цикл сходимости между новыми данными и старыми
    # сначала конвертируем старые данные в таблицы pandas
    for i in d_basic.keys():
        d_basic[i] = pd.DataFrame.from_dict(d_basic[i])
    # 2.1.1 мэтчим по full_ID
    d_basic = simple_match(d_basic, d_nnn)
    clean_keys(d_nnn)
    
    # 2.1.2 
    # какие-то full ID не равны. мэтчим по-другому.
    # запускаем те же три скрипта (но модифицированные) снова 
    while True:
        d_nnn_start = d_nnn.copy()
        (d_basic, d_nnn) = step21_full(d_basic, d_nnn)
        clean_keys(d_nnn)
        (d_basic, d_nnn) = step22_full(d_basic, d_nnn)
        clean_keys(d_nnn)
        (d_basic, d_nnn) = step3_full(d_basic, d_nnn)
        clean_keys(d_nnn)
        if len(d_nnn.keys()) == len(d_nnn_start.keys()):
            break
        else:
            print(len(d_nnn.keys()))
            
    #### 2.2 Ask the editor about the uncertain cases          
    l_of_asked =[]
    for i in d_nnn.keys():
        for j in d_basic.keys():
            if sorted([i, j]) in l_of_asked:
                pass
            else:
                if fuzz.ratio(i, j)>88:
                    print("\nitem 1: ", i)
                    print("item 2: ", j, "\n")
                    decision = input("Это один и тот же трек? (Y/N) ", )
                    if decision == "Y":
                        d_basic[j] = pd.concat([d_basic[j], d_nnn[i]])
                        d_nnn[j] = None
                    l_of_asked.append(sorted([i,j]))
    clean_keys(d_nnn)
    
    ### 2.3.присоединяем то, что не замэтчилось
    for i in d_nnn.keys():
        if i in list(d_basic.keys()):
            print("ERROR. matching went wrong. there are still same keys in new and old data.")
        else:
            # create new keys 
            d_basic[i] = d_nnn[i]
            
    
    d_final = {}
    #### 3. чистим от дубликатов и чистим индекс
    for i in list(d_basic.keys()):        
        d_final[i] = d_basic[i].drop_duplicates()
        d_final[i].reset_index(drop="True", inplace = True)
        
    #### 4. Ставим наиболее полное имя в качестве имени каждого подсловаря
    #for i in list(d_final.keys()):

    #### 5. конвертируем все таблицы в словари - для экспорта
    for i in d_final.keys():
        d_final[i] = d_final[i].to_dict()

    #### 6. Export
    weeksin_d_basic.extend(new_weeks)

    with open("tracks_dict.json", "w") as outfile:  
        json.dump(d_final, outfile) 
    print(datetime.now(), " Exported updated tracks_dict.json")

    outfile.close()

    with open("weeksin_tracks_dict.json", "w") as outfile:  
        json.dump({"weeks": weeksin_d_basic}, outfile) 
    print(datetime.now(), " Exported updated weeksin_tracks_dict.json")
    
else:
    print(datetime.now(), " no new weeks in data")

