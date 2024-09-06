import telebot
from telebot import types
from datetime import datetime, timedelta
from itertools import zip_longest
import pandas as pd
from io import BytesIO

bot = telebot.TeleBot('7052131672:AAHEs6hOG_27apuoHFVyq81CdfXPn_Yx_WI')
ADMIN_ID = 818757464
users = {}
request_count = 0
current_route = None

bus_schedule_941 = [
]

bus_schedule_324 = [
]

bus_schedule_324_weekend = [
]

@bot.message_handler(commands=['change_schedule'])
def change_schedule(chat):
    if chat.from_user.id == ADMIN_ID:
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        btn_941 = types.KeyboardButton('941 all')
        btn_324_weekday = types.KeyboardButton('324 weekday')
        btn_324_weekend = types.KeyboardButton('324 weekend')
        markup.add(btn_941, btn_324_weekday, btn_324_weekend)
        bot.send_message(chat.chat.id, "Оберіть маршрут, для якого бажаєту змінити розклад:", reply_markup=markup)
    else:
        bot.send_message(chat.chat.id, "У вас немає доступу до цієї команди.")

@bot.message_handler(func=lambda message: message.text in ['941 all', '324 weekday', '324 weekend'])
def route_selected(chat):
    if chat.from_user.id == ADMIN_ID:
        global current_route
        current_route = chat.text
        bot.send_message(chat.chat.id, f"Ви обрали {current_route}. Тепер завантажту Excel файл з розкладом.")
    else:
        bot.send_message(chat.chat.id, "У вас немає доступу до цієї команди.")

@bot.message_handler(content_types=['document'])
def handle_document(chat):
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
        bot.send_message(chat.chat.id, "У вас немає доступу до цієї команди або маршрут не обран.")

def update_schedule(df, route):

    if route == '941 all':
        global bus_schedule_941
        bus_schedule_941 = df.values.tolist()
    elif route == '324 weekday':
        global bus_schedule_324
        bus_schedule_324 = df.values.tolist()
    elif route == '324 weekend':
        global bus_schedule_324_weekend
        bus_schedule_324_weekend = df.values.tolist()

@bot.message_handler(commands=['start'])
def start(chat):
    user_id = chat.from_user.id
    username = chat.from_user.username or "Нет ника"
    if user_id not in users:
        users[user_id] = username
    bot.send_message(chat.chat.id, 'Бот розпочав роботу. Доступні функції перегляду розкладу автобусів')

@bot.message_handler(commands=['bus_941'])
def bus_941_schedule(chat):
    global request_count
    request_count += 1
    schedule = bus_schedule_941
    header = f"------------<b>941</b>------------\n{'З Воронькову':<16} {'З Києва':<12}"
    col_width = max(len(item) for sublist in schedule for item in sublist) + 2
    formatted_schedule = [f"{header:<{col_width + 30}}"]
    for row in zip(*schedule):
        formatted_schedule.append(f"{row[0]:<{col_width + 19}}{row[1]:<{col_width}}")
    formatted_schedule_res = "\n".join(formatted_schedule)
    bot.send_message(chat.chat.id, f"{formatted_schedule_res}", parse_mode='HTML')

@bot.message_handler(commands=['bus_324'])
def bus_324_schedule(chat):
    global request_count
    request_count += 1
    today = datetime.today().weekday()
    if today in [5, 6]:
        schedule = bus_schedule_324_weekend
        header = f"-----<b>324(Вихідний)</b>-----\n{'З Процеву':<16} {'З Києва':<12}"
    else:
        schedule = bus_schedule_324
        header = f"----------<b>324</b>----------\n{'З Процеву':<16} {'З Києва':<12}"

    col_width = max(len(item) for sublist in schedule for item in sublist) + 2
    formatted_schedule = [f"{header:<{col_width + 30}}"]
    for row in zip(*schedule):
        formatted_schedule.append(f"{row[0]:<{col_width + 16}}{row[1]:<{col_width}}")
    formatted_schedule_res = "\n".join(formatted_schedule)
    link = "\n\nПосилання на сайт: http://avto-servis.com.ua/avtobusn-marshruti/marshrut-324/"
    bot.send_message(chat.chat.id, f"{formatted_schedule_res}{link}", parse_mode='HTML')

@bot.message_handler(commands=['bus_324_weekend'])
def bus_324_schedule(chat):
    global request_count
    request_count += 1
    schedule = bus_schedule_324_weekend
    header = f"-----<b>324(Вихідний)</b>-----\n{'З Процеву':<16} {'З Києва':<12}"
    col_width = max(len(item) for sublist in schedule for item in sublist) + 2
    formatted_schedule = [f"{header:<{col_width + 30}}"]
    for row in zip(*schedule):
        formatted_schedule.append(f"{row[0]:<{col_width + 16}}{row[1]:<{col_width}}")
    formatted_schedule_res = "\n".join(formatted_schedule)
    link = "\n\nПосилання на сайт: http://avto-servis.com.ua/avtobusn-marshruti/marshrut-324/"
    bot.send_message(chat.chat.id, f"{formatted_schedule_res}\n{link}", parse_mode='HTML')


def format_schedule(header, schedule):
    col_width = max(len(item) for sublist in schedule for item in sublist) + 2
    formatted_schedule = [f"{header:<{col_width + 30}}"]
    for row in zip(*schedule):
        formatted_schedule.append(f"{row[0]:<{col_width + 20}}{row[1]:<{col_width}}")

    return "\n".join(formatted_schedule)

@bot.message_handler(commands=['bus_324_weekday'])
def bus_324_schedule_weekday(chat):
    global request_count
    request_count += 1
    schedule = bus_schedule_324
    header = f"----------<b>324</b>----------\n{'З Процеву':<16} {'З Києва':<12}"
    col_width = max(len(item) for sublist in schedule for item in sublist) + 2
    formatted_schedule = [f"{header:<{col_width + 30}}"]
    for row in zip(*schedule):
        formatted_schedule.append(f"{row[0]:<{col_width + 16}}{row[1]:<{col_width}}")
    formatted_schedule_res = "\n".join(formatted_schedule)
    link = "\n\nПосилання на сайт: http://avto-servis.com.ua/avtobusn-marshruti/marshrut-324/"
    bot.send_message(chat.chat.id, f"{formatted_schedule_res}\n{link}", parse_mode='HTML')


def format_schedule(header, schedule):
    col_width = max(len(item) for sublist in schedule for item in sublist) + 2
    formatted_schedule = [f"{header:<{col_width + 30}}"]
    for row in zip(*schedule):
        formatted_schedule.append(f"{row[0]:<{col_width + 20}}{row[1]:<{col_width}}")

    return "\n".join(formatted_schedule)

@bot.message_handler(commands=['all'])
def full_schedule(chat):
    global request_count
    request_count += 1
    today = datetime.today().weekday()

    if today in [5, 6]:
        schedule_324 = bus_schedule_324_weekend
    else:
        schedule_324 = bus_schedule_324

    header_941 = "------------<b>941</b>------------\nЗ Воронькову       З Києва"
    formatted_schedule_941 = format_schedule(header_941, bus_schedule_941)

    header_324 = "------------<b>324</b>------------\nЗ Процеву             З Києва"
    formatted_schedule_324 = format_schedule(header_324, schedule_324)

    link = "\n\nПосилання на сайт для 324: http://avto-servis.com.ua/avtobusn-marshruti/marshrut-324/"

    full_schedule_message = (f"{formatted_schedule_941}\n\n{formatted_schedule_324}{link}")
    bot.send_message(chat.chat.id, full_schedule_message, parse_mode='HTML')


@bot.message_handler(commands=['next_buses'])
def next_buses(chat):
    global request_count
    request_count += 1
    now = datetime.now().time()
    today = datetime.today().weekday()

    # Determine the schedule to use based on the day of the week
    if today in [5, 6]:
        schedule_324 = bus_schedule_324_weekend
    else:
        schedule_324 = bus_schedule_324

    schedule_941 = bus_schedule_941

    # Convert schedule lists of time strings to datetime.time objects for sorting
    def convert_to_time_list(schedule):
        return [parse_time(time) for time in schedule]

    upcoming_941_kyiv = convert_to_time_list(schedule_941[1])
    upcoming_941_vornykiv = convert_to_time_list(schedule_941[0])
    upcoming_324_kyiv = convert_to_time_list(schedule_324[1])
    upcoming_324_protsiv = convert_to_time_list(schedule_324[0])

    # Sort upcoming buses by time
    kyiv_buses = sorted(
        [(time, '324') for time in upcoming_324_kyiv] +
        [(time, '941') for time in upcoming_941_kyiv],
        key=lambda x: x[0]
    )

    protsiv_buses = sorted(
        [(time, '324') for time in upcoming_324_protsiv] +
        [(time, '941') for time in upcoming_941_vornykiv],
        key=lambda x: x[0]
    )

    header = "-----<b>Найближчі автобуси</b>-----\n"
    formatted_kyiv = "\n".join([f"{format_time(time)} {route}" for time, route in kyiv_buses])
    formatted_protsiv = "\n".join([f"{format_time(time)} {route}" for time, route in protsiv_buses])

    max_lines = max(len(formatted_kyiv.split("\n")), len(formatted_protsiv.split("\n")))
    formatted_kyiv_lines = formatted_kyiv.split("\n") + [""] * (max_lines - len(formatted_kyiv.split("\n")))
    formatted_protsiv_lines = formatted_protsiv.split("\n") + [""] * (max_lines - len(formatted_protsiv.split("\n")))

    combined_schedule = "\n".join([
        f"{protsiv_line:<24} {kyiv_line if not protsiv_line.endswith('941') else ' ' + kyiv_line}"
        if protsiv_line.strip()
        else f"{'':<33} {kyiv_line}"
        for protsiv_line, kyiv_line in zip(formatted_protsiv_lines, formatted_kyiv_lines)
    ])

    link = "\n\nПосилання на сайт для 324: http://avto-servis.com.ua/avtobusn-marshruti/marshrut-324/"
    bot.send_message(
        chat.chat.id,
        f"{header}\n<b>З Села</b>                     <b>З Києва</b>\n{combined_schedule}{link}",
        parse_mode='HTML'
    )

def parse_time(time_str):
    return datetime.strptime(time_str, "%H:%M").time()

def format_time(time_obj):
    return time_obj.strftime("%H:%M")

@bot.message_handler(commands=['statistics'])
def show_statistics(chat):
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

def parse_time(time_str):
    return datetime.strptime(time_str, "%H:%M").time()

def format_time(time_obj):
    return time_obj.strftime("%H:%M")

def get_upcoming_buses(current_time, schedule):
    cutoff_time = (datetime.combine(datetime.today(), current_time) + timedelta(hours=2)).time()
    upcoming_buses = [time for time in schedule if parse_time(time) > current_time and parse_time(time) <= cutoff_time]
    return sorted(upcoming_buses, key=parse_time)

bot.infinity_polling()