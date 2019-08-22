import telebot
from telebot import apihelper
from time import sleep
import pytz
from datetime import datetime
import psycopg2


def todayActivity(user, day, cursor):
    cursor.execute("SELECT messages FROM activity WHERE day = %s AND username = %s;", (day, user))
    today = cursor.fetchall()
    if today == []:
        today = [(0,)]
    return today

def monthActivity(user, month, year, cursor):
    cursor.execute("SELECT SUM(messages) FROM activity WHERE username = %s AND date_part('month', day) = %s AND date_part('year', day) = %s;", (user, month, year))
    monthNum = cursor.fetchall()
    return monthNum

def activeDays(user, month, year, cursor):
    cursor.execute("SELECT COUNT(*) FROM activity WHERE username = %s  AND date_part('month', day) = %s AND date_part('year', day) = %s;", (user, month, year))
    active = cursor.fetchall()
    return active

def toDayLeader(day, cursor):
    cursor.execute("SELECT MAX(messages) FROM activity WHERE day = %s;", (day, ))
    max = cursor.fetchall()
    cursor.execute("SELECT username FROM activity WHERE day = %s AND messages = %s", (day, max[0][0]))
    leaders = cursor.fetchall()
    return leaders

def monthLeader(month, year, cursor):
    cursor.execute("select MAX(sum) from (select username, sum(messages) from activity WHERE date_part('month', day) = %s AND date_part('year', day) = %s GROUP BY username) AS x;", (month, year, ))
    max = cursor.fetchall()
    cursor.execute("select username from (select username, sum(messages) from activity WHERE date_part('month', day) = %s AND date_part('year', day) = %s  GROUP BY username) AS x WHERE sum = %s;", (month, year, max[0][0]))
    leaders = cursor.fetchall()
    return leaders

def numberLeader(month, year, cursor):
    cursor.execute("SELECT MAX(count) FROM (SELECT COUNT(username) FROM activity WHERE date_part('month', day) = %s AND date_part('year', day) = %s GROUP BY username) as x;", (month, year, ))
    max = cursor.fetchall()
    cursor.execute("SELECT username FROM (SELECT username, COUNT(username) FROM activity WHERE date_part('month', day) = %s AND date_part('year', day) = %s GROUP BY username) as x WHERE count = %s;", (month, year, max[0][0]))
    leaders = cursor.fetchall()
    return leaders

@bot.message_handler(commands=['help'])
def commandHelp(message):
    string = "How to use:\n/help@EnglishClubStatsbot - get help;\n" \
             "/day@EnglishClubStatsbot - get today's statistics;\n" \
             "/month@EnglishClubStatsbot - get monthly statistics."
    bot.send_message(message.chat.id, string)

@bot.message_handler(commands=['day'])
def commandDay(message):
    table = []
    conn = psycopg2.connect(dbname=dbName, user=dbUser, password=dbPass, host=dbAddr)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT username FROM activity;")
    users = list(map(lambda x: x[0], cursor.fetchall()))
    day = datetime.now(pytz.timezone('Europe/Moscow')).strftime('%Y-%m-%d')

    for user in users:
        info = {}
        today = todayActivity(user, day, cursor)[0][0]
        info['login'] = user;
        info['today'] = today
        table.append(info)

    string = "Today activity:\n"
    newTable = sorted(table, key=lambda k: k['today'], reverse=True)
    for item in newTable:
        if item['today'] > 0:
            string += f"{item['login']} - {item['today']}\n"

    bot.send_message(message.chat.id, string)
    cursor.close()
    conn.close()

@bot.message_handler(commands=['month'])
def commandMonth(message):
    table = []
    conn = psycopg2.connect(dbname=dbName, user=dbUser, password=dbPass, host=dbAddr)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT username FROM activity;")
    users = list(map(lambda x: x[0], cursor.fetchall()))
    day = datetime.now(pytz.timezone('Europe/Moscow')).strftime('%Y-%m-%d')
    month = datetime.now(pytz.timezone('Europe/Moscow')).strftime('%m')
    year = datetime.now(pytz.timezone('Europe/Moscow')).strftime('%Y')

    for user in users:
        info = {}
        today = todayActivity(user, day, cursor)[0][0]
        monthNum = monthActivity(user, month, year, cursor)[0][0]
        active = activeDays(user, month, year, cursor)[0][0]
        info['login'] = user
        info['today'] = today
        info['month'] = monthNum
        info['activeDays'] = active
        table.append(info)

    string = "<!DOCTYPE html>" \
             "<html lang='en'>" \
             "<head>" \
             "<meta charset='UTF-8'>" \
             "<title>Stats</title>" \
             "</head>" \
             "<body style='font-size: 30px;'>"

    string += f"<h4>Statistics on {datetime.now(pytz.timezone('Europe/Moscow')).strftime('%d-%m-%Y %H:%M')}</h4>" \
              f"<table style='width: 100%; border-collapse: collapse; '>" \
              f"<tr>" \
              f"<td style='border: 1px solid grey; padding: 10px;'>Username</td>" \
              f"<td style='border: 1px solid grey; padding: 10px;'>Today</td>" \
              f"<td style='border: 1px solid grey; padding: 10px;'>Month</td>" \
              f"<td style='border: 1px solid grey; padding: 10px;'>Days of activity</td>" \
              f"</tr>"

    for item in table:
        string += f"<tr>" \
                  f"<td style='border: 1px solid grey; padding: 10px;'>{item['login']}</td>" \
                  f"<td style='border: 1px solid grey; padding: 10px;'>{item['today']}</td>" \
                  f"<td style='border: 1px solid grey; padding: 10px;'>{item['month']}</td>" \
                  f"<td style='border: 1px solid grey; padding: 10px;'>{item['activeDays']}</td>" \
                  f"</tr>"

    string += "</table>" \
              "<h4>Today's leaders:</h4>"

    leadersToday = toDayLeader(day, cursor)
    for leader in leadersToday:
        string += f"<p>{leader[0]}</p>"

    string += "<h4>The largest number of posts for the current month:</h4>"

    leadersMonth = monthLeader(month, year, cursor)
    for leader in leadersMonth:
        string += f"<p>{leader[0]}</p>"

    string += "<h4>Most days of activity:</h4>"
    leadersNumber = numberLeader(month, year, cursor)
    for leader in leadersNumber:
        string += f"<p>{leader[0]}</p>"

    string += "</body></html>"

    cursor.close()
    conn.close()

    doc = open('statistics.html', 'w', encoding='utf-8')
    doc.write(string)
    doc.close()
    doc = open('statistics.html', 'r', encoding='utf-8')
    bot.send_document(message.chat.id, doc)
    doc.close()

@bot.message_handler(func=lambda message: True, content_types=['text','entities', 'caption_entities', 'audio', 'document', 'photo', 'sticker', 'video', 'video_note', 'voice', 'caption', 'contact', 'location', 'venue'])
def msgHandler(message):
    conn = psycopg2.connect(dbname=dbName, user=dbUser, password=dbPass, host=dbAddr)
    cursor = conn.cursor()
    username = ''
    d = message.json['from']
    day = datetime.now(pytz.timezone('Europe/Moscow')).strftime('%Y-%m-%d')

    if 'first_name' in d:
        username = username + d['first_name']
        if 'last_name' in d:
            username = username + " " + d['last_name']
    elif 'last_name' in d:
        username = username + d['last_name']
    else:
        username = username + d['username']

    cursor.execute("SELECT messages FROM activity WHERE username = %s AND day = %s;", (username, day,))
    records = cursor.fetchall()

    if records != []:
        cursor.execute("UPDATE activity SET messages = messages + 1 WHERE username = %s AND day = %s;",
                       (username, day,))
        conn.commit()
    else:
        cursor.execute("INSERT INTO activity VALUES (%s, %s, 1);", (username, day,))
        conn.commit()

    cursor.close()
    conn.close()


token = 'TELEGRAM_TOKEN'
proxy = 'socks5://IP_ADDRESS:PORT'
dbAddr = 'db.examle.com'
dbName = 'db_name'
dbUser = 'db_username'
dbPass = 'db_password'
apihelper.proxy = {'https': proxy}
bot = telebot.TeleBot(token)

while True:
    try:
        bot.polling()
    except:
        sleep(5)
