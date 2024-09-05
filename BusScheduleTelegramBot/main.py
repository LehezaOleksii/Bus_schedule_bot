import telebot
from telebot import types
from datetime import datetime, timedelta
from itertools import zip_longest

bot = telebot.TeleBot('7052131672:AAHEs6hOG_27apuoHFVyq81CdfXPn_Yx_WI')

bus_schedule_941 = [
    ["З Воронькову", "10:00", "13:15"],
    ["З Києва", "11:17", "12:16", "13:15"]
]

bus_schedule_324 = [
    ["З Процеву", "10:00", "13:00"],
    ["З Києва", "11:15", "12:16", "13:15"]
]

bus_schedule_324_weekend = [
    ["З Процеву", "12:00", "13:15","14:20"],
    ["З Києва", "12:00"]
]

@bot.message_handler(content_types=['start'])
def start(chat):
    markup = types.ReplyKeyboardMarkup()
    btn1 = types.KeyboardButton('324')
    btn2 = types.KeyboardButton('941')
    markup.add(btn1)
    markup.add(btn2)
    bot.send_message(chat.chat.id, "Select bus route:", reply_markup=markup)

# @bot.message_handler(commands=['start'])
# def main(chat):
#     bot.send_message(chat.chat.id, '')

@bot.message_handler(commands=['bus_324'])
def bus_324_schedule(chat):
    today = datetime.today().weekday()
    if today in [5, 6]:
        schedule = bus_schedule_324_weekend
        header = f"-----<b>324(Вихідний)</b>-----\n{'З Процеву':<12} {'З Києва':<12}"
    else:
        schedule = bus_schedule_324
        header = f"----------<b>324</b>----------\n{'З Процеву':<12} {'З Києва':<12}"

    formatted_schedule = "\n".join(
        [f"{from_proc:<17} {from_kyiv:<12}" if from_proc.strip() else f"{'':<22} {from_kyiv}"
         for from_proc, from_kyiv in zip_longest(schedule[0][1:], schedule[1][1:], fillvalue="")]
    )
    link = "\n\nПосилання на сайт: http://avto-servis.com.ua/avtobusn-marshruti/marshrut-324/"
    bot.send_message(chat.chat.id, f"{header}\n{formatted_schedule}{link}", parse_mode='HTML')


@bot.message_handler(commands=['bus_324_weekend'])
def bus_324_schedule(chat):
    schedule = bus_schedule_324_weekend
    header = f"-----<b>324(Вихідний)</b>-----\n{'З Процеву':<12} {'З Києва':<12}"
    formatted_schedule = "\n".join(
        [f"{from_proc:<17} {from_kyiv:<12}" if from_proc.strip() else f"{'':<22} {from_kyiv}"
         for from_proc, from_kyiv in zip_longest(schedule[0][1:], schedule[1][1:], fillvalue="")]
    )
    link = "\n\nПосилання на сайт: http://avto-servis.com.ua/avtobusn-marshruti/marshrut-324/"
    bot.send_message(chat.chat.id, f"{header}\n{formatted_schedule}{link}", parse_mode='HTML')


@bot.message_handler(commands=['all'])
def full_schedule(chat):
    today = datetime.today().weekday()
    if today in [5, 6]:
        schedule_324 = bus_schedule_324_weekend
    else:
        schedule_324 = bus_schedule_324

    header_941 = f"------------<b>941</b>------------\n{'З Воронькову':<18} {'З Києва':<12}"
    formatted_schedule_941 = "\n".join(
        [f"{from_proc:<26} {from_kyiv:<12}" if from_proc.strip() else f"{'':<30} {from_kyiv}"
         for from_proc, from_kyiv in zip_longest(bus_schedule_941[0][1:], bus_schedule_941[1][1:], fillvalue="")]
    )

    header_324 = f"----------<b>324</b>----------\n{'З Процеву':<12} {'З Києва':<12}"
    formatted_schedule_324 = "\n".join(
        [f"{from_proc:<17} {from_kyiv:<12}" if from_proc.strip() else f"{'':<22} {from_kyiv}"
         for from_proc, from_kyiv in zip_longest(schedule_324[0][1:], schedule_324[1][1:], fillvalue="")]
    )
    link = "\n\nПосилання на сайт для 324: http://avto-servis.com.ua/avtobusn-marshruti/marshrut-324/"

    full_schedule_message = (f"{header_941}\n{formatted_schedule_941}\n\n"
                             f"{header_324}\n{formatted_schedule_324}{link}")
    bot.send_message(chat.chat.id, full_schedule_message, parse_mode='HTML')


@bot.message_handler(commands=['next_buses'])
def next_buses(chat):
    now = datetime.now().time()
    today = datetime.today().weekday()

    if today in [5, 6]:
        schedule_324 = bus_schedule_324_weekend
    else:
        schedule_324 = bus_schedule_324

    upcoming_941_kyiv = get_upcoming_buses(now, bus_schedule_941[1][1:])
    upcoming_941_vornykiv = get_upcoming_buses(now, bus_schedule_941[0][1:])
    upcoming_324_kyiv = get_upcoming_buses(now, schedule_324[1][1:])
    upcoming_324_protsiv = get_upcoming_buses(now, schedule_324[0][1:])

    kyiv_buses = sorted(
        [(time, '324') for time in upcoming_324_kyiv] +
        [(time, '941') for time in upcoming_941_kyiv],
        key=lambda x: parse_time(x[0])
    )

    protsiv_buses = sorted(
        [(time, '324') for time in upcoming_324_protsiv] +
        [(time, '941') for time in upcoming_941_vornykiv],
        key=lambda x: parse_time(x[0])
    )

    header = "-----<b>Найближчі автобуси</b>-----\n"
    formatted_kyiv = "\n".join([f"{format_time(parse_time(time))} {route}" for time, route in kyiv_buses])
    formatted_protsiv = "\n".join([f"{format_time(parse_time(time))} {route}" for time, route in protsiv_buses])

    max_lines = max(len(formatted_kyiv.split("\n")), len(formatted_protsiv.split("\n")))
    formatted_kyiv_lines = formatted_kyiv.split("\n") + [""] * (max_lines - len(formatted_kyiv.split("\n")))
    formatted_protsiv_lines = formatted_protsiv.split("\n") + [""] * (max_lines - len(formatted_protsiv.split("\n")))

    combined_schedule = "\n".join([
        f"{protsiv_line:<24} {kyiv_line if not protsiv_line.endswith('941') else ' ' + kyiv_line}"
        if protsiv_line.strip()
        else f"{'':<33} {kyiv_line}"
        for protsiv_line, kyiv_line in zip(formatted_protsiv_lines,formatted_kyiv_lines)
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

def get_upcoming_buses(current_time, schedule):
    cutoff_time = (datetime.combine(datetime.today(), current_time) + timedelta(hours=2)).time()
    upcoming_buses = [time for time in schedule if parse_time(time) > current_time and parse_time(time) <= cutoff_time]
    return sorted(upcoming_buses, key=parse_time)

bot.infinity_polling()