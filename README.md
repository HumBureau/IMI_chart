# Общая информация -- папки

Дерево всего проекта:
1. Daily
  - Содержит скрипты и данные по всему, что связано с Apple Music, Deezer, VK, Яндекс.Музыкой
  - Содержит скрипт для парсинга ежедневного чарта Spotify (нужно для "технических" целей)
2. Spotify_parsing
  - То же для Spotify
3. Youtube_parsing
  - Содержит скрипт для парсинга и составление недельного чарта Youtube, а также базу всех сохраненных данных

------------

# 1. Папка Daily: подробнее

В данной папке есть файлы следующих типов:
1. all_название стриминга.csv - это базы данных, куда сохраняется вся история парсингов ежедневных чартов
2. all_название стриминга_weekly.csv - это базы данных, куда сохраняются все рассчитанные нашими алгоритмами недельные чарты
3. current_название стриминга_json.json - это json, в котором лежит актуальная версия недельного чарта
4. current_название стриминга_html.html - то же самое, но в html и с красивыми русскими названиями колонок

------------

A так же скрипты:
1. Daily_parsing
- должен запускаться каждый день один раз в сутки в 11:30 утра
- осуществляет парсинг ежедневных чартов
-- через requests: Apple Music
-- через selenium: VK (нужны системные зависимости — пакет `geckodriver 0.27.0` и браузер Firefox 81.0)

2. Yandex_intra_day_parsing
- парсит чарт яндекса весь день с периодичностью в полчаса
- должен запускаться каждый день в 00:30
- работает круглые сутки до полуночи

3. Deezer_daily_parsing
- запускается в самом начале суток и каждые 20 минут парсит актуальный чат Deezer
- останавливается тогда, когда находит новый чарт

4. Spotify_daily_parsing
- парсит ежедневный чарт Спотифая
- запускать в 15:40 по Мск

4. Make_weekly_charts
- выдает еженедельные чарты стримингов, усредняя ежедневные чарты за 7 дней
-- стриминги: Apple Music, VK, Deezer, Yandex
- должен запускаться один раз в неделю утром пятницы после Daily_parsing и Spotify_parsing (т.e. в районе 11:40)
 -- размещен в этой папке просто из-за удобства, а не потому, что надо запускать каждый день!

-на выходе:
- обновляет csv файлы с соответствующими еженедельными чартами 4-x стримингов
-- all_vk_weekly.csv, и т.д.
- сохраняет html файлы с актуальными недельными чартами
-- current_vk_html.html и т.д.
- сохраняет json файлы с актуальными недельными чартами
-- current_vk_json.json и т.д.


# 2. Папка Spotify_weekly: подробнее

Скрипт: Spotify_parsing
- парсит еженедельный чарт Spotify Top 200 Russia
- время запуска: утро пятницы
- период чарта: пятница-четверг

- на выходе:
-- обновляет уже хранящиеся данные прошлых недель в csv
-- сохраняет html файл актуального чарта для демонстрации на сайте
-- сохраняет json актуального чарта

# 3. Папка Youtube_weekly: подробнее

То же, что со Spotify_weekly, но
- время запуска: утро воскресенья
- хотя период чарта: пятница-четверг
-- чарт Ютуба задерживается, поэтому так.

-- -- внимание: парсится именно чарт Top Tracks, т.к. он уже включает в себя Top Music Videos (см. подробнее https://support.google.com/youtube/answer/9014376?hl=en)

-----------

# Полный цикл работы скриптов еще раз:

Каждые сутки с 00:30 до 23:59 (выключается сам):
- Yandex_intra_day_parsing
- Deezer_daily_parsing

Каждый день в 11:30:
- Daily_parsing

Каждый день в 15:40:
- Spotify_daily_parsing

Каждое утро пятницы, после 11:30:
- Make_weekly_charts
- Spotify_parsing

Каждое утро воскрeсенья:
- Youtube_parsing

------------

# Scripts

- run ``git rm --cached `git ls-files -i -X .gitignore`` to exclude ignored files from repository
