import sqlite3
import threading
from sys import platform

import telebot
from datetime import datetime, timedelta
import time
import pytz

TOKEN = ''
ADMIN_ID = ''
bot = telebot.TeleBot(TOKEN)

moscow_tz = pytz.timezone('Europe/Moscow')

DB_PATH = ""

if platform == "linux" or platform == "linux2":
    DB_PATH = "/root/reminds-app/reminders.db"
elif platform == "win32":
    DB_PATH = "reminders.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        chat_id INTEGER NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS reminders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        message TEXT NOT NULL,
        reminder_date TEXT,
        reminder_time TEXT NOT NULL,
        repeat BOOLEAN NOT NULL DEFAULT 0,
        days_of_week TEXT DEFAULT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    ''')

    conn.commit()
    conn.close()

init_db()


def make_text_cute(text):
    return f'🌸 {text} 🌸'


@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE chat_id = ?', (chat_id,))
    user_exists = cursor.fetchone()

    if not user_exists:
        cursor.execute('INSERT INTO users (chat_id) VALUES (?)', (chat_id,))
        conn.commit()
        conn.close()
        bot.reply_to(message,
                     'Приветик, моё маленькое солнышко! ☀️ Я здесь, чтобы помочь тебе не забывать важные вещи ^^!\n'
                     'Используй команды:\n'
                     '/start -- чтобы увидеть это сообщение снова!\n'
                     '/напомни ГГГГ-ММ-ДД ЧЧ:ММ сообщение -- для единоразового напоминания\n'
                     '/ежедневное ЧЧ:ММ сообщение -- для установки ежедневных напоминаний\n'
                     '/неделя ПН,ВТ,СР ЧЧ:ММ сообщение -- для установки напоминаний по дням недели\n'
                     '/список -- для получения списка твоих напоминаний\n'
                     '/удали ид -- для удаления напоминания\n'
                     'Ето всё ( ⓛ ﻌ ⓛ *)')
    else:
        conn.close()
        bot.reply_to(message, 'Приветик снова~ Я рад видеть тебя! Если нужна помощь, просто скажи.\n'
                              'Используй команды:\n'
                                 '/start -- чтобы увидеть это сообщение снова!\n'
                                 '/напомни ГГГГ-ММ-ДД ЧЧ:ММ сообщение -- для единоразового напоминания\n'
                                 '/ежедневное ЧЧ:ММ сообщение -- для установки ежедневных напоминаний\n'
                                '/неделя ПН,ВТ,СР ЧЧ:ММ сообщение -- для установки напоминаний по дням недели\n'
                                 '/список -- для получения списка твоих напоминаний\n'
                                 '/удали ид -- для удаления напоминания\n'
                                 'Ето всё ( ⓛ ﻌ ⓛ *)')




@bot.message_handler(commands=['напомни'])
def set_reminder(message):
    chat_id = message.chat.id
    try:
        date_str, time_str, *reminder_text = message.text.split()[1:]
        message_text = ' '.join(reminder_text)
        reminder_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        reminder_time = datetime.strptime(time_str, '%H:%M').time()
        reminder_datetime = moscow_tz.localize(datetime.combine(reminder_date, reminder_time))

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE chat_id = ?', (chat_id,))
        user_id = cursor.fetchone()[0]

        cursor.execute('''
        INSERT INTO reminders (user_id, message, reminder_date, reminder_time, repeat)
        VALUES (?, ?, ?, ?, 0)
        ''', (user_id, message_text, reminder_datetime.strftime('%Y-%m-%d'), reminder_datetime.strftime('%H:%M')))
        conn.commit()
        conn.close()

        bot.reply_to(message, f'Напоминание установлено на {date_str} в {time_str} (московское время). Не забудь! ଘ(੭◉ω◉)つー☆')
    except (IndexError, ValueError):
        bot.reply_to(message, 'Использование: /напомни YYYY-MM-DD HH:MM сообщение (≧∇≦)')

@bot.message_handler(commands=['ежедневное'])
def set_daily_reminder(message):
    chat_id = message.chat.id
    try:
        time_str, *reminder_text = message.text.split()[1:]
        message_text = ' '.join(reminder_text)
        reminder_time = datetime.strptime(time_str, '%H:%M').time()
        reminder_datetime = moscow_tz.localize(datetime.combine(datetime.now().date(), reminder_time))

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE chat_id = ?', (chat_id,))
        user_id = cursor.fetchone()[0]

        cursor.execute('''
        INSERT INTO reminders (user_id, message, reminder_date, reminder_time, repeat)
        VALUES (?, ?, NULL, ?, 1)
        ''', (user_id, message_text, reminder_datetime.strftime('%H:%M')))
        conn.commit()
        conn.close()

        bot.reply_to(message, f'Ежедневное напоминание установлено на {time_str} (московское время). Каждый день буду напоминать! /ᐠ≽·ヮ·≼マ')
    except (IndexError, ValueError):
        bot.reply_to(message, 'Использование: /ежедневное HH:MM сообщение ૮₍ ˶ᵔ ᵕ ᵔ˶ ₎ა')

@bot.message_handler(commands=['неделя'])
def set_weekly_reminder(message):
    chat_id = message.chat.id
    try:
        days_str, time_str, *reminder_text = message.text.split()[1:]
        message_text = ' '.join(reminder_text)
        reminder_time = datetime.strptime(time_str, '%H:%M').time()
        reminder_datetime = moscow_tz.localize(datetime.combine(datetime.now().date(), reminder_time))
        days_of_week = days_str.split(',')

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE chat_id = ?', (chat_id,))
        user_id = cursor.fetchone()[0]

        cursor.execute('''
        INSERT INTO reminders (user_id, message, reminder_date, reminder_time, repeat, days_of_week)
        VALUES (?, ?, NULL, ?, 1, ?)
        ''', (user_id, message_text, reminder_datetime.strftime('%H:%M'), ','.join(days_of_week)))
        conn.commit()
        conn.close()

        bot.reply_to(message, f'Напоминание установлено на {", ".join(days_of_week)} в {time_str} (московское время). Буду напоминать в эти дни! /ᐠ≽·ヮ·≼マ')
    except (IndexError, ValueError):
        bot.reply_to(message, 'Использование: /неделя ПН,ВТ,СР HH:MM сообщение ૮₍ ˶ᵔ ᵕ ᵔ˶ ₎ა')

@bot.message_handler(commands=['список'])
def list_reminders(message):
    chat_id = message.chat.id
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM users WHERE chat_id = ?', (chat_id,))
    user_id = cursor.fetchone()[0]

    cursor.execute('''
    SELECT id, message, reminder_date, reminder_time, repeat, days_of_week
    FROM reminders 
    WHERE user_id = ?
    ORDER BY reminder_date, reminder_time
    ''', (user_id,))
    reminders = cursor.fetchall()
    conn.close()

    if reminders:
        reminder_list = '\n'.join(
            [f'{row[0]}: {row[1]} в {row[3]} на {row[2] if row[2] else ("каждый день" if row[4] else row[5])}' for row in reminders])
        bot.reply_to(message, f'Твои напоминания:\n{reminder_list} (づ๑•ᴗ•๑)づ♡')
    else:
        bot.reply_to(message, 'У тебя нет напоминаний. (ᵕ—ᴗ—)')

@bot.message_handler(commands=['удали'])
def delete_reminder(message):
    chat_id = message.chat.id
    try:
        reminder_id = int(message.text.split()[1])
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE chat_id = ?', (chat_id,))
        user_id = cursor.fetchone()[0]

        cursor.execute('DELETE FROM reminders WHERE id = ? AND user_id = ?', (reminder_id, user_id))
        if cursor.rowcount > 0:
            bot.reply_to(message, f'Напоминание {reminder_id} удалено. ૮ ˙Ⱉ˙ ა rawr!')
        else:
            bot.reply_to(message, f'Напоминание {reminder_id} не найдено. ଘ(˵╹-╹)━☆')

        conn.commit()
        conn.close()
    except (IndexError, ValueError):
        bot.reply_to(message, 'Использование: /удали id_напоминания')

@bot.message_handler(commands=['time'])
def admin_list_users(message):
    bot.reply_to(message, datetime.now().strftime("%H:%M:%S"))

@bot.message_handler(commands=['admin_l'])
def admin_list_users(message):
    if str(message.chat.id) == ADMIN_ID:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT chat_id FROM users')
        users = cursor.fetchall()
        conn.close()

        user_list = '\n'.join([str(user[0]) for user in users])
        bot.reply_to(message, f'Список пользователей:\n{user_list}')
    else:
        bot.reply_to(message, 'У вас нет прав для использования этой команды.')

@bot.message_handler(commands=['admin_r'])
def admin_list_reminders(message):
    if str(message.chat.id) == ADMIN_ID:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
        SELECT users.chat_id, reminders.id, reminders.message, reminders.reminder_date, reminders.reminder_time, reminders.repeat, reminders.days_of_week
        FROM reminders 
        JOIN users ON reminders.user_id = users.id 
        ORDER BY reminders.user_id, reminders.reminder_date, reminders.reminder_time
        ''')
        reminders = cursor.fetchall()
        conn.close()

        if reminders:
            reminder_list = '\n'.join(
                [f'User {row[0]}: {row[1]}: {row[2]} в {row[4]} на {row[3] if row[3] else ("каждый день" if row[5] else row[6])}' for row in reminders])
            bot.reply_to(message, f'Все напоминания:\n{reminder_list}')
        else:
            bot.reply_to(message, 'Нет напоминаний.')
    else:
        bot.reply_to(message, 'У вас нет прав для использования этой команды.')
def check_reminders():
    while True:
        now = datetime.now(moscow_tz)
        current_time = now.time().strftime('%H:%M')
        current_date = now.date().strftime('%Y-%m-%d')
        current_day_of_week = now.strftime('%a')

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
        SELECT users.chat_id, reminders.message, reminders.repeat, reminders.days_of_week 
        FROM reminders 
        JOIN users ON reminders.user_id = users.id 
        WHERE (reminder_date = ? OR repeat = 1 OR days_of_week LIKE ?) AND reminder_time = ?
        ''', (current_date, f'%{current_day_of_week}%', current_time))
        reminders = cursor.fetchall()

        for chat_id, message, repeat, days_of_week in reminders:
            bot.send_message(chat_id=chat_id, text=message)
            if not repeat and not days_of_week:
                cursor.execute(
                    'DELETE FROM reminders WHERE reminder_date = ? AND reminder_time = ? AND user_id = (SELECT id FROM users WHERE chat_id = ?)',
                    (current_date, current_time, chat_id))

        conn.commit()
        conn.close()

        now = datetime.now(moscow_tz)
        next_minute = (now + timedelta(minutes=1)).replace(second=0, microsecond=0)
        time_to_sleep = (next_minute - now).total_seconds()
        time.sleep(time_to_sleep)


if __name__ == '__main__':
    check_reminders_thread = threading.Thread(target=check_reminders)
    check_reminders_thread.start()
    bot.infinity_polling()
