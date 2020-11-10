#!/usr/bin/env python
# coding: utf-8

# In[98]:


from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager
from selenium import webdriver


# In[102]:


options = Options()
options.add_argument('-headless')

profile = webdriver.FirefoxProfile()
profile.set_preference('intl.accept_languages', 'rus-RUS, ru')


br = webdriver.Firefox(executable_path=GeckoDriverManager().install(), firefox_profile=profile, options = options)
url='https://open.spotify.com/artist/3oLccEy7y6zTe1gCFHxuWr?si=6TlQnse-Q-qnnEmONgKWSg'
br.get(url)
soup = bs(br.page_source)
br.quit()

print('data-locale="ru"' in str(soup))

