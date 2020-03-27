import config
import telebot
from telebot import types
import requests
import dbworker
import json
from datetime import datetime

bot = telebot.TeleBot(config.TOKEN)

headers = {
    'content-type': 'application/x-www-form-urlencoded',
}
data = {
    'email': config.email,
    'password': config.password  # hashed
}
response = requests.post('https://web.ewa.ua/ewa/api/v10/user/login', headers=headers, data=data)
cookie = response.json()['sessionId']
sale_point = response.json()['user']['salePoint']['id']
user = response.json()['user']['id']
company_id = response.json()['user']['salePoint']['company']['id']
company_type = response.json()['user']['salePoint']['company']['type']
cookies = {
    'JSESSIONID': cookie
}
headers = {
    'content-type': 'application/json'
}

# CONSTANTS
customer_category = 'NATURAL'
utility = {}


def date_plus_day(message):
    date_raw = message.date
    date_from = datetime.fromtimestamp(int(date_raw)).strftime('%Y-%m-%d %H:%M:%S')
    date_from_list = date_from.split(' ')
    day_plus_one = int(date_from_list[0].split('-')[2]) + 1
    day_plus_seven = int(date_from_list[0].split('-')[2]) + 7
    date_plus_one_day = date_from_list[0].split('-')[0] + '-' + date_from_list[0].split('-')[1] + '-' + str(
        day_plus_one).zfill(2)  # Завтрашняя дата
    date_plus_seven_day = date_from_list[0].split('-')[0] + '-' + date_from_list[0].split('-')[1] + '-' + str(
        day_plus_seven).zfill(
        2)  # Дата +7 дней
    if str(day_plus_one) == '32' or str(day_plus_one) == '31':
        day_plus_one = '1'
        month_plus_one = int(date_from_list[0].split('-')[1]) + 1
        date_plus_one_day = date_from_list[0].split('-')[0] + '-' + str(month_plus_one).zfill(2) + '-' + str(day_plus_one).zfill(
            2)
    if str(day_plus_seven) == '32' or str(day_plus_seven) == '31' or str(day_plus_seven) == '33' or str(day_plus_seven) == '34' or str(day_plus_seven) == '35' or str(day_plus_seven) == '36' or str(day_plus_seven) == '37' or str(day_plus_seven) == '38':
        day_plus_seven = '1'
        month_plus_one = int(date_from_list[0].split('-')[1]) + 1
        date_plus_seven_day = date_from_list[0].split('-')[0] + '-' + str(month_plus_one).zfill(2) + '-' + str(
            day_plus_seven).zfill(
            2)
    return date_plus_one_day, date_plus_seven_day


@bot.message_handler(commands=['reset'])
def reset(message):
    try:
        utility.pop(str(message.chat.id) + 'place_code')
        utility.pop(str(message.chat.id) + 'date_from')
        utility.pop(str(message.chat.id) + 'date_to')
        utility.pop(str(message.chat.id) + 'trip_purpose')
    except KeyError:
        pass
    bot.send_message(message.chat.id, 'Бот готовий до повторного використання')


@bot.message_handler(commands=['help'])
def help(message):
    bot.send_message(message.chat.id, 'Зверніться до служби підтримки')


@bot.message_handler(commands=['rules'])
def rules(message):
    bot.send_message(message.chat.id, 'Правила використання')


@bot.message_handler(commands=['start'])
def hello(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    button1 = types.KeyboardButton('Оформити страхування')
    markup.add(button1)
    bot.send_message(message.chat.id,
                     'Добридень {0.first_name}, вас вітає бот для оформлення страхування для ваших подорожей - {1.first_name}🚘'.format(
                         message.from_user, bot.get_me()), reply_markup=markup)
    utility = {str(message.chat.id) + 'place_code': '',
               str(message.chat.id) + 'date_from': '',
               str(message.chat.id) + 'date_to': '',
               str(message.chat.id) + 'trip_purpose': ''}


@bot.message_handler(func=lambda message: message.text == 'Оформити страхування')
def beggining(message):
    r = requests.get('https://web.ewa.ua/ewa/api/v10/territory/countries', headers=headers, cookies=cookies)
    print(r.json())
    markup = types.InlineKeyboardMarkup()
    button = types.InlineKeyboardButton(text='Увесь світ', callback_data='273')
    button1 = types.InlineKeyboardButton(text='Європа', callback_data='272')
    markup.add(button, button1)
    # 273 World
    # 272 Europe
    bot.send_message(message.chat.id, 'Куди ви збираєтесь поїхати?✈', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if str(call.data) == '273':
        utility.update({str(call.message.chat.id) + 'place_code': str(call.data)})
    if str(call.data) == '272':
        utility.update({str(call.message.chat.id) + 'place_code': str(call.data)})
    date_example = date_plus_day(call.message)
    bot.send_message(call.message.chat.id,
                     f'Добре! Теперь скажіть будь ласка дату виліту🖊 Дата повинна бути у форматі {date_example[0]}')
    dbworker.set_state(call.message.chat.id, config.States.S_ASKING_DATE_TO.value)


@bot.message_handler(
    func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S_ASKING_DATE_TO.value)
def date_to(message):
    date_from = message.text
    utility.update({str(message.chat.id) + 'date_from': date_from})
    date_example = date_plus_day(message)
    bot.send_message(message.chat.id,
                     f'Запам\'ятаю, теперь скажіть дату повернення🏠 Усе у тому ж форматі {date_example[1]}')
    dbworker.set_state(message.chat.id, config.States.S_ASKING_DATE_FROM.value)


@bot.message_handler(
    func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S_ASKING_DATE_FROM.value)
def date_from(message):
    date_to = message.text
    utility.update({str(message.chat.id) + 'date_to': date_to})
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    button1 = types.KeyboardButton('Навчання🎓')
    button2 = types.KeyboardButton('Туризм📸')
    button3 = types.KeyboardButton('Спорт⚽')
    button4 = types.KeyboardButton('Активний туризм🏄')
    button5 = types.KeyboardButton('Екстремальний туризм🎿')
    button6 = types.KeyboardButton('Професіональний спорт🥇')
    button7 = types.KeyboardButton('Робота💼')
    button8 = types.KeyboardButton('Небезпечна робота⛑')
    markup.add(button1, button2, button3, button4, button5, button6, button7, button8)
    bot.send_message(message.chat.id, 'Вкажіть будь ласка ціль вашої поїздки:\nНавчання🎓\nТуризм📸\nСпорт⚽\nАктивний туризм🏄\nЕкстремальний туризм🎿\nПрофесіональний спорт🥇\nРобота💼\nНебезпечна робота⛑', reply_markup=markup)
    dbworker.set_state(message.chat.id, config.States.S_GETTING_TARGET.value)


@bot.message_handler(
    func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S_GETTING_TARGET.value)
def getting_target(message):
    if message.text == 'Навчання🎓':
        trip_purpose = 'study'
    if message.text == 'Туризм📸':
        trip_purpose = 'tourism'
    if message.text == 'Спорт⚽':
        trip_purpose = 'sport'
    if message.text == 'Активний туризм🏄':
        trip_purpose = 'active_sport'
    if message.text == 'Екстремальний туризм🎿':
        trip_purpose = 'extrim'
    if message.text == 'Професіональний спорт🥇':
        trip_purpose = 'prof_sport'
    if message.text == 'Робота💼':
        trip_purpose = 'work'
    if message.text == 'Небезпечна робота⛑':
        trip_purpose = 'danger_work'
    utility.update({str(message.chat.id) + 'trip_purpose': trip_purpose})
    data = {
        'multivisa': False,
        'coverageFrom': utility.get(str(message.chat.id) + 'date_from'),
        'coverageTo': utility.get(str(message.chat.id) + 'date_to'),
        # 'coverageDays':
    }




# BOT RUNNING
if __name__ == '__main__':
    bot.polling(none_stop=True)
