import config
import telebot
from telebot import types
import requests
import dbworker
import json
import random
import datetime
import sqlite3 as sql
import inline_calendar

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
# connection = sql.connect('DATABASE.sqlite')
# q = connection.cursor()
# q.execute('''
# 			CREATE TABLE "user" (
# 				'id' TEXT,
# 				'surname' TEXT,
# 				'name' TEXT,
# 				'date_of_birth' TEXT,
# 				'address' TEXT,
# 				'email' TEXT,
# 				'phone' TEXT
# 			)''')
# connection.commit()
# q.close()
# connection.close()
#
# connection = sql.connect('DATABASE.sqlite')
# q = connection.cursor()
# q.execute('''
# 			CREATE TABLE "passport" (
# 			    'id' TEXT,
# 			    'series' TEXT,
# 			    'number' TEXT,
# 			    'date' TEXT,
# 			    'issued_by' TEXT
# 			)''')
# connection.commit()
# q.close()
# connection.close()
# CONSTANTS
customer_category = 'NATURAL'
utility = {}


def log(message):
    print("<!------!>")
    print(datetime.datetime.now())
    print("Сообщение от {0} {1} (id = {2}) \n {3}".format(message.from_user.first_name,
                                                          message.from_user.last_name,
                                                          str(message.from_user.id), message.text))


def tariff_parsing(tariff):
    name = tariff['tariff']['name']
    insurer = tariff['tariff']['insurer']['namePrint']
    id = tariff['tariff']['id']
    payment = tariff['payment']
    discounted_payment = tariff['discountedPayment']
    risk_amount = tariff['risks'][0]['amount']
    print('Risk amount:  ' + str(risk_amount))
    markup = types.InlineKeyboardMarkup()
    button = types.InlineKeyboardButton(text='Оформити', callback_data=id)
    markup.add(button)
    return insurer, name, id, payment, discounted_payment, markup, risk_amount


def date_plus_day(message):
    date_raw = message.date
    date_from = datetime.datetime.fromtimestamp(int(date_raw)).strftime('%Y-%m-%d %H:%M:%S')
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
        date_plus_one_day = date_from_list[0].split('-')[0] + '-' + str(month_plus_one).zfill(2) + '-' + str(
            day_plus_one).zfill(
            2)
    if str(day_plus_seven) == '32' or str(day_plus_seven) == '31' or str(day_plus_seven) == '33' or str(
            day_plus_seven) == '34' or str(day_plus_seven) == '35' or str(day_plus_seven) == '36' or str(
        day_plus_seven) == '37' or str(day_plus_seven) == '38':
        day_plus_seven = '1'
        month_plus_one = int(date_from_list[0].split('-')[1]) + 1
        date_plus_seven_day = date_from_list[0].split('-')[0] + '-' + str(month_plus_one).zfill(2) + '-' + str(
            day_plus_seven).zfill(
            2)
    return date_plus_one_day, date_plus_seven_day


@bot.callback_query_handler(func=inline_calendar.is_inline_calendar_callbackquery)
def calendar_callback_handler(q: types.CallbackQuery):
    if utility.get(str(q.from_user.id) + 'date_from_check') == '1':
        bot.answer_callback_query(q.id)
        try:
            return_data = inline_calendar.handler_callback(q.from_user.id, q.data)
            if return_data is None:
                bot.edit_message_reply_markup(chat_id=q.from_user.id, message_id=q.message.message_id,
                                              reply_markup=inline_calendar.get_keyboard(q.from_user.id))
            else:
                picked_data = return_data
                print(picked_data)
                bot.edit_message_text(text=picked_data, chat_id=q.from_user.id, message_id=q.message.message_id,
                                      reply_markup=inline_calendar.get_keyboard(q.from_user.id))
                utility.update({str(q.from_user.id) + 'date_from': picked_data})
                bot.send_message(q.from_user.id, 'Запам\'ятаю, теперь скажіть дату повернення🏠')
                inline_calendar.init(q.from_user.id,
                                     datetime.date.today(),
                                     datetime.date.today(),
                                     datetime.date.today() + datetime.timedelta(days=365))
                bot.send_message(q.from_user.id, text='Обрана дата',
                                 reply_markup=inline_calendar.get_keyboard(q.from_user.id))
                utility.update({str(q.from_user.id) + 'date_to_check': '1'})
                utility.update({str(q.from_user.id) + 'date_from_check': '0'})
        except inline_calendar.WrongChoiceCallbackException:
            bot.edit_message_text(text='Неправильний вибір', chat_id=q.from_user.id, message_id=q.message.message_id,
                                  reply_markup=inline_calendar.get_keyboard(q.from_user.id))
    if utility.get(str(q.from_user.id) + 'date_to_check') == '1':
        bot.answer_callback_query(q.id)
        try:
            return_data = inline_calendar.handler_callback(q.from_user.id, q.data)
            if return_data is None:
                bot.edit_message_reply_markup(chat_id=q.from_user.id, message_id=q.message.message_id,
                                              reply_markup=inline_calendar.get_keyboard(q.from_user.id))
            else:
                picked_data = return_data
                print(picked_data)
                utility.update({str(q.from_user.id) + 'date_to': picked_data})
                bot.edit_message_text(text=picked_data, chat_id=q.from_user.id, message_id=q.message.message_id,
                                      reply_markup=inline_calendar.get_keyboard(q.from_user.id))
                asking_target(q)

        except inline_calendar.WrongChoiceCallbackException:
            bot.edit_message_text(text='Неправильний вибір', chat_id=q.from_user.id, message_id=q.message.message_id,
                                  reply_markup=inline_calendar.get_keyboard(q.from_user.id))


@bot.message_handler(commands=['reset'])
def reset(message):
    try:
        utility.pop(str(message.chat.id) + 'place_code')
        utility.pop(str(message.chat.id) + 'date_from')
        utility.pop(str(message.chat.id) + 'date_from_check')
        utility.pop(str(message.chat.id) + 'date_to')
        utility.pop(str(message.chat.id) + 'date_to_check')
        utility.pop(str(message.chat.id) + 'trip_purpose')
        utility.pop(str(message.chat.id) + 'tariff1')
        utility.pop(str(message.chat.id) + 'tariff2')
        utility.pop(str(message.chat.id) + 'tariff3')
        utility.pop(str(message.chat.id) + 'tariff4')
        utility.pop(str(message.chat.id) + 'tariff5')
        utility.pop(str(message.chat.id) + 'tariff_risk_amount')
        utility.pop(str(message.chat.id) + 'tariff_name')
        utility.pop(str(message.chat.id) + 'contract_id')
        utility.pop(str(message.chat.id) + 'tariff_payment')
        utility.pop(str(message.chat.id) + 'tariff_discounted_payment')
        utility.pop(str(message.chat.id) + 'order')
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
    connection = sql.connect('DATABASE.sqlite')
    q = connection.cursor()
    q.execute("INSERT INTO 'user' (id) VALUES ('%s')" % message.from_user.id)
    connection.commit()
    q.close()
    connection.close()
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    button1 = types.KeyboardButton('Оформити страхування')
    markup.add(button1)
    bot.send_message(message.chat.id,
                     'Добридень {0.first_name}, вас вітає бот для оформлення страхування для ваших подорожей-{1.first_name}✈\nДля введення деяких даних буде потрібний закордонний паспорт📖\nПриготуйте його заздалегідь☝'.format(
                         message.from_user, bot.get_me()), reply_markup=markup)
    utility = {str(message.chat.id) + 'place_code': '',
               str(message.chat.id) + 'date_from': '',
               str(message.chat.id) + 'date_from_check': '',
               str(message.chat.id) + 'date_to': '',
               str(message.chat.id) + 'date_to_check': '',
               str(message.chat.id) + 'trip_purpose': '',
               str(message.chat.id) + 'tariff1': '',
               str(message.chat.id) + 'tariff2': '',
               str(message.chat.id) + 'tariff3': '',
               str(message.chat.id) + 'tariff4': '',
               str(message.chat.id) + 'tariff5': '',
               str(message.chat.id) + 'tariff_name': '',
               str(message.chat.id) + 'tariff_risk_amount': '',
               str(message.chat.id) + 'contract_id': '',
               str(message.chat.id) + 'tariff_payment': '',
               str(message.chat.id) + 'tariff_discounted_payment': '',
               str(message.chat.id) + 'order': ''
               }


@bot.message_handler(func=lambda message: message.text == 'Оформити страхування')
def beggining(message):
    r = requests.get('https://web.ewa.ua/ewa/api/v10/territory/countries', headers=headers, cookies=cookies)
    markup = types.InlineKeyboardMarkup()
    button = types.InlineKeyboardButton(text='Увесь світ🌍', callback_data='273')
    button1 = types.InlineKeyboardButton(text='Європа🇪🇺', callback_data='272')
    markup.add(button, button1)
    # 273 World
    # 272 Europe
    bot.send_message(message.chat.id, 'Куди ви збираєтесь поїхати?✈', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    print(call.data)
    if str(call.data) == '273':
        utility.update({str(call.message.chat.id) + 'place_code': str(call.data)})
        date_example = date_plus_day(call.message)
        bot.send_message(call.message.chat.id,
                         f'Добре! Теперь скажіть будь ласка дату виліту🖊 Дата повинна бути у форматі {date_example[0]}')
        inline_calendar.init(call.message.chat.id,
                             datetime.date.today(),
                             datetime.date.today(),
                             datetime.date.today() + datetime.timedelta(days=365))
        bot.send_message(call.message.chat.id, text='Обрана дата',
                         reply_markup=inline_calendar.get_keyboard(call.message.chat.id))
        utility.update({str(call.message.chat.id) + 'date_from_check': '1'})
    if str(call.data) == '272':
        utility.update({str(call.message.chat.id) + 'place_code': str(call.data)})
        date_example = date_plus_day(call.message)
        bot.send_message(call.message.chat.id,
                         f'Добре! Теперь скажіть будь ласка дату виліту🖊 Дата повинна бути у форматі {date_example[0]}')
        inline_calendar.init(call.message.chat.id,
                             datetime.date.today(),
                             datetime.date.today(),
                             datetime.date.today() + datetime.timedelta(days=365))
        bot.send_message(call.message.chat.id, text='Обрана дата',
                         reply_markup=inline_calendar.get_keyboard(call.message.chat.id))
        utility.update({str(call.message.chat.id) + 'date_from_check': '1'})
    try:
        if int(call.data) == utility.get(str(call.message.chat.id) + 'tariff1')[2]:
            print('Callback accepted1')
            utility.update({str(call.message.chat.id) + 'tariff_risk_amount':
                                utility.get(str(call.message.chat.id) + 'tariff1')[6]})
            utility.update(
                {str(call.message.chat.id) + 'tariff_payment': utility.get(str(call.message.chat.id) + 'tariff1')[3]})
            utility.update(
                {str(call.message.chat.id) + 'tariff_name': utility.get(str(call.message.chat.id) + 'tariff1')[1]})
            bot.send_message(call.message.chat.id,
                             'Гарний вибір! Зараз вам знадобиться ваш закородонний паспорт.\nНапишіть ваше ім\'я (латинськими літерами)✍')
            dbworker.set_state(call.message.chat.id, config.States.S_NAME_INPUT.value)
        if int(call.data) == utility.get(str(call.message.chat.id) + 'tariff2')[2]:
            print('Callback accepted2')
            utility.update({str(call.message.chat.id) + 'tariff_risk_amount':
                                utility.get(str(call.message.chat.id) + 'tariff2')[6]})
            utility.update(
                {str(call.message.chat.id) + 'tariff_payment': utility.get(str(call.message.chat.id) + 'tariff2')[3]})
            utility.update(
                {str(call.message.chat.id) + 'tariff_name': utility.get(str(call.message.chat.id) + 'tariff2')[1]})
            bot.send_message(call.message.chat.id,
                             'Гарний вибір! Зараз вам знадобиться ваш закородонний паспорт.\nНапишіть ваше ім\'я (латинськими літерами)✍')
            dbworker.set_state(call.message.chat.id, config.States.S_NAME_INPUT.value)
        if int(call.data) == utility.get(str(call.message.chat.id) + 'tariff3')[2]:
            print('Callback accepted3')
            utility.update({str(call.message.chat.id) + 'tariff_risk_amount':
                                utility.get(str(call.message.chat.id) + 'tariff3')[6]})
            utility.update(
                {str(call.message.chat.id) + 'tariff_payment': utility.get(str(call.message.chat.id) + 'tariff3')[3]})
            utility.update(
                {str(call.message.chat.id) + 'tariff_name': utility.get(str(call.message.chat.id) + 'tariff3')[1]})
            bot.send_message(call.message.chat.id,
                             'Гарний вибір! Зараз вам знадобиться ваш закородонний паспорт.\nНапишіть ваше ім\'я (латинськими літерами)✍')
            dbworker.set_state(call.message.chat.id, config.States.S_NAME_INPUT.value)
        if int(call.data) == utility.get(str(call.message.chat.id) + 'tariff4')[2]:
            print('Callback accepted4')
            utility.update({str(call.message.chat.id) + 'tariff_risk_amount':
                                utility.get(str(call.message.chat.id) + 'tariff4')[6]})
            utility.update(
                {str(call.message.chat.id) + 'tariff_payment': utility.get(str(call.message.chat.id) + 'tariff4')[3]})
            utility.update(
                {str(call.message.chat.id) + 'tariff_name': utility.get(str(call.message.chat.id) + 'tariff4')[1]})
            bot.send_message(call.message.chat.id,
                             'Гарний вибір! Зараз вам знадобиться ваш закородонний паспорт.\nНапишіть ваше ім\'я (латинськими літерами)✍')
            dbworker.set_state(call.message.chat.id, config.States.S_NAME_INPUT.value)
        if int(call.data) == utility.get(str(call.message.chat.id) + 'tariff5')[2]:
            print('Callback accepted5')
            utility.update({str(call.message.chat.id) + 'tariff_risk_amount':
                                utility.get(str(call.message.chat.id) + 'tariff5')[6]})
            utility.update(
                {str(call.message.chat.id) + 'tariff_payment': utility.get(str(call.message.chat.id) + 'tariff5')[3]})
            utility.update(
                {str(call.message.chat.id) + 'tariff_name': utility.get(str(call.message.chat.id) + 'tariff5')[1]})
            bot.send_message(call.message.chat.id,
                             'Гарний вибір! Зараз вам знадобиться ваш закородонний паспорт.\nНапишіть ваше ім\'я (латинськими літерами)✍')
            dbworker.set_state(call.message.chat.id, config.States.S_NAME_INPUT.value)
    except TypeError:
        pass


@bot.message_handler(
    func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S_ASKING_DATE_FROM.value)
def asking_target(message):
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
    bot.send_message(message.from_user.id,
                     'Вкажіть будь ласка ціль вашої поїздки:\nНавчання🎓\nТуризм📸\nСпорт⚽\nАктивний туризм🏄\nЕкстремальний туризм🎿\nПрофесіональний спорт🥇\nРобота💼\nНебезпечна робота⛑',
                     reply_markup=markup)
    dbworker.set_state(message.from_user.id, config.States.S_GETTING_TARGET.value)


@bot.message_handler(
    func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S_GETTING_TARGET.value)
def getting_target(message):
    if message.text == 'Навчання🎓':
        trip_purpose = 'study'
        utility.update({str(message.chat.id) + 'trip_purpose': trip_purpose})
        birth_date(message)
    if message.text == 'Туризм📸':
        trip_purpose = 'tourism'
        utility.update({str(message.chat.id) + 'trip_purpose': trip_purpose})
        birth_date(message)
    if message.text == 'Спорт⚽':
        trip_purpose = 'sport'
        utility.update({str(message.chat.id) + 'trip_purpose': trip_purpose})
        birth_date(message)
    if message.text == 'Активний туризм🏄':
        trip_purpose = 'active_sport'
        utility.update({str(message.chat.id) + 'trip_purpose': trip_purpose})
        birth_date(message)
    if message.text == 'Екстремальний туризм🎿':
        trip_purpose = 'extrim'
        utility.update({str(message.chat.id) + 'trip_purpose': trip_purpose})
        birth_date(message)
    if message.text == 'Професіональний спорт🥇':
        trip_purpose = 'prof_sport'
        utility.update({str(message.chat.id) + 'trip_purpose': trip_purpose})
        birth_date(message)
    if message.text == 'Робота💼':
        trip_purpose = 'work'
        utility.update({str(message.chat.id) + 'trip_purpose': trip_purpose})
        birth_date(message)
    if message.text == 'Небезпечна робота⛑':
        trip_purpose = 'danger_work'
        utility.update({str(message.chat.id) + 'trip_purpose': trip_purpose})
        birth_date(message)


@bot.message_handler(
    func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S_BIRTH_DATE.value)
def birth_date(message):
    bot.send_message(message.chat.id,
                     'Тепер введіть свій день народження🎂 Усе у тому ж форматі РРРР-ММ-ДД.\nНаприклад 1991-09-18')
    dbworker.set_state(message.chat.id, config.States.S_GETTING_BIRTH_DATE.value)


@bot.message_handler(
    func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S_GETTING_BIRTH_DATE.value)
def getting_birth_date(message):
    date_of_birth = message.text
    connection = sql.connect('DATABASE.sqlite')
    q = connection.cursor()
    q.execute("UPDATE user SET date_of_birth='%s' WHERE id='%s'" % (date_of_birth, message.from_user.id))
    connection.commit()
    q.close()
    connection.close()
    connection = sql.connect('DATABASE.sqlite')
    q = connection.cursor()
    q.execute("SELECT * from user WHERE id='%s'" % message.from_user.id)
    dob = q.fetchall()
    connection.commit()
    q.close()
    connection.close()
    bot.send_message(message.chat.id, 'Відмінно! Ось доступні вам тарифи🔽')
    print((datetime.datetime.strptime(str(utility.get(str(message.chat.id) + 'date_to')),
                                      '%Y-%m-%d').date() - datetime.datetime.strptime(
        str(utility.get(str(message.chat.id) + 'date_from')), '%Y-%m-%d').date()).days)
    data = {
        'multivisa': 'false',
        'coverageFrom': str(utility.get(str(message.chat.id) + 'date_from')),
        'coverageTo': str(utility.get(str(message.chat.id) + 'date_to')),
        'coverageDays': str((datetime.datetime.strptime(str(utility.get(str(message.chat.id) + 'date_to')),
                                                        '%Y-%m-%d').date() - datetime.datetime.strptime(
            str(utility.get(str(message.chat.id) + 'date_from')), '%Y-%m-%d').date()).days),
        'country': utility.get(str(message.chat.id) + 'place_code'),
        'risks': [
            {'risk': 1,
             'inCurrency': 'true'}
        ],
        'birthDays': [dob[0][3]],
        'simplified': 'true',
        'tripPurpose': utility.get(str(message.chat.id) + 'trip_purpose'),
        'salePoint': sale_point,
        'customerCategory': customer_category
    }
    json_string = json.dumps(data)
    r = requests.post('https://web.ewa.ua/ewa/api/v10/tariff/choose/tourism', headers=headers, cookies=cookies,
                      data=json_string)
    print(r)
    print(r.json())
    try:
        tariff1 = tariff_parsing(r.json()[0])
        tariff2 = tariff_parsing(r.json()[1])
        tariff3 = tariff_parsing(r.json()[2])
        tariff4 = tariff_parsing(r.json()[3])
        tariff5 = tariff_parsing(r.json()[4])
    except IndexError:
        pass
    try:
        utility.update({str(message.chat.id) + 'tariff1': tariff1})
        utility.update({str(message.chat.id) + 'tariff2': tariff2})
        utility.update({str(message.chat.id) + 'tariff3': tariff3})
        utility.update({str(message.chat.id) + 'tariff4': tariff4})
        utility.update({str(message.chat.id) + 'tariff5': tariff5})
    except:
        pass
    try:
        bot.send_message(message.chat.id,
                         f'👔 Страховик: {utility.get(str(message.chat.id) + "tariff5")[0]}\n💼 Назва: {utility.get(str(message.chat.id) + "tariff5")[1]}\n💵 Вартість: {utility.get(str(message.chat.id) + "tariff5")[3]}',
                         reply_markup=utility.get(str(message.chat.id) + "tariff5")[5])
    except TypeError:
        pass
    try:
        bot.send_message(message.chat.id,
                         f'👔 Страховик: {utility.get(str(message.chat.id) + "tariff4")[0]}\n💼 Назва: {utility.get(str(message.chat.id) + "tariff4")[1]}\n💵 Вартість: {utility.get(str(message.chat.id) + "tariff4")[3]}',
                         reply_markup=utility.get(str(message.chat.id) + "tariff4")[5])
    except TypeError:
        pass
    try:
        bot.send_message(message.chat.id,
                         f'👔 Страховик: {utility.get(str(message.chat.id) + "tariff3")[0]}\n💼 Назва: {utility.get(str(message.chat.id) + "tariff3")[1]}\n💵 Вартість: {utility.get(str(message.chat.id) + "tariff3")[3]}',
                         reply_markup=utility.get(str(message.chat.id) + "tariff3")[5])
    except TypeError:
        pass
    try:
        bot.send_message(message.chat.id,
                         f'👔 Страховик: {utility.get(str(message.chat.id) + "tariff2")[0]}\n💼 Назва: {utility.get(str(message.chat.id) + "tariff2")[1]}\n💵 Вартість: {utility.get(str(message.chat.id) + "tariff2")[3]}',
                         reply_markup=utility.get(str(message.chat.id) + "tariff2")[5])
    except TypeError:
        pass
    try:
        bot.send_message(message.chat.id,
                         f'👔Страховик: {utility.get(str(message.chat.id) + "tariff1")[0]}\n💼 Назва: {utility.get(str(message.chat.id) + "tariff1")[1]}\n💵 Вартість: {utility.get(str(message.chat.id) + "tariff1")[3]}',
                         reply_markup=utility.get(str(message.chat.id) + "tariff1")[5])
    except TypeError:
        pass


@bot.message_handler(
    func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S_NAME_INPUT.value)
def name_input(message):
    name = message.text
    connection = sql.connect('DATABASE.sqlite')
    q = connection.cursor()
    q.execute("UPDATE user SET name='%s' WHERE id='%s'" % (name, message.from_user.id))
    connection.commit()
    q.close()
    connection.close()
    bot.send_message(message.chat.id, 'Введіть вашу фамілію (латинськими літерам)✍')
    dbworker.set_state(message.chat.id, config.States.S_SURNAME_INPUT.value)


@bot.message_handler(
    func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S_SURNAME_INPUT.value)
def name_input(message):
    surname = message.text
    connection = sql.connect('DATABASE.sqlite')
    q = connection.cursor()
    q.execute("UPDATE user SET surname='%s' WHERE id='%s'" % (surname, message.from_user.id))
    connection.commit()
    q.close()
    connection.close()
    bot.send_message(message.chat.id, 'Вашу поточну адресу проживання (у форматі місто, вулиця, дім, квартира)✍')
    dbworker.set_state(message.chat.id, config.States.S_ADDRESS.value)


@bot.message_handler(
    func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S_ADDRESS.value)
def address_input(message):
    address = message.text
    connection = sql.connect('DATABASE.sqlite')
    q = connection.cursor()
    q.execute("UPDATE user SET address='%s' WHERE id='%s'" % (address, message.from_user.id))
    connection.commit()
    q.close()
    connection.close()
    bot.send_message(message.chat.id, 'Введіть ваш номер телефону✍')
    dbworker.set_state(message.chat.id, config.States.S_PHONE.value)


@bot.message_handler(
    func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S_PHONE.value)
def phone_input(message):
    phone = message.text
    connection = sql.connect('DATABASE.sqlite')
    q = connection.cursor()
    q.execute("UPDATE user SET phone='%s' WHERE id='%s'" % (phone, message.from_user.id))
    connection.commit()
    q.close()
    connection.close()
    bot.send_message(message.chat.id, 'Тепер введіть вашу електронну пошту (сюди буде відправлений поліс)✍')
    dbworker.set_state(message.chat.id, config.States.S_EMAIL.value)


@bot.message_handler(
    func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S_EMAIL.value)
def email_input(message):
    email = message.text
    connection = sql.connect('DATABASE.sqlite')
    q = connection.cursor()
    q.execute("UPDATE user SET email='%s' WHERE id='%s'" % (email, message.from_user.id))
    connection.commit()
    q.close()
    connection.close()
    bot.send_message(message.chat.id, 'Тепер введіть серію вашого закордонника✍')
    dbworker.set_state(message.chat.id, config.States.S_SERIES.value)


@bot.message_handler(
    func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S_SERIES.value)
def series_input(message):
    series = message.text
    connection = sql.connect('DATABASE.sqlite')
    q = connection.cursor()
    q.execute("SELECT EXISTS(SELECT 1 FROM passport WHERE id='%s')" % message.from_user.id)
    results1 = q.fetchone()
    if results1[0] != 1:
        q.execute("INSERT INTO 'passport' (id) VALUES ('%s')" % message.from_user.id)
    q.execute("UPDATE passport SET series='%s' WHERE id='%s'" % (series, message.from_user.id))
    connection.commit()
    q.close()
    connection.close()
    bot.send_message(message.chat.id, 'Введіть номер закордонного паспорта✍')
    dbworker.set_state(message.chat.id, config.States.S_NUMBER.value)


@bot.message_handler(func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S_NUMBER.value)
def number_taking(message):
    number = message.text
    # if len(number) != 6:
    #     bot.send_message(message.chat.id, 'Номер паспорта має містити 6 цифр. Спробуйте ще')
    #     dbworker.set_state(message.chat.id, config.States.S_NUMBER.value)
    # else:
    connection = sql.connect('DATABASE.sqlite')
    q = connection.cursor()
    q.execute("UPDATE passport SET number='%s' WHERE id='%s'" % (number, message.from_user.id))
    connection.commit()
    q.close()
    connection.close()
    prefinal(message)


def prefinal(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    button1 = types.KeyboardButton('Так✔')
    button2 = types.KeyboardButton('Змінити✖')
    button3 = types.KeyboardButton('Спочатку🔄')
    markup.add(button1, button2, button3)
    bot.send_message(message.chat.id, 'Відмінно! Перевірте правильність введених даних.')
    connection = sql.connect('DATABASE.sqlite')
    q = connection.cursor()
    q.execute("SELECT * from user WHERE id='%s'" % message.from_user.id)
    results = q.fetchall()
    q.execute("SELECT * from passport WHERE id='%s'" % message.from_user.id)
    results1 = q.fetchall()
    connection.commit()
    q.close()
    connection.close()
    try:
        surname = results[0][1]
    except IndexError:
        surname = ''
    try:
        name = results[0][2]
    except IndexError:
        name = ''
    try:
        birth = results[0][3]
    except IndexError:
        birth = ''
    try:
        reg_addres = results[0][4]
    except IndexError:
        reg_addres = ''
    try:
        email = results[0][5]
    except IndexError:
        email = ''
    try:
        phone = results[0][6]
    except IndexError:
        phone = ''
    try:
        series = results1[0][1]
    except IndexError:
        series = ''
    try:
        doc_num = results1[0][2]
    except IndexError:
        doc_num = ''
    if str(utility.get(str(message.chat.id) + 'place_code')) == '273':
        place = 'Увесь світ🌍'
    else:
        place = 'Європа🇪🇺'
    coverage = str((datetime.datetime.strptime(str(utility.get(str(message.chat.id) + 'date_to')),
                                               '%Y-%m-%d').date() - datetime.datetime.strptime(
        str(utility.get(str(message.chat.id) + 'date_from')), '%Y-%m-%d').date()).days)
    bot.send_message(message.chat.id,
                     f"Дані про подорож✈\n\nМісце:  {place}\nДата виліту: {utility.get(str(message.chat.id) + 'date_from')}\nДата повернення:{utility.get(str(message.chat.id) + 'date_to')}\nКількість дней покриття: {coverage}\nЦіль поїздки: {utility.get(str(message.chat.id) + 'trip_purpose')}\n\nВаша особиста інформація😉\n\nПрізвище:  {surname}\nІм'я:  {name}\nДата народждения:  {birth}\nАдреса реєстрації:  {reg_addres}\nEMAIL:  {email}\nТелефон:  {phone}\n\nДані вашого документа📖\n\nСерія/Запис документа:  {series}\nНомер документа:  {doc_num}",
                     reply_markup=markup)
    dbworker.clear_db(message.chat.id)


@bot.message_handler(func=lambda message: message.text == 'Спочатку🔄')
def again(message):
    beggining(message)


@bot.message_handler(func=lambda message: message.text == 'Так✔')
def yes(message):
    connection = sql.connect('DATABASE.sqlite')
    q = connection.cursor()
    q.execute("SELECT * from user WHERE id='%s'" % message.from_user.id)
    results = q.fetchall()
    q.execute("SELECT * from passport WHERE id='%s'" % message.from_user.id)
    results1 = q.fetchall()
    print(results1)
    connection.commit()
    q.close()
    connection.close()
    bot.send_message(message.chat.id, 'Добре!👍\nПереходжу до формування договору📝\nЗачекайте⏳',
                     reply_markup=types.ReplyKeyboardRemove())
    print('Risk amount:' + str(utility.get(str(message.chat.id) + 'tariff_risk_amount')))
    contract_data = {
        'type': 'tourism',
        'salePoint': {
            'id': sale_point
        },
        'user': {
            'id': user
        },
        'tariff': {
            'type': 'tourism',
            'id': utility.get(str(message.chat.id) + 'tariff1')[2]
        },
        'date': str(datetime.datetime.fromtimestamp(int(message.date)).strftime('%Y-%m-%d')),
        'dateFrom': str(utility.get(str(message.chat.id) + 'date_from')) + 'T00:00:00.000+0000',
        'coverageDays': str((datetime.datetime.strptime(str(utility.get(str(message.chat.id) + 'date_to')),
                                                        '%Y-%m-%d').date() - datetime.datetime.strptime(
            str(utility.get(str(message.chat.id) + 'date_from')), '%Y-%m-%d').date()).days),
        'customer': {
            'dontHaveCode': 'true',
            'nameLast': results[0][1],
            'nameFirst': results[0][2],
            'address': results[0][4],
            'phone': results[0][6],
            'email': results[0][5],
            'birthDate': results[0][3],
            'document': {
                'type': 'EXTERNAL_PASSPORT',
                'series': results1[0][1],
                'number': results1[0][2]
            },
            'legal': 'true'
        },
        'insuranceObject': {
            'type': 'person',
            'document': {
                'type': 'EXTERNAL_PASSPORT',
                'series': results1[0][1],
                'number': results1[0][2]
            },
            'address': results[0][4],
            'email': results[0][5],
            'dontHaveCode': 'true',
            'nameLast': results[0][1],
            'nameFirst': results[0][2],
            'birthDate': results[0][3],
            'phone': results[0][6]
        },
        'risks': [
            {'risk': {'id': 1},
             'insuranceAmount': utility.get(str(message.chat.id) + 'tariff_risk_amount')}
        ],
        'customFields': [
            {'code': 'program_of_trip',
             'value': 'econom'},
            {'code': 'purpose_of_trip',
             'value': utility.get(str(message.chat.id) + 'trip_purpose')}
        ],
        'state': 'DRAFT',
        'multiObject': 'false',
        'multivisa': 'false',
        'country': {
            'id': utility.get(str(message.chat.id) + 'place_code')
        }
    }
    print(contract_data)
    url_for_save_contract = 'https://web.ewa.ua/ewa/api/v10/contract/save'
    json_string = json.dumps(contract_data)
    r = requests.post(url_for_save_contract, headers=headers, cookies=cookies,
                      data=json_string)  # Перевод договора в состояние ЧЕРНОВИК
    print(r)
    print(r.json())
    bad_data = 0
    try:
        id_contract = r.json()['id']
        utility.update({str(message.chat.id) + 'contract_id': id_contract})
    except KeyError:
        print('Какое-то из значений было введено неправильно')
        bot.send_message(message.chat.id, 'Якісь дані були введені некоректно. Спробуйте ще')
        bad_data = 1
    if bad_data == 1:
        prefinal(message)
    else:
        contract = utility.get(str(message.chat.id) + 'contract_id')
        # print(contract)
        # url_for_req = f'https://web.ewa.ua/ewa/api/v10/contract/{contract}/state/REQUEST'
        # print(url_for_req)
        # r1 = requests.post(url_for_req, headers=headers, cookies=cookies)  # перевод договора в состояние ЗАЯВЛЕН
        # print(r1)
        # print(r1.reason)
        url_for_otp = f'https://web.ewa.ua/ewa/api/v10/contract/{contract}/otp/send?customer=true'
        r_otp = requests.get(url_for_otp, headers=headers, cookies=cookies)
        print(r_otp)
        bot.send_message(message.chat.id,
                         '📲На ваш мобільний телефон було відправлено СМС з паролем для підпису електронного полісу.\n\nВведіть пароль з повідомлення✍')
        dbworker.set_state(message.chat.id, config.States.S_OTP.value)


@bot.message_handler(func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S_OTP.value)
def otp(message):
    otp = message.text
    contract = utility.get(str(message.chat.id) + 'contract_id')
    url_otp_2 = f'https://web.ewa.ua/ewa/api/v9/contract/{contract}/otp?customer={otp}'
    r_otp_2 = requests.get(url_otp_2, headers=headers, cookies=cookies)
    print(r_otp_2)
    connection = sql.connect('DATABASE.sqlite')
    q = connection.cursor()
    q.execute("SELECT * from user WHERE id='%s'" % message.from_user.id)
    results = q.fetchall()
    connection.commit()
    q.close()
    connection.close()
    random_integer = random.randint(10000, 99999)
    payment = utility.get(str(message.chat.id) + 'tariff_payment')
    product_name = f"ТУРИЗМ від - {utility.get(str(message.chat.id) + 'tariff_name')}"
    order = f'order{str(random_integer)}'
    amount = round(payment * 100.)
    bot.send_invoice(message.chat.id,
                     title=product_name,
                     description='Страховий поліс ТУРИЗМ',
                     invoice_payload=order,
                     provider_token=config.liqpay_token,
                     currency='UAH',
                     prices=[types.LabeledPrice(label='Полис', amount=amount)],
                     start_parameter='true',
                     photo_url='https://aic.com.ua/img/pyt3.jpg')
    utility.update({str(message.chat.id) + 'order': order})


@bot.pre_checkout_query_handler(func=lambda query: True)
def process_pre_checkout_query(pre_checkout_query: types.PreCheckoutQuery):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@bot.message_handler(content_types='successful_payment')
def process_successful_payment(message: types.Message):
    print(message.successful_payment)
    # total_amount = message.successful_payment['total_amount']  TypeError: 'SuccessfulPayment' object is not subscriptable
    # payload = message.successful_payment['invoice_payload']
    print('Платёж прошел. Всё найс')
    contract = utility.get(str(message.chat.id) + 'contract_id')
    url_for_emi = f'https://web.ewa.ua/ewa/api/v10/contract/{contract}/state/SIGNED'
    rf = requests.post(url_for_emi, headers=headers, cookies=cookies)  # перевод договора в состояние ЗАКЛЮЧЕН
    print(rf)
    bot.send_message(message.chat.id,
                     '👌Платіж пройшов успішно!\n\n📬Перевірте пошту, яку вказували при оформленні - ваш електронний поліс у форматі PDF має бути там.\n\n👏Якщо ви задоволені моєю роботою - поділіться мною, будь-ласка, з другом  - https://t.me/tourism_insurance_bot.')
    dbworker.clear_db(message.chat.id)
    try:
        utility.pop(str(message.chat.id) + 'place_code')
        utility.pop(str(message.chat.id) + 'date_from')
        utility.pop(str(message.chat.id) + 'date_from_check')
        utility.pop(str(message.chat.id) + 'date_to')
        utility.pop(str(message.chat.id) + 'date_to_check')
        utility.pop(str(message.chat.id) + 'trip_purpose')
        utility.pop(str(message.chat.id) + 'tariff1')
        utility.pop(str(message.chat.id) + 'tariff2')
        utility.pop(str(message.chat.id) + 'tariff3')
        utility.pop(str(message.chat.id) + 'tariff4')
        utility.pop(str(message.chat.id) + 'tariff5')
        utility.pop(str(message.chat.id) + 'tariff_risk_amount')
        utility.pop(str(message.chat.id) + 'tariff_name')
        utility.pop(str(message.chat.id) + 'contract_id')
        utility.pop(str(message.chat.id) + 'tariff_payment')
        utility.pop(str(message.chat.id) + 'tariff_discounted_payment')
        utility.pop(str(message.chat.id) + 'order')
    except KeyError:
        pass


@bot.message_handler(func=lambda message: message.text == 'Змінити✖')
def no(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    button1 = types.KeyboardButton('Прізвище')
    button2 = types.KeyboardButton("І'мя")
    button3 = types.KeyboardButton('Дата нарождения')
    button4 = types.KeyboardButton('Адреса реєстрації')
    button5 = types.KeyboardButton('EMAIL')
    button6 = types.KeyboardButton('Телефон')
    button7 = types.KeyboardButton('Серія документа')
    button8 = types.KeyboardButton('Номер документа')
    markup.add(button1, button2, button3, button4, button5, button6, button7, button8)
    bot.send_message(message.chat.id, 'Виберіть що хочете змінити:', reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == 'Прізвище')
def surname_set(message):
    bot.send_message(message.chat.id, 'Введіть ваше прізвище(українською):✍')
    dbworker.set_state(message.chat.id, config.States.S1_SURNAME.value)


@bot.message_handler(func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S1_SURNAME.value)
def surname_taking_again(message):
    log(message)
    v = message.text
    connection = sql.connect('DATABASE.sqlite')
    q = connection.cursor()
    q.execute("UPDATE user SET surname='%s' WHERE id='%s'" % (v, message.from_user.id))
    connection.commit()
    q.close()
    connection.close()
    prefinal(message)


@bot.message_handler(func=lambda message: message.text == "І'мя")
def name_set(message):
    bot.send_message(message.chat.id, 'Введіть ваше імя(українською):✍')
    dbworker.set_state(message.chat.id, config.States.S1_NAME.value)


@bot.message_handler(func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S1_NAME.value)
def name_taking_again(message):
    log(message)
    v = message.text
    connection = sql.connect('DATABASE.sqlite')
    q = connection.cursor()
    q.execute("UPDATE user SET name='%s' WHERE id='%s'" % (v, message.from_user.id))
    connection.commit()
    q.close()
    connection.close()
    prefinal(message)


@bot.message_handler(func=lambda message: message.text == 'Дата нарождения')
def date_set(message):
    bot.send_message(message.chat.id, 'Введіть вашу дату нарождения(в форматі РРРР-ММ-ДД):✍')
    dbworker.set_state(message.chat.id, config.States.S1_DATE_OF_BIRTH.value)


@bot.message_handler(
    func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S1_DATE_OF_BIRTH.value)
def date_taking_again(message):
    log(message)
    v = message.text
    connection = sql.connect('DATABASE.sqlite')
    q = connection.cursor()
    q.execute("UPDATE user SET date_of_birth='%s' WHERE id='%s'" % (v, message.from_user.id))
    connection.commit()
    q.close()
    connection.close()
    prefinal(message)


@bot.message_handler(func=lambda message: message.text == 'Адреса реєстрації')
def address_set(message):
    bot.send_message(message.chat.id, 'Введіть вашу адресу прописки(в форматі "Місто,Вулиця,Дім,Квартира"):✍')
    dbworker.set_state(message.chat.id, config.States.S1_ADDRESS.value)


@bot.message_handler(func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S1_ADDRESS.value)
def address_taking_again(message):
    log(message)
    v = message.text
    connection = sql.connect('DATABASE.sqlite')
    q = connection.cursor()
    q.execute("UPDATE user SET address='%s' WHERE id='%s'" % (v, message.from_user.id))
    connection.commit()
    q.close()
    connection.close()
    prefinal(message)


@bot.message_handler(func=lambda message: message.text == 'EMAIL')
def email_set(message):
    bot.send_message(message.chat.id, 'Введіть ваш email(сюди буде висланий поліс):✍')
    dbworker.set_state(message.chat.id, config.States.S1_EMAIL.value)


@bot.message_handler(func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S1_EMAIL.value)
def email_taking_again(message):
    log(message)
    v = message.text
    connection = sql.connect('DATABASE.sqlite')
    q = connection.cursor()
    q.execute("UPDATE user SET email='%s' WHERE id='%s'" % (v, message.from_user.id))
    connection.commit()
    q.close()
    connection.close()
    prefinal(message)


@bot.message_handler(func=lambda message: message.text == 'Телефон')
def phone_set(message):
    bot.send_message(message.chat.id, 'Введіть ваш номер телефону:✍')
    dbworker.set_state(message.chat.id, config.States.S1_PHONE.value)


@bot.message_handler(func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S1_PHONE.value)
def phone_taking_again(message):
    log(message)
    v = message.text
    connection = sql.connect('DATABASE.sqlite')
    q = connection.cursor()
    q.execute("UPDATE user SET phone='%s' WHERE id='%s'" % (v, message.from_user.id))
    connection.commit()
    q.close()
    connection.close()
    prefinal(message)


@bot.message_handler(func=lambda message: message.text == 'Серія документа')
def series_set(message):
    bot.send_message(message.chat.id, 'Введіть вашу серію документа:✍')
    dbworker.set_state(message.chat.id, config.States.S1_SERIES.value)


@bot.message_handler(func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S1_SERIES.value)
def series_taking_again(message):
    log(message)
    v = message.text
    connection = sql.connect('DATABASE.sqlite')
    q = connection.cursor()
    q.execute("UPDATE passport SET series='%s' WHERE id='%s'" % (v, message.from_user.id))
    connection.commit()
    q.close()
    connection.close()
    prefinal(message)


@bot.message_handler(func=lambda message: message.text == 'Номер документа')
def number_set(message):
    bot.send_message(message.chat.id, 'Введіть ваш номер документа:✍')
    dbworker.set_state(message.chat.id, config.States.S1_NUMBER.value)


@bot.message_handler(func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S1_NUMBER.value)
def number_taking_again(message):
    log(message)
    v = message.text
    connection = sql.connect('DATABASE.sqlite')
    q = connection.cursor()
    q.execute("UPDATE passport SET number='%s' WHERE id='%s'" % (v, message.from_user.id))
    connection.commit()
    q.close()
    connection.close()
    prefinal(message)


# BOT RUNNING
if __name__ == '__main__':
    bot.polling(none_stop=True)
