# Простейший телеграмм бот для напоминаний
В качестве БД использует SQLite.

Для настройки заполните в файле .py следующие строки:

```
TOKEN = '' #Токен TG
ADMIN_ID = ''#ID аккаунта администратора

#Пути к файлу БД в зависимости от операционной системы

if platform == "linux" or platform == "linux2":
    DB_PATH = ""
elif platform == "win32":
    DB_PATH = ""

```
