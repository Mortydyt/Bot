import peewee
from bot_init import bot
from telebot.types import Message, CallbackQuery
from keyboards import (start_kb, change_kb, start_users_kb, main_menu_kb, get_subscribe_kb,
                       game_start_kb, result_game_kb, stop_game, check_payment_kb, subscribe_users_kb)
from database import db, UsersData, HistoryData, UsersInfo
import time
from selenium import webdriver
import fake_useragent
from bs4 import BeautifulSoup
import sqlite3
import yookassa
from yookassa import Payment
from bot_secrets import ADMIN_ID, SHOP_ID, SHOP_SECRET_KEY
from headers import HEADERS
import requests
import datetime

user = fake_useragent.UserAgent().random
headers = {
    "user-agent": user
}

# Создаем объект ChromeOptions для настройки параметров запуска ChromeDriver
options = webdriver.ChromeOptions()

# Отключаем некоторые функции, чтобы скрыть использование автоматизации
options.add_argument("--disable-blink-features=AutomationControlled")

# Запускаем браузер в фоновом режиме без отображения графического интерфейса
options.add_argument('--headless')

# Устанавливаем размер окна браузера на 1920x1080 пикселей
options.add_argument("--window-size=1920,1080")

# Отключаем все расширения браузера, чтобы избежать их влияния на работу
options.add_argument("--disable-extensions")

# Указываем использовать прямое соединение без прокси-сервера
options.add_argument("--proxy-server='direct://'")

# Указываем игнорировать все прокси-сервера для всех запросов
options.add_argument("--proxy-bypass-list=*")

# Запускаем браузер с максимальным размером окна
options.add_argument("--start-maximized")

# Отключаем использование /dev/shm для хранения временных файлов, чтобы избежать проблем на системах с ограниченной памятью
options.add_argument("--disable-dev-shm-usage")

# Отключаем режим песочницы, что может быть полезно в Docker или ограниченных средах
options.add_argument('--no-sandbox')

# Игнорируем ошибки сертификатов, чтобы избежать сбоев при работе с HTTPS-сайтами с недействительными сертификатами
options.add_argument("--ignore-certificate-errors")

# Отключаем вывод лишних логов в консоль
options.add_experimental_option('excludeSwitches', ['enable-logging'])


def get_payment_status(payment_id):
    response = requests.get(f"https://api.yookassa.ru/v3/payments/{payment_id}", headers=HEADERS)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error in get_payment_status: {response.status_code}, {response.json()}")
        return None


def create_payment(price: str, description: str):
    """
    Функция для создания ссылки на оплату через сервис ЮКасса
    :param price: стоимость заказа
    :param description: описание товара
    :return: confirmation_url, id_order: ссылка на оплату, номер заказа
    """
    yookassa.Configuration.configure(SHOP_ID, SHOP_SECRET_KEY)

    res = Payment.create(
        {
            "amount": {
                "value": price,
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": "https://t.me/intensiv_vyz_tgbot"  # Ссылка на бота после оплаты
            },

            "capture": True,
            "description": description,
            "receipt": {  # Создаем чек
                "customer": {
                    "full_name": "Дмитренко Михаил Иванович",
                    "email": "mikhail@dmitrenko.spb.ru",
                    "phone": "79313002280",
                    "inn": "780110481480"
                },
                "items": [
                    {
                        "description": description,
                        "quantity": "1.00",
                        "amount": {
                            "value": price,
                            "currency": "RUB"
                        },
                        "vat_code": "2",
                    },
                ]
            }
        }
    )
    confirmation_url = res.confirmation.confirmation_url  # Ссылка на оплату
    id_order = res.id  # Номер платежа
    return confirmation_url, id_order


# Настраиваем работу магазина
yookassa.Configuration.account_id = SHOP_ID  # '<Идентификатор магазина>'
yookassa.Configuration.secret_key = SHOP_SECRET_KEY  # '<Секретный ключ>'

with db:  # Создаем таблицы для всех баз данных бота
    db.create_tables([UsersData, HistoryData, UsersInfo])


def get_history_from_db():
    """
    Функция получения всех данных из таблицы БД, хранящей информацию о всех темах
    :return: all_data: все данные из таблицы БД SQLite
    """
    conn = sqlite3.connect('1win_analiz.db')
    cursor = conn.cursor()
    cursor.execute("SELECT round_num, coefficient FROM history_data ORDER BY round_num LIMIT 100000")
    all_data = cursor.fetchall()
    conn.close()
    return all_data


@bot.message_handler(func=lambda message: message.text == 'Остановить!')
@bot.message_handler(func=lambda message: message.text == 'Запустить!')
def parsing_selenium(message: Message, url='https://lucky-jet.gamedev-atech.cc/?exitUrl=https%253A%252F%252F1wwxqc.win%252Fcasino&language=ru&b=demo', delay=7):
    """
    Функция начала парсинга всех коэффициентов и запуск основной функции бота
    :param message: команда от пользователя
    :param url: ссылка на страницу игры Lucky Jet
    :param delay: пауза (устанавливаем == 7)
    """
    driver = webdriver.Chrome(options=options)
    driver.maximize_window()
    driver.get(url)
    time.sleep(delay)
    history_arr = []  # Словарь с коэффициентами
    info = UsersData.get(UsersData.user_id == message.from_user.id)  # Обращение к БД пользователя

    if message.text == 'Запустить!':
        info.check = 'False'
        info.good_step = 0
        bot.send_message(chat_id=message.chat.id, text='Бот начал свою работу!', reply_markup=start_kb)
    elif message.text == 'Остановить!':
        info.check = 'True'
        bot.send_message(chat_id=message.chat.id, text='Работа бота остановлена!', reply_markup=start_kb)
    info.save()

    while info.check == 'False':
        try:
            time.sleep(3)
            soup = BeautifulSoup(driver.page_source, 'lxml')
            history_div = soup.find('div', {'id': 'history'})
            if len(history_arr) < 100_000:
                new_coefficient = float(history_div.find('div', {'class': 'sc-cmaqmh igNieT'}).text.strip().rstrip('x'))  # Коэффициент из игры
                if len(history_arr) == 0:
                    history_arr.append(new_coefficient)
                    # print(history_arr[::-1])
                    info = UsersData.get(UsersData.user_id == message.from_user.id)  # Обращение к БД пользователя
                    if info.check == 'False':
                        info.game_round += 1
                        info.save()

                    try:
                        HistoryData.create(
                            round_num=info.game_round,
                            coefficient=new_coefficient,
                        )
                    except peewee.IntegrityError:
                        print('Такой раунд уже был')

                    if new_coefficient < info.rate:
                        info.good_step += 1  # Повышаем удачную серию
                        info.save()

                        if info.good_step == info.once_row:  # Проверка, совпало ли количество в ряд
                            if info.check == 'False':
                                bot.send_message(chat_id=message.chat.id,
                                                 text=f'<b>Количество в ряд выполнилось!</b> \U00002705 \n\n'
                                                      f'Параметры:\n\n'
                                                      f'{info.once_row} раз(а) подряд\n'
                                                      f'Коэффициент меньше {info.rate}\n\n',
                                                 parse_mode='html')
                            info.good_step = 0
                            info.save()
                        else:
                            continue
                    else:
                        if info.good_step != 0:  # Проверка, была ли начата удачная серия
                            info.good_step = 0
                            info.save()
                        else:
                            continue

                elif new_coefficient != history_arr[-1]:
                    history_arr.append(new_coefficient)
                    info = UsersData.get(UsersData.user_id == message.from_user.id)  # Обращение к БД пользователя
                    if info.check == 'False':
                        info.game_round += 1
                        info.save()

                    try:
                        HistoryData.create(
                            round_num=info.game_round,
                            coefficient=new_coefficient,
                        )
                    except peewee.IntegrityError:
                        print('Такой раунд уже был')

                    if new_coefficient < info.rate:
                        info.good_step += 1  # Повышаем удачную серию
                        info.save()

                        if info.good_step == info.once_row:  # Проверка, совпало ли количество в ряд
                            if info.check == 'False':
                                bot.send_message(chat_id=message.chat.id,
                                                 text=f'<b>Количество в ряд выполнилось!</b> \U00002705 \n\n'
                                                      f'Параметры:\n\n'
                                                      f'{info.once_row} раз(а) подряд\n'
                                                      f'Коэффициент меньше {info.rate}\n\n',
                                                 parse_mode='html')
                            info.good_step = 0
                            info.save()
                        else:
                            continue
                    else:
                        if info.good_step != 0:  # Проверка, была ли начата удачная серия
                            info.good_step = 0
                            info.save()
                        else:
                            continue
            else:
                new_coefficient = history_div.find('div', {'class': 'sc-cmaqmh igNieT'}).text.strip()
                if new_coefficient != history_arr[-1]:
                    bot.send_message(chat_id=message.chat.id, text='Прошло 100_000 игр!')
                    history_arr.append(new_coefficient)
                history_arr.pop(0)
        except ValueError as exc:
            print('Плохой коэффициент', exc)


@bot.message_handler(func=lambda message: message.text == 'Вернуться назад')
@bot.message_handler(commands=['start'])
def start_work(message: Message):
    """
    Функция начала работы с ботом
    :param message: сообщение от пользователя
    """
    if message.from_user.id == int(ADMIN_ID):
        # Создаем базу данных для админа
        try:
            UsersData.create(
                user_id=message.from_user.id,
                once_row=0,
                rate=0,
                need_rate=0,
                good_step=0,
                game_round=0,
                check=0,
            )
        except peewee.IntegrityError:
            print('Уже есть в БД')

        bot.send_message(chat_id=message.chat.id, text='Выберите действие ниже \U00002B07',
                         reply_markup=start_kb)
    else:
        try:
            # Создаем базу данных для пользователей бота
            UsersInfo.create(
                user_id=message.from_user.id,
                amount=0,
                subscribe_date=0,
                coefficient=0,
                check=0,
                try_period=3,
                order_num=0,
            )
        except peewee.IntegrityError:
            print('Уже был')

        photo_path = 'Фото начало.jpg'  # Путь к фотографии

        with open(photo_path, 'rb') as photo:
            bot.send_photo(chat_id=message.chat.id, photo=photo,
                           caption='\U0001F4CC Бот специально был создан для игры в Lucky Jet.'
                                    ' Данный бот реализован на математической модели, которая высчитывает вероятность '
                                   'сыгровки тех или иных коэффициентов.\n\n'
                                   '\U0001F914 В боте вас ожидает:\n'
                                    '\U00002705 Расчет процентного шанса выпадения коэффициентов вашей ставки на каждую игру.\n'
                                    '\U00002705 Бесперебойное функционирование.\n'
                                    '\U00002705 99% шанс захода коэффициента.\n'
                                    '\U00002705 Круглосуточная техническая поддержка пользователей.\n',
                           reply_markup=start_users_kb)


@bot.callback_query_handler(func=lambda call: call.data == 'main_menu')
def back_start_func(call: CallbackQuery):
    """
    Функция возвращения к приветственному сообщению бота
    :param call: callback-кнопка
    """
    photo_path = 'Фото начало.jpg'  # Путь к фотографии

    with open(photo_path, 'rb') as photo:
        bot.send_photo(chat_id=call.message.chat.id, photo=photo,
                       caption='\U0001F4CC Бот специально был создан для игры в Lucky Jet.'
                               'Данный бот реализован на математической модели, которая высчитывает вероятность '
                               'сыгровки тех или иных коэффициентов.\n\n'
                               ' В боте вас ожидает:\n'
                               '\U0001F914 В боте вас ожидает:\n'
                               '\U00002705 Расчет процентного шанса выпадения коэффициентов вашей ставки на каждую игру.\n'
                               '\U00002705 Бесперебойное функционирование.\n'
                               '\U00002705 99% шанс захода коэффициента.\n'
                               '\U00002705 Круглосуточная техническая поддержка пользователей.\n',
                       reply_markup=start_users_kb)


@bot.callback_query_handler(func=lambda call: call.data == 'more_info')
def more_information(call: CallbackQuery):
    """
    Функция отправки большей информации о боте
    :param call: callback-кнопка
    """
    if call.message:
        bot.send_message(chat_id=call.message.chat.id, text='Бот основан на анализе базы данных, которая включает в '
                                                            'себя результаты последних 100_000 игр. Посредством динамического '
                                                            'обновления информации высчитывается процентное отношение коэффициентов на '
                                                            'следующую ставку, что позволяет выбрать беспроигрышный результат игры или '
                                                            'заведомо отказаться от ставки с провальным коэффициентом в нужный момент.\n\n'
                                                            '<b>Время испытать бота, проверь его результаты!</b>\n'
                                                            'После оплаты вы получите промокод с помощью которого сможете испытывать бота с крупными суммами и меньшим риском.',
                         parse_mode='html',
                         reply_markup=main_menu_kb)


@bot.callback_query_handler(func=lambda call: call.data == 'subscribe')
def get_subscribe(call: CallbackQuery):
    """
    Функция начала оформления подписки
    :param call: callback-кнопка
    """
    if call.message:
        bot.send_message(chat_id=call.message.chat.id, text='<b>Информация о ценах:</b>\n\n'
                                                            'Ежедневная: 500 руб.\n'
                                                            'Еженедельная: 2750 <s>3500</s> руб.\n'
                                                            'Ежемесячная: 11850 <s>15000</s> руб.\n'
                                                            'Ежегодная: 100000 <s>180000</s> руб.',
                         parse_mode='html',
                         reply_markup=get_subscribe_kb)


@bot.callback_query_handler(func=lambda call: call.data == 'game_result')
def game_result(call: CallbackQuery):
    """
    Функция выдачи результата игр
    :param call: callback-кнопка
    """
    if call.message:
        info = UsersInfo.get(UsersInfo.user_id == call.from_user.id)
        info.try_period -= 1
        info.save()

        if info.try_period >= 0 or info.subscribe_date != 0:
            history = get_history_from_db()  # Обращаемся к БД и получаем историю коэффициентов
            bot.send_message(chat_id=call.message.chat.id, text=f'Информация основана на последних 100_000 игр')
            coefficient_1_5 = 0
            coefficient_2 = 0
            coefficient_2_5 = 0
            coefficient_3 = 0
            coefficient_3_5 = 0
            coefficient_100 = 0

            for row in history:
                if 1.45 <= float(row[1]) <= 1.55 or float(row[1]) >= 1.5:
                    coefficient_1_5 += 1
                elif 1.95 <= float(row[1]) <= 2.05 or float(row[1]) >= 2:
                    coefficient_2 += 1
                elif 2.45 <= float(row[1]) <= 2.55 or float(row[1]) >= 2.5:
                    coefficient_2_5 += 1
                elif 2.95 <= float(row[1]) <= 3.05 or float(row[1]) >= 3:
                    coefficient_3 += 1
                elif 3.45 <= float(row[1]) <= 3.55 or float(row[1]) >= 3.5:
                    coefficient_3_5 += 1
                elif 99.5 <= float(row[1]) <= 100.5 or float(row[1]) >= 100:
                    coefficient_100 += 1

            bot.send_message(chat_id=call.message.chat.id, text=f'В следующей игре:\n\n'
                                                                f'1.5 - {round(coefficient_1_5 / len(history) * 100, 2)} %\n'
                                                                f'2.0 - {round(coefficient_2 / len(history) * 100, 2)} %\n'
                                                                f'2.5 - {round(coefficient_2_5 / len(history) * 100, 2)} %\n'
                                                                f'3.0 - {round(coefficient_3 / len(history) * 100, 2)} %\n'
                                                                f'3.5 - {round(coefficient_3_5 / len(history) * 100, 2)} %\n'
                                                                f'>100 - {round(coefficient_100 / len(history) * 100, 2)} %')
        else:
            bot.send_message(chat_id=call.message.chat.id, text='Ваш пробный период закончился')


@bot.callback_query_handler(func=lambda call: call.data == 'day')
@bot.callback_query_handler(func=lambda call: call.data == 'week')
@bot.callback_query_handler(func=lambda call: call.data == 'month')
@bot.callback_query_handler(func=lambda call: call.data == 'year')
@bot.callback_query_handler(func=lambda call: call.data == 'back_promo')
def get_payment(call: CallbackQuery):
    """
    Функция для перехода к оплате подписки
    :param call: callback-кнопка
    """
    if call.message:
        user_info = UsersInfo.get(UsersInfo.user_id == call.from_user.id)
        if call.data == 'day':
            end_date = datetime.datetime.now() + datetime.timedelta(days=1)
            user_info.amount = '500'
            user_info.subscribe_date = end_date
        elif call.data == 'week':
            end_date = datetime.datetime.now() + datetime.timedelta(days=7)
            user_info.amount = '2750'
            user_info.subscribe_date = end_date
        elif call.data == 'month':
            end_date = datetime.datetime.now() + datetime.timedelta(days=31)
            user_info.amount = '11850'
            user_info.subscribe_date = end_date
        elif call.data == 'year':
            end_date = datetime.datetime.now() + datetime.timedelta(days=366)
            user_info.amount = '100000'
            user_info.subscribe_date = end_date
        # user_info.save()

        description = 'Подписка на бот'
        payment_url = create_payment(user_info.amount, description)
        user_info.order_num = payment_url[1]
        user_info.save()

        bot.send_message(chat_id=call.message.chat.id, text=f"<b>Перейди по ссылке ниже и соверши платёж, после чего предоставится полный доступ к боту</b> {payment_url[0]}\n\n"
                                                            f"<b>Номер заказа:</b> {payment_url[1]}\n\nПосле оплаты заказа нажмите кнопку ниже \U00002B07",
                         parse_mode='html',
                         reply_markup=check_payment_kb)


@bot.callback_query_handler(func=lambda call: call.data == 'check_payment')
def check_payment(call: CallbackQuery):
    """
    Функция для просмотра истории игр уже с уже купленной подпиской
    :param call: callback-кнопка
    """
    if call.message:
        payment_id = UsersInfo.get(UsersInfo.user_id == call.from_user.id).order_num
        user_info = UsersInfo.get(UsersInfo.user_id == call.from_user.id)
        HEADERS['Idempotence-Key'] = payment_id
        payment_status = get_payment_status(payment_id)

        if payment_status and payment_status['status'] == 'succeeded':
            bot.send_message(chat_id=call.message.chat.id, text=f'<b>Оплата прошла успешно!\U00002705</b>\n\n'
                                                                f'Ваша подписка истекает: {user_info.subscribe_date}',
                             parse_mode='html')

            photo_path = 'Фото промо.jpg'  # Путь к фотографии

            with open(photo_path, 'rb') as photo:
                bot.send_photo(chat_id=call.message.chat.id, photo=photo,
                               caption='С покупкой подписки вам открыта возможность гарантировано зарабатывать неограниченное количество средств. Воспользовавшись '
                                       'промокодом: INOIJET к вашему депозиту добавиться 500%. Начни зарабатывать на проекте [прямо сейчас](https://1wbhk.com/?open=register&p=u421).',
                               parse_mode='Markdown',
                               reply_markup=game_start_kb)
        else:
            bot.send_message(chat_id=call.message.chat.id, text='<b>Ваш платеж не прошел</b> \U0000274C \n\n'
                                                                'Попробуйте еще раз',
                             parse_mode='html',
                             reply_markup=subscribe_users_kb)


@bot.callback_query_handler(func=lambda call: call.data == 'update')
@bot.callback_query_handler(func=lambda call: call.data == 'game_result_buying')
def game_result_buying(call: CallbackQuery):
    """
    Функция для просмотра истории игр уже с уже купленной подпиской
    :param call: callback-кнопка
    """
    if call.message:
        # Получаем последние 20 коэффициентов из базы данных
        conn = sqlite3.connect('1win_analiz.db')
        cursor = conn.cursor()
        cursor.execute('''SELECT * FROM history_data ORDER BY round_num DESC LIMIT 20''')
        rows = cursor.fetchall()
        conn.close()

        coefficient_list = []  # Список с этими коэффициентами
        for row in rows:
            coefficient_list.append(float(row[1]))

        text = ''  # Выводящий текст бота
        for coefficient in coefficient_list:
            if coefficient >= 1.5 or coefficient >= 2 or coefficient >= 2.5 or coefficient >= 3 or coefficient >= 3.5 or coefficient >= 100:
                text += f'\U00002705 {coefficient}\n'
            else:
                text += f'\U0000274C {coefficient}\n'

        bot.send_message(chat_id=call.message.chat.id, text=text, reply_markup=result_game_kb)


@bot.callback_query_handler(func=lambda call: call.data == 'my_subscribe')
def users_subscribe(call: CallbackQuery):
    """
    Функция для проверки подписки пользователем
    :param call: callback-кнопка
    """
    if call.message:
        info = UsersInfo.get(UsersInfo.user_id == call.from_user.id)
        end_date = info.subscribe_date
        bot.send_message(chat_id=call.message.chat.id, text=f'Ваша подписка истекает: {end_date}')


@bot.callback_query_handler(func=lambda call: call.data == 'start_game')
@bot.callback_query_handler(func=lambda call: call.data == 'stop_working')
def starting_game(call: CallbackQuery):
    """
    Функция для проверки подписки пользователем
    :param call: callback-кнопка
    """
    if call.message:
        info = UsersInfo.get(UsersInfo.user_id == call.from_user.id)
        if call.data == 'start_game':
            info.check = 'True'
        elif call.data == 'stop_working':
            info.check = 'False'
        info.save()

        # Получаем последней игры из БД
        while info.check == 'True':
            conn = sqlite3.connect('1win_analiz.db')
            cursor = conn.cursor()
            cursor.execute('''SELECT * FROM history_data ORDER BY round_num DESC LIMIT 1''')
            rows = cursor.fetchall()
            conn.close()

            for row in rows:
                if info.coefficient != row[1]:
                    bot.send_message(chat_id=call.message.chat.id, text=f'<b>Сыграл только что следующий коэффициент:</b> {row[1]}',
                                     parse_mode='html',
                                     reply_markup=stop_game)
                    info.coefficient = row[1]
                    info.save()
                    time.sleep(5)
                else:
                    time.sleep(5)
                    continue


@bot.callback_query_handler(func=lambda call: call.data == 'support_after')
@bot.callback_query_handler(func=lambda call: call.data == 'support_before')
def support_after(call: CallbackQuery):
    """
    Функция связи с технической поддержкой бота
    :param call: callback-кнопка
    """
    if call.message:
        bot.send_message(chat_id=call.message.chat.id, text='\U0001F4F1  Связь с поддержкой:\n\n'
                                                            '@inoijet_support')


@bot.message_handler(func=lambda message: message.text == 'Изменить параметры!')
def change_settings(message: Message):
    """
    Функция изменения параметров бота
    :param message: команда от пользователя
    """
    bot.send_message(chat_id=message.chat.id, text=f'<b>Ваши параметры:</b>\n\n'
                                                   f'{UsersData.get(UsersData.user_id == message.from_user.id).once_row} раз(а) подряд\n'
                                                   f'Коэффициент меньше {UsersData.get(UsersData.user_id == message.from_user.id).rate}',
                     parse_mode='html',
                     reply_markup=change_kb)


@bot.message_handler(func=lambda message: message.text == 'Изменить!')
def get_once_row(message: Message):
    """
    Функция получения данных о количестве в ряд
    :param message: команда от пользователя
    """
    msg = bot.send_message(chat_id=message.chat.id, text='Введите количество в ряд')
    bot.register_next_step_handler(msg, save_once_row)


def save_once_row(message: Message):
    """
    Функция сохранения в БД количества в ряд
    :param message: данные от пользователя
    """
    info = UsersData.get(UsersData.user_id == message.from_user.id)
    info.once_row = int(message.text)
    info.save()

    msg = bot.send_message(chat_id=message.chat.id, text='Введите максимальный коэффициент в виде вещественного числа')
    bot.register_next_step_handler(msg, save_rate)


def save_rate(message: Message):
    """
    Функция сохранения в БД максимального коэффициента
    :param message: данные от пользователя
    """
    info = UsersData.get(UsersData.user_id == message.from_user.id)
    info.rate = float(message.text)
    info.save()

    bot.send_message(chat_id=message.chat.id, text=f'<b>Ваши параметры изменены:</b>\n\n'
                                                   f'{info.once_row} раз(а) подряд\n'
                                                   f'Коэффициент меньше {info.rate}\n\n'
                                                   f'<b>НЕ ЗАБУДЬТЕ ЗАПУСТИТЬ БОТА</b> \U00002757',
                     parse_mode='html')
    bot.send_message(chat_id=message.chat.id, text='Выберите действие ниже \U00002B07',
                     reply_markup=start_kb)


@bot.message_handler(func=lambda message: message.text == 'Проверить по истории!')
def bot_history(message: Message):
    """
    Функция просмотра истории
    :param message: команда от пользователя
    """
    msg = bot.send_message(chat_id=message.chat.id, text='Введите коэффициент, который будете ждать')
    bot.register_next_step_handler(msg, save_need_rate)


def save_need_rate(message: Message):
    info = UsersData.get(UsersData.user_id == message.from_user.id)
    info.need_rate = float(message.text)
    info.save()

    bot.send_message(chat_id=message.chat.id, text=f'<b>Запрос на проверку истории отправлен!</b>\n\n'
                                                   f'Параметры:\n\n'
                                                   f'{info.once_row} раз(а) подряд\n'
                                                   f'Коэффициент меньше {info.rate}\n\n'
                                                   f'Ожидаем коэффициента {info.need_rate}.\n'
                                                   f'Это может занять несколько минут. Ожидайте ответа.',
                     parse_mode='html')

    history = get_history_from_db()
    signal = 0  # Количество сигналов
    good_step = 0  # Удачная серия
    counter = 0  # Счетчик раза
    text = ''  # Сообщение бота

    for row in history:
        if row[1] < info.rate:
            good_step += 1
            if good_step == info.once_row:
                signal += 1
                good_step = 0

    bot.send_message(chat_id=message.chat.id, text=f'\U0001F4D6 <b>По истории за последние {len(history)} игр!</b>\n\n'
                                                   f'По вашему алгоритму было {signal} сигналов\n\n'
                                                   f'Если ждать коэффициент {info.need_rate}, то:\n',
                     parse_mode='html')

    good_step = 0

    for row in history:
        if good_step >= info.once_row and row[1] >= info.need_rate:
            bot.send_message(chat_id=message.chat.id, text=f'\U00002705 {good_step} из {signal} зашло с {counter} раза.')
            counter = 0
            good_step = 0
        if row[1] < info.rate:
            if good_step <= info.once_row:
                good_step += 1
            if good_step >= info.once_row:
                good_step += 1
                counter += 1


@bot.message_handler(func=lambda message: True)
def echo_all(message) -> None:
    """
    Обработчик сообщений echo_all
    :param message: принятое сообщение от пользователя
    """
    bot.reply_to(message, message.text)


if __name__ == '__main__':
    bot.infinity_polling()
