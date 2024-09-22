import telebot
from telebot import types
from datetime import datetime, timedelta
import pandas as pd
from io import BytesIO
import pytz
import re
import signal
import sys
import os

bot = telebot.TeleBot('7052131672:AAHEs6hOG_27apuoHFVyq81CdfXPn_Yx_WI')
ADMIN_ID = 818757464
current_route = None
# Local
file_path_schedule = r'C:\Users\serge\Oleksii\university\bots\bus_schedule\schedules.xlsx'
file_path_photo_941= r'C:\Users\serge\Oleksii\university\bots\bus_schedule\941_photo.jpg'
# pythonanywhere
# file_path_schedule = '/home/OleksiiLeheza12/bot/schedules.xlsx'
# file_path_photo_941= '/home/OleksiiLeheza12/bot/941_photo.jpg'

bus_schedule_941 = [
]

bus_schedule_324 = [
]

bus_schedule_324_weekend = [
]
statistics_file = "client_statistics.txt"

class BusInfo:
    def __init__(self, text):
        match = re.match(r'(\d{1,2}:\d{2})\s*\((.*?)\)', text)
        if match:
            time_str, self.description = match.groups()
        else:
            time_str = re.match(r'(\d{1,2}:\d{2})', text).group(1)
            self.description = ""

        self.time = datetime.strptime(time_str, "%H:%M").time()

    def __lt__(self, other):
        return self.time < other.time

    def __str__(self):
        if self.description:
            return f"{self.time.strftime('%H:%M')} ({self.description})"
        return f"{self.time.strftime('%H:%M')}"

def initialize_schedules():
    global bus_schedule_941, bus_schedule_324, bus_schedule_324_weekend
    try:
        df = pd.read_excel(file_path_schedule, sheet_name=None)

        bus_schedule_941_df = df['941']
        bus_schedule_324_df = df['324_weekday']
        bus_schedule_324_weekend_df = df['324_weekend']

        bus_schedule_941 = [clean_row(row) for row in bus_schedule_941_df.values.tolist()]
        bus_schedule_324 = [clean_row(row) for row in bus_schedule_324_df.values.tolist()]
        bus_schedule_324_weekend = [clean_row(row) for row in bus_schedule_324_weekend_df.values.tolist()]

        print("Schedules initialized successfully.")
    except Exception as e:
        print(f"Error initializing schedules: {e}")

def clean_row(row):
    return [value if not pd.isna(value) else '' for value in row]

@bot.message_handler(commands=['change_schedule'])
def change_schedule(chat):
    try:
        if chat.from_user.id == ADMIN_ID:
            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            btn_941 = types.KeyboardButton('941 all')
            btn_324_weekday = types.KeyboardButton('324 weekday')
            btn_324_weekend = types.KeyboardButton('324 weekend')
            markup.add(btn_941, btn_324_weekday, btn_324_weekend)
            bot.send_message(chat.chat.id, "Оберіть маршрут, для якого бажаєте змінити розклад:", reply_markup=markup)
        else:
            bot.send_message(chat.chat.id, "У вас немає доступу до цієї команди.")
    except Exception as e:
        bot.send_message(chat.chat.id, f"Помилка при оновлені даних: {e}")

@bot.message_handler(func=lambda message: message.text in ['941 all', '324 weekday', '324 weekend'])
def route_selected(chat):
    try:
        if chat.from_user.id == ADMIN_ID:
            global current_route
            current_route = chat.text
            bot.send_message(chat.chat.id, f"Ви обрали {current_route}. Тепер завантажте Excel файл з розкладом.")
        else:
            bot.send_message(chat.chat.id, "У вас немає доступу до цієї команди.")
    except Exception as e:
        bot.send_message(chat.chat.id, f"Помилка при оновлені даних: {e}")

@bot.message_handler(content_types=['document'])
def handle_document(chat):
    try:
        global current_route
        if chat.from_user.id == ADMIN_ID and current_route:
            document_id = chat.document.file_id
            file_info = bot.get_file(document_id)
            file = bot.download_file(file_info.file_path)
            df = pd.read_excel(BytesIO(file))

            try:
                update_schedule(df, current_route)
                bot.send_message(chat.chat.id, f"Розклад для {current_route} успішно оновлено.")
            except Exception as e:
                bot.send_message(chat.chat.id, f"Помилка при оновлені даних: {e}")

            current_route = None
        else:
            bot.send_message(chat.chat.id, "У вас немає доступу до цієї команди або маршрут не обрано.")
    except Exception as e:
        bot.send_message(chat.chat.id, f"Помилка при оновлені даних при роботі з документами: {e}")

def update_schedule(df, route):
    def clean_row(row):
        return [value if not pd.isna(value) else '' for value in row]

    if route == '941 all':
        global bus_schedule_941
        bus_schedule_941 = [clean_row(row) for row in df.values.tolist()]
    elif route == '324 weekday':
        global bus_schedule_324
        bus_schedule_324 = [clean_row(row) for row in df.values.tolist()]
    elif route == '324 weekend':
        global bus_schedule_324_weekend
        bus_schedule_324_weekend = [clean_row(row) for row in df.values.tolist()]

@bot.message_handler(commands=['start'])
def start(chat):
    try:
        bot.send_message(chat.chat.id, 'Бот розпочав роботу. Доступні функції перегляду розкладу автобусів')
    except Exception as e:
        bot.send_message(chat.chat.id, f"Помилка: {e}")

@bot.message_handler(commands=['bus_941'])
def bus_941_schedule(chat):
    try:
        username = chat.from_user.username or "No Username"
        log_request(chat.from_user.id, username, 'bus_941')
        header_941 = f"---------------<b>941</b>---------------\n{'<b>З Воронькову</b>':<30} {'<b>З Києва</b>':<12}"
        col_width = max(len(item) for sublist in bus_schedule_941 for item in sublist) + 2
        formatted_schedule = [f"{header_941:<{col_width +29}}"]
        for row in zip(*bus_schedule_941):
            if not row[0].strip():
                formatted_schedule.append(f"{' ' * (col_width+18)}{row[1]:<{col_width}}")
            else:
                if len(row[0]) == col_width-2:
                    formatted_schedule.append(f"{row[0]:<{col_width+1}}{row[1]:<{col_width}}")
                else:
                    formatted_schedule.append(f"{row[0]:<{col_width+13}}{row[1]:<{col_width}}")
        formatted_schedule_941_res = "\n".join(formatted_schedule)
        bot.send_message(chat.chat.id, f"{formatted_schedule_941_res}", parse_mode='HTML')
    except Exception as e:
        bot.send_message(chat.chat.id, f"Помилка при виконанні запиту до розкладу автобусу 941: {e}")


@bot.message_handler(commands=['bus_324'])
def bus_324_schedule(chat):
    try:
        username = chat.from_user.username or "No Username"
        log_request(chat.from_user.id, username, 'bus_324')
        today = datetime.today().weekday()
        if today in [5, 6]:  # Weekend
            schedule = bus_schedule_324_weekend
            header = f"------<b>324(Вихідні)</b>------\n{'<b>З Процеву</b>':<{16}} {'<b>З Києва</b>':<{12}}"
        else:  # Weekday
            schedule = bus_schedule_324
            header = f"----------<b>324</b>----------\n{'<b>З Процеву</b>':<{16}} {'<b>З Києва</b>':<{12}}"

        col_width = max(len(item) for sublist in schedule for item in sublist) + 2
        formatted_schedule = [f"{header:<{col_width + 30}}"]
        for row in zip(*schedule):
            if not row[0].strip():
                formatted_schedule.append(f"{' ' * 28}{row[1]:<{col_width}}")
            else:
                formatted_schedule.append(f"{row[0]:<{col_width + 15}}{row[1]:<{col_width}}")
        formatted_schedule_res = "\n".join(formatted_schedule)
        link = "\n\nПосилання на сайт: <a href='http://avto-servis.com.ua/avtobusn-marshruti/marshrut-324/'>Деталі</a>"
        bot.send_message(chat.chat.id, f"{formatted_schedule_res}{link}", parse_mode='HTML')
    except Exception as e:
        bot.send_message(chat.chat.id, f"Помилка при виконанні запиту до розкладу автобусу 324: {e}")

@bot.message_handler(commands=['bus_324_weekend'])
def bus_324_schedule_weekend(chat):
    try:
        username = chat.from_user.username or "No Username"
        log_request(chat.from_user.id, username, 'bus_324_weekend')
        schedule = bus_schedule_324_weekend
        header = f"------<b>324(Вихідні)</b>------\n{'<b>З Процеву</b>':<15} {'<b>З Києва</b>':<12}"
        col_width = max(len(item) for sublist in schedule for item in sublist) + 2
        formatted_schedule = [f"{header:<{col_width + 30}}"]
        for row in zip(*schedule):
            if not row[0].strip():
                formatted_schedule.append(f"{' ' * 28}{row[1]:<{col_width}}")
            else:
                formatted_schedule.append(f"{row[0]:<{col_width + 15}}{row[1]:<{col_width}}")
        formatted_schedule_res = "\n".join(formatted_schedule)
        link = "\n\nПосилання на сайт: <a href='http://avto-servis.com.ua/avtobusn-marshruti/marshrut-324/'>Деталі</a>"
        bot.send_message(chat.chat.id, f"{formatted_schedule_res}{link}", parse_mode='HTML')
    except Exception as e:
        bot.send_message(chat.chat.id, f"Помилка при виконання запиту до розкладу автобусу 324 weekend: {e}")

@bot.message_handler(commands=['bus_324_weekday'])
def bus_324_schedule_weekday(chat):
    try:
        username = chat.from_user.username or "No Username"
        log_request(chat.from_user.id, username, 'bus_324_weekday')
        schedule = bus_schedule_324
        header = f"----------<b>324</b>----------\n{'<b>З Процеву</b>':<15} {'<b>З Києва</b>':<12}"
        col_width = max(len(item) for sublist in schedule for item in sublist) + 2
        formatted_schedule = [f"{header:<{col_width + 30}}"]
        for row in zip(*schedule):
            if not row[0].strip():
                formatted_schedule.append(f"{' ' * 28}{row[1]:<{col_width}}")
            else:
                formatted_schedule.append(f"{row[0]:<{col_width + 15}}{row[1]:<{col_width}}")
        formatted_schedule_res = "\n".join(formatted_schedule)
        link = "\n\nПосилання на сайт: <a href='http://avto-servis.com.ua/avtobusn-marshruti/marshrut-324/'>Деталі</a>"
        bot.send_message(chat.chat.id, f"{formatted_schedule_res}\n{link}", parse_mode='HTML')
    except Exception as e:
        bot.send_message(chat.chat.id, f"Помилка при виконання запиту до розкладу автобусу 324 weekday: {e}")

@bot.message_handler(commands=['all'])
def full_schedule(chat):
    try:
        username = chat.from_user.username or "No Username"
        log_request(chat.from_user.id, username, 'all')
        today = datetime.today().weekday()

        if today in [5, 6]:
            schedule_324 = bus_schedule_324_weekend
            header_324 = f"------<b>324(Вихідні)</b>------\n{'<b>З Процеву</b>':<16} {'<b>З Києва</b>':<12}"
        else:
            schedule_324 = bus_schedule_324
            header_324 = f"----------<b>324</b>----------\n{'<b>З Процеву</b>':<16} {'<b>З Києва</b>':<12}"

        header_941 = f"---------------<b>941</b>---------------\n{'<b>З Воронькову</b>':<30} {'<b>З Києва</b>':<12}"
        col_width = max(len(item) for sublist in bus_schedule_941 for item in sublist) + 2
        formatted_schedule = [f"{header_941:<{col_width + 29}}"]
        for row in zip(*bus_schedule_941):
            if not row[0].strip():
                formatted_schedule.append(f"{' ' * (col_width+18)}{row[1]:<{col_width}}")
            else:
                if len(row[0]) == col_width-2:
                    formatted_schedule.append(f"{row[0]:<{col_width+1}}{row[1]:<{col_width}}")
                else:
                    formatted_schedule.append(f"{row[0]:<{col_width+13}}{row[1]:<{col_width}}")
        formatted_schedule_941_res = "\n".join(formatted_schedule)

        col_width = max(len(item) for sublist in schedule_324 for item in sublist) + 2
        formatted_schedule = [f"{header_324:<{col_width + 30}}"]

        for row in zip(*schedule_324):
            if not row[0].strip():
                formatted_schedule.append(f"{' ' * 28}{row[1]:<{col_width}}")
            else:
                formatted_schedule.append(f"{row[0]:<{col_width + 15}}{row[1]:<{col_width}}")
        formatted_schedule_324_res = "\n".join(formatted_schedule)

        link = "\n\nПосилання на сайт для 324: <a href='http://avto-servis.com.ua/avtobusn-marshruti/marshrut-324/'>Деталі</a>"

        full_schedule_message = (f"{formatted_schedule_941_res}\n\n{formatted_schedule_324_res}{link}")
        bot.send_message(chat.chat.id, full_schedule_message, parse_mode='HTML')
    except Exception as e:
        bot.send_message(chat.chat.id, f"Помилка при виконання запиту до розкладу автобусу 324 all: {e}")

@bot.message_handler(commands=['next_buses'])
def next_buses(chat):
    try:
        username = chat.from_user.username or "No Username"
        log_request(chat.from_user.id, username, 'next_buses')
        kyiv_tz = pytz.timezone('Europe/Kiev')
        now = datetime.now(kyiv_tz)
        today = datetime.today().weekday()

        if today in [5, 6]:
            schedule_324 = bus_schedule_324_weekend
        else:
            schedule_324 = bus_schedule_324

        schedule_941 = bus_schedule_941

        upcoming_941_kyiv = get_upcoming_buses(now, schedule_941[1])
        upcoming_941_vornykiv = get_upcoming_buses(now, schedule_941[0])
        upcoming_324_kyiv = get_upcoming_buses(now, schedule_324[1])
        upcoming_324_protsiv = get_upcoming_buses(now, schedule_324[0])

        kyiv_buses = sorted(
            [(bus.time, '324', bus.description) for bus in upcoming_324_kyiv] +
            [(bus.time, '941', bus.description) for bus in upcoming_941_kyiv],
            key=lambda x: x[0]
        )

        protsiv_buses = sorted(
            [(bus.time, '324', bus.description) for bus in upcoming_324_protsiv] +
            [(bus.time, '941', bus.description) for bus in upcoming_941_vornykiv],
            key=lambda x: x[0]
        )

        formatted_kyiv = "\n".join([
            f"{bus_time.strftime('%H:%M')} - {route} {f'({description})' if description else ''}"
            for bus_time, route, description in kyiv_buses
        ])

        formatted_protsiv = "\n".join([
            f"{bus_time.strftime('%H:%M')} - {route} {f'({description})' if description else ''}"
            for bus_time, route, description in protsiv_buses
        ])
        if any("(до лік. Ч. Хутір)" in line for line in formatted_protsiv.split("\n")):
            header = "----------<b>Найближчі автобуси</b>----------\n"
            header2="<b>З Села</b>                                        <b>З Києва</b>"
            max_lines = max(len(formatted_kyiv.split("\n")), len(formatted_protsiv.split("\n")))
            formatted_kyiv_lines = formatted_kyiv.split("\n") + [""] * (max_lines - len(formatted_kyiv.split("\n")))
            formatted_protsiv_lines = formatted_protsiv.split("\n") + [""] * (
                        max_lines - len(formatted_protsiv.split("\n")))
            combined_schedule = "\n".join([
                f"{protsiv_line:<32}{kyiv_line}" if protsiv_line.endswith("Хутір)") else f"{protsiv_line:<44}{kyiv_line if not protsiv_line.endswith('941') else ' ' + kyiv_line}"
                if protsiv_line.strip()
                else f"{' ':<52} {kyiv_line}"
                for protsiv_line, kyiv_line in zip(formatted_protsiv_lines, formatted_kyiv_lines)
            ])
        else:
            header = "-----<b>Найближчі автобуси</b>-----\n"
            header2="<b>З Села</b>                     <b>З Києва</b>"
            max_lines = max(len(formatted_kyiv.split("\n")), len(formatted_protsiv.split("\n")))
            formatted_kyiv_lines = formatted_kyiv.split("\n") + [""] * (max_lines - len(formatted_kyiv.split("\n")))
            formatted_protsiv_lines = formatted_protsiv.split("\n") + [""] * (
                        max_lines - len(formatted_protsiv.split("\n")))

            combined_schedule = "\n".join([
                f"{protsiv_line:<24} {kyiv_line if not protsiv_line.endswith('941') else ' ' + kyiv_line}"
                if protsiv_line.strip()
                else f"{' ':<33} {kyiv_line}"
                for protsiv_line, kyiv_line in zip(formatted_protsiv_lines, formatted_kyiv_lines)
            ])

        link = "\n\nПосилання на сайт для 324: <a href='http://avto-servis.com.ua/avtobusn-marshruti/marshrut-324/'>Деталі</a>"
        bot.send_message(
            chat.chat.id,
            f"{header}\n{header2}\n{combined_schedule}{link}",
            parse_mode='HTML'
        )
    except Exception as e:
        bot.send_message(chat.chat.id, f"Помилка при виконання запиту до розкладу автобусу next_buses: {e}")

def parse_time(time_str):
    return datetime.strptime(time_str, "%H:%M").time()

def format_time(time_obj):
    return time_obj.strftime("%H:%M")

def get_upcoming_buses(current_time, schedule):
    kyiv_tz = pytz.timezone('Europe/Kiev')
    now = datetime.now(kyiv_tz)
    current_time_kyiv = now.replace(hour=current_time.hour, minute=current_time.minute, second=0, microsecond=0)
    cutoff_time = current_time_kyiv + timedelta(hours=2)

    current_time_only = current_time_kyiv.time()
    cutoff_time_only = cutoff_time.time()

    upcoming_buses = []
    for text in schedule:
        time_match = re.match(r'(\d{1,2}:\d{2})', text)
        if time_match:
            bus_time = datetime.strptime(time_match.group(1), "%H:%M").time()
            if current_time_only < bus_time <= cutoff_time_only:
                upcoming_buses.append(BusInfo(text))
    return sorted(upcoming_buses)

if not os.path.exists(statistics_file):
    with open(statistics_file, 'w') as f:
        f.write("User ID, Command, Timestamp\n")

def log_request(user_id, username, command):
    kyiv_tz = pytz.timezone('Europe/Kiev')
    timestamp = datetime.now(kyiv_tz).strftime('%Y-%m-%d %H:%M:%S')
    with open(statistics_file, 'a') as f:
        f.write(f"{user_id}, {username}, {command}, {timestamp}\n")

def read_statistics():
    statistics = {
        'total_requests': 0,
        'client_requests': {},
        'command_requests': {}
    }

    with open(statistics_file, 'r') as f:
        next(f)
        for line in f:
            user_id, username, command, timestamp = line.strip().split(", ")
            statistics['total_requests'] += 1
            if user_id not in statistics['client_requests']:
                statistics['client_requests'][user_id] = {
                    'username': username,
                    'count': 0,
                    'commands': {}
                }
            statistics['client_requests'][user_id]['count'] += 1
            if command not in statistics['command_requests']:
                statistics['command_requests'][command] = 0
            statistics['command_requests'][command] += 1
            if command not in statistics['client_requests'][user_id]['commands']:
                statistics['client_requests'][user_id]['commands'][command] = 0
            statistics['client_requests'][user_id]['commands'][command] += 1

    return statistics


@bot.message_handler(commands=['stats'])
def show_statistics(chat):
    try:
        if chat.from_user.id == ADMIN_ID:
            statistics = read_statistics()
            total_requests = statistics['total_requests']
            client_requests = statistics['client_requests']
            command_requests = statistics['command_requests']
            response = f"Загальна кількість запитів: {total_requests}\n\nКлієнти:\n"
            for user_id, data in client_requests.items():
                most_used_command = max(data['commands'], key=data['commands'].get) if data['commands'] else "None"
                most_used_count = data['commands'].get(most_used_command, 0) if most_used_command != "None" else 0
                response += (f"- {data['username']} (ID: {user_id}): {data['count']} запитів, "
                             f"Улюблений запит: {most_used_command} ({most_used_count} рази)\n")

            response += "\nСтатистика по запитам:\n"
            for command, count in command_requests.items():
                response += f"- {command}: {count} разів\n"

            bot.send_message(chat.chat.id, response)
        else:
            bot.send_message(chat.chat.id, "У вас немає доступу до цієї команди.")
    except Exception as e:
        bot.send_message(chat.chat.id, f"Помилка при виведенні статистики: {e}")

@bot.message_handler(commands=['photo_941'])
def show_941_schedule_photo(chat):
    try:
        with open(file_path_photo_941, 'rb') as photo:
            bot.send_photo(chat.chat.id, photo)
    except Exception as e:
        bot.send_message(chat.chat.id, f"Помилка при завантаженні фото: {e}")

initialize_schedules()

def send_shutdown_message():
    bot.send_message(chat_id=ADMIN_ID, text="The bot has been shut down.")

def signal_handler(sig, frame):
    send_shutdown_message()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)
bot.infinity_polling()