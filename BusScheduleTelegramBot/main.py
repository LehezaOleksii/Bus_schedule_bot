import telebot
from telebot import types
from datetime import datetime, timedelta
import pandas as pd
from io import BytesIO
import pytz
import re
import signal
import sys

bot = telebot.TeleBot('7052131672:AAHEs6hOG_27apuoHFVyq81CdfXPn_Yx_WI')
ADMIN_ID = 818757464
users = {}
request_count = 0
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
        user_id = chat.from_user.id
        username = chat.from_user.username or "Нет ника"
        if user_id not in users:
            users[user_id] = username
        bot.send_message(chat.chat.id, 'Бот розпочав роботу. Доступні функції перегляду розкладу автобусів')
    except Exception as e:
        bot.send_message(chat.chat.id, f"Помилка: {e}")

def format_schedule(header, schedule, max_col_width):
    formatted_schedule = [f"{header}"]
    print(max_col_width)
    for row in zip(*schedule):
        if not row[0].strip():
            print('\nIF')
            current_length = len(row[1])
            print(current_length)
            spaces_needed = max_col_width - current_length
            print(spaces_needed)
            formatted_schedule.append(f"{' ' * max(spaces_needed, 0)}{row[1]:<{max_col_width}}")
        else:
            print('\nELSE')
            current_length = len(row[0])
            print(current_length)
            spaces_needed = max_col_width - current_length
            print(spaces_needed)
            formatted_schedule.append(f"{row[0]:<{max_col_width}}{' ' * max(spaces_needed, 0)}{row[1]:<{max_col_width}}")

    return "\n".join(formatted_schedule)

@bot.message_handler(commands=['bus_941'])
def bus_941_schedule(chat):
    try:
        global request_count
        request_count += 1
        schedule = bus_schedule_941
        header = f"------------<b>941</b>------------\n{'З Воронькову':<16} {'З Києва':<12}"
        formatted_schedule_res = format_schedule(header, schedule, max_col_width=16)
        bot.send_message(chat.chat.id, f"{formatted_schedule_res}", parse_mode='HTML')
    except Exception as e:
        bot.send_message(chat.chat.id, f"Помилка при виконанні запиту до розкладу автобусу 941: {e}")


@bot.message_handler(commands=['bus_324'])
def bus_324_schedule(chat):
    try:
        global request_count
        request_count += 1
        today = datetime.today().weekday()
        spaces_between_max_col_width_and_second_col = 0
        max_col_width = 0
        if today in [5, 6]:
            schedule = bus_schedule_324_weekend
            max_col_width = max(len(item) for sublist in schedule for item in sublist) + spaces_between_max_col_width_and_second_col+2
            header = f"------<b>324(Вихідні)</b>------\n{'З Процеву':<{max_col_width}} {'З Києва':<{max_col_width}}"
        else:
            schedule = bus_schedule_324
            max_col_width = max(len(item) for sublist in schedule for item in sublist) + spaces_between_max_col_width_and_second_col+2
            header = f"----------<b>324</b>----------\n{'З Процеву':<{max_col_width}} {'З Києва':<{max_col_width}}"

        formatted_schedule_res = format_schedule(header, schedule, max_col_width)
        link = "\n\nПосилання на сайт: http://avto-servis.com.ua/avtobusn-marshruti/marshrut-324/"
        bot.send_message(chat.chat.id, f"{formatted_schedule_res}{link}", parse_mode='HTML')
    except Exception as e:
        bot.send_message(chat.chat.id, f"Помилка при виконанні запиту до розкладу автобусу 324: {e}")

@bot.message_handler(commands=['bus_324_weekend'])
def bus_324_schedule(chat):
    try:
        global request_count
        request_count += 1
        schedule = bus_schedule_324_weekend
        header = f"------<b>324(Вихідні)</b>------\n{'З Процеву':<16} {'З Києва':<12}"
        col_width = max(len(item) for sublist in schedule for item in sublist) + 2
        formatted_schedule = [f"{header:<{col_width + 30}}"]
        for row in zip(*schedule):
            if not row[0].strip():
                formatted_schedule.append(f"{' ' * 28}{row[1]:<{col_width}}")
            else:
                formatted_schedule.append(f"{row[0]:<{col_width + 16}}{row[1]:<{col_width}}")
        formatted_schedule_res = "\n".join(formatted_schedule)
        link = "\n\nПосилання на сайт: http://avto-servis.com.ua/avtobusn-marshruti/marshrut-324/"
        bot.send_message(chat.chat.id, f"{formatted_schedule_res}\n{link}", parse_mode='HTML')
    except Exception as e:
        bot.send_message(chat.chat.id, f"Помилка при виконання запиту до розкладу автобусу 324 weekend: {e}")

@bot.message_handler(commands=['bus_324_weekday'])
def bus_324_schedule_weekday(chat):
    try:
        global request_count
        request_count += 1
        schedule = bus_schedule_324
        header = f"----------<b>324</b>----------\n{'З Процеву':<16} {'З Києва':<12}"
        col_width = max(len(item) for sublist in schedule for item in sublist) + 2
        formatted_schedule = [f"{header:<{col_width + 30}}"]

        for row in zip(*schedule):
            if not row[0].strip():
                formatted_schedule.append(f"{' ' * 28}{row[1]:<{col_width}}")
            else:
                formatted_schedule.append(f"{row[0]:<{col_width + 16}}{row[1]:<{col_width}}")
        formatted_schedule_res = "\n".join(formatted_schedule)

        link = "\n\nПосилання на сайт: http://avto-servis.com.ua/avtobusn-marshruti/marshrut-324/"
        bot.send_message(chat.chat.id, f"{formatted_schedule_res}\n{link}", parse_mode='HTML')
    except Exception as e:
        bot.send_message(chat.chat.id, f"Помилка при виконання запиту до розкладу автобусу 324 weekday: {e}")

@bot.message_handler(commands=['all'])
def full_schedule(chat):
    try:
        global request_count
        request_count += 1
        today = datetime.today().weekday()

        if today in [5, 6]:
            schedule_324 = bus_schedule_324_weekend
            header_324 = f"------<b>324(Вихідні)</b>------\n{'З Процеву':<16} {'З Києва':<12}"
        else:
            schedule_324 = bus_schedule_324
            header_324 = f"----------<b>324</b>----------\n{'З Процеву':<16} {'З Києва':<12}"

        header_941 = f"------------<b>941</b>------------\n{'З Воронькову':<16} {'З Києва':<12}"
        col_width = max(len(item) for sublist in bus_schedule_941 for item in sublist) + 2
        formatted_schedule = [f"{header_941:<{col_width + 30}}"]
        for row in zip(*bus_schedule_941):
            if not row[0].strip():
                formatted_schedule.append(f"{' ' * 31}{row[1]:<{col_width}}")
            else:
                formatted_schedule.append(f"{row[0]:<{col_width + 19}}{row[1]:<{col_width}}")
        formatted_schedule_941_res = "\n".join(formatted_schedule)

        col_width = max(len(item) for sublist in schedule_324 for item in sublist) + 2
        formatted_schedule = [f"{header_324:<{col_width + 30}}"]

        for row in zip(*schedule_324):
            if not row[0].strip():
                formatted_schedule.append(f"{' ' * 28}{row[1]:<{col_width}}")
            else:
                formatted_schedule.append(f"{row[0]:<{col_width + 16}}{row[1]:<{col_width}}")
        formatted_schedule_324_res = "\n".join(formatted_schedule)

        link = "\n\nПосилання на сайт для 324: http://avto-servis.com.ua/avtobusn-marshruti/marshrut-324/"

        full_schedule_message = (f"{formatted_schedule_941_res}\n\n{formatted_schedule_324_res}{link}")
        bot.send_message(chat.chat.id, full_schedule_message, parse_mode='HTML')
    except Exception as e:
        bot.send_message(chat.chat.id, f"Помилка при виконання запиту до розкладу автобусу 324 all: {e}")

@bot.message_handler(commands=['next_buses'])
def next_buses(chat):
    try:
        global request_count
        request_count += 1
        kyiv_tz = pytz.timezone('Europe/Kiev')
        now = datetime.now(kyiv_tz)
        today = datetime.today().weekday()

        # Вибираємо відповідний розклад для 324 в залежності від дня тижня
        if today in [5, 6]:  # Якщо це субота чи неділя
            schedule_324 = bus_schedule_324_weekend
        else:
            schedule_324 = bus_schedule_324

        schedule_941 = bus_schedule_941

        # Отримуємо найближчі автобуси для кожного маршруту
        upcoming_941_kyiv = get_upcoming_buses(now, schedule_941[1])
        upcoming_941_vornykiv = get_upcoming_buses(now, schedule_941[0])
        upcoming_324_kyiv = get_upcoming_buses(now, schedule_324[1])
        upcoming_324_protsiv = get_upcoming_buses(now, schedule_324[0])

        # Сортуємо автобуси для Києва та Проціву
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

        # Формуємо повідомлення для відправки
        header = "-----<b>Найближчі автобуси</b>-----\n"
        formatted_kyiv = "\n".join([
            f"{bus_time.strftime('%H:%M')} - {route} {f'({description})' if description else ''}"
            for bus_time, route, description in kyiv_buses
        ])

        formatted_protsiv = "\n".join([
            f"{bus_time.strftime('%H:%M')} - {route} {f'({description})' if description else ''}"
            for bus_time, route, description in protsiv_buses
        ])
        # Додаємо порожні строки для вирівнювання, якщо списки різної довжини
        max_lines = max(len(formatted_kyiv.split("\n")), len(formatted_protsiv.split("\n")))
        formatted_kyiv_lines = formatted_kyiv.split("\n") + [""] * (max_lines - len(formatted_kyiv.split("\n")))
        formatted_protsiv_lines = formatted_protsiv.split("\n") + [""] * (max_lines - len(formatted_protsiv.split("\n")))

        # Об'єднуємо строки для відправки
        combined_schedule = "\n".join([
            f"{protsiv_line:<24} {kyiv_line if not protsiv_line.endswith('941') else ' ' + kyiv_line}"
            if protsiv_line.strip()
            else f"{' ':<33} {kyiv_line}"
            for protsiv_line, kyiv_line in zip(formatted_protsiv_lines, formatted_kyiv_lines)
        ])

        # Додаємо посилання
        link = "\n\nПосилання на сайт для 324: http://avto-servis.com.ua/avtobusn-marshruti/marshrut-324/"

        # Відправляємо повідомлення
        bot.send_message(
            chat.chat.id,
            f"{header}\n<b>З Села</b>                     <b>З Києва</b>\n{combined_schedule}{link}",
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

# Приклад використання:
current_time = datetime.now().time()
schedule = ["7:30 (до лік. Ч. Хутір)", "8:00", "8:45 (до вокзалу)", "9:15", "10:00 (до парку)"]  # Приклад розкладу
upcoming_buses = get_upcoming_buses(current_time, schedule)

for bus in upcoming_buses:
    print(bus)


@bot.message_handler(commands=['statistics'])
def show_statistics(chat):
    try:
        if chat.from_user.id == ADMIN_ID:
            total_users = len(users)
            total_requests = request_count
            user_list = "\n".join([f"Username: {username}, ID: {user_id}" for user_id, username in users.items()])
            if not user_list:
                user_list = "Користувачі відсутні."
            bot.send_message(chat.chat.id,
                             f"<b>Статистика:</b>\n"
                             f"Кількість запитів: {total_requests}\n"
                             f"Кількість користувачів: {total_users}\n"
                             f"Список користувачів:\n{user_list}\n",
                             parse_mode='HTML')
        else:
            bot.send_message(chat.chat.id, "У вас немає доступу до цієї команди.")
    except Exception as e:
        bot.send_message(chat.chat.id, f"Помилка при виведені статистики клієнтів: {e}")

@bot.message_handler(commands=['photo_941'])
def show_941_schedule_photo(chat):
    try:
        with open(file_path_photo_941, 'rb') as photo:
            bot.send_photo(chat.chat.id, photo)
    except Exception as e:
        bot.send_message(chat.chat.id, f"Помилка при завантаженні фото: {e}")

@bot.message_handler(commands=['info'])
def info (chat):
    try:
        bot.send_message(chat.chat.id,"/next_buses - Розклад на наступні 2 години для 941 та 324\n\n"
                       "/all - Розклад 941 та 324. \n324 має розклад на будні та вихідіні, розклад автомтаично підлаштовується під сьогоднішній день.\n"
                        "Знизу надсилається посилання на сайт з розкладом 324 автобусу \n\n"
                       "/bus_941 - Розклад 941\n\n"
                       "/bus_324 - Розклад 324\n324 має розклад на будні та вихідіні, розклад автомтаично підлаштовується під сьогоднішній день.\n"
                                      "Знизу надсилається посилання на сайт з розкладом 324 автобусу\n\n"
                       "/bus_324_weekend - Розклад 324 у вихідні\n"
                                      "Знизу надсилається посилання на сайт з розкладом 324 автобусу\n\n"
                       "/bus_324_weekday - Розклад 324 у будні\n"
                                      "Знизу надсилається посилання на сайт з розкладом 324 автобусу\n\n"
                       "/photo_941 - Розклад 941 у jpg форматі\n\n"
                       "/info - детальна інформація про можливості бота\n\n")
    except Exception as e:
        bot.send_message(chat.chat.id, f"Помилка при надсиланні детальної інформаціїї: {e}")

initialize_schedules()

def send_shutdown_message():
    bot.send_message(chat_id=ADMIN_ID, text="The bot has been shut down.")

def signal_handler(sig, frame):
    send_shutdown_message()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)
bot.infinity_polling()