import telebot

# Стартовая клавиатура
start_kb = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
start_btn = telebot.types.KeyboardButton('Запустить!')
stop_btn = telebot.types.KeyboardButton('Остановить!')
settings_btn = telebot.types.KeyboardButton('Изменить параметры!')
history_btn = telebot.types.KeyboardButton('Проверить по истории!')
start_kb.add(start_btn, stop_btn)
start_kb.add(settings_btn, history_btn)

# Клавиатура начала изменения параметров
change_kb = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
change_btn = telebot.types.KeyboardButton('Изменить!')
back_btn = telebot.types.KeyboardButton('Вернуться назад')
change_kb.add(change_btn, back_btn)

# Вводная клавиатура
start_users_kb = telebot.types.InlineKeyboardMarkup(row_width=1)
subscribe_btn = telebot.types.InlineKeyboardButton(text='Подписка', callback_data='subscribe')
more_info = telebot.types.InlineKeyboardButton(text='Узнать больше о боте', callback_data='more_info')
game_result = telebot.types.InlineKeyboardButton(text='Результаты игр', callback_data='game_result')
start_users_kb.add(subscribe_btn)
start_users_kb.add(more_info)
start_users_kb.add(game_result)

# Кнопка главного меню
main_menu_kb = telebot.types.InlineKeyboardMarkup(row_width=1)
back_btn = telebot.types.InlineKeyboardButton(text='Назад \U000021A9', callback_data='main_menu')
main_menu_kb.add(back_btn)

# Функция выбора подписки
get_subscribe_kb = telebot.types.InlineKeyboardMarkup(row_width=1)
day_btn = telebot.types.InlineKeyboardButton(text='Ежедневная', callback_data='day')
week_btn = telebot.types.InlineKeyboardButton(text='Еженедельная', callback_data='week')
month_btn = telebot.types.InlineKeyboardButton(text='Ежемесячная', callback_data='month')
years_btn = telebot.types.InlineKeyboardButton(text='Ежегодная', callback_data='year')
support_btn = telebot.types.InlineKeyboardButton(text='Техническая поддержка', callback_data='support_before')
get_subscribe_kb.add(day_btn)
get_subscribe_kb.add(week_btn)
get_subscribe_kb.add(month_btn)
get_subscribe_kb.add(years_btn)
get_subscribe_kb.add(support_btn)

# Начало игры
game_start_kb = telebot.types.InlineKeyboardMarkup(row_width=1)
start_game_btn = telebot.types.InlineKeyboardButton(text='Начать игру', callback_data='start_game')
result_btn = telebot.types.InlineKeyboardButton(text='Результаты игр', callback_data='game_result_buying')
my_subscribe = telebot.types.InlineKeyboardButton(text='Моя подписка', callback_data='my_subscribe')
support_btn = telebot.types.InlineKeyboardButton(text='Техническая поддержка', callback_data='support_after')
game_start_kb.add(start_game_btn)
game_start_kb.add(result_btn)
game_start_kb.add(my_subscribe)
game_start_kb.add(support_btn)

# Клавиатура под результатами игр
result_game_kb = telebot.types.InlineKeyboardMarkup(row_width=2)
back_promo_btn = telebot.types.InlineKeyboardButton('Назад', callback_data='back_promo')
update_btn = telebot.types.InlineKeyboardButton(text='Обновить', callback_data='update')
result_game_kb.add(back_promo_btn, update_btn)

# Остановить игру
stop_game = telebot.types.InlineKeyboardMarkup(row_width=1)
stop_game_btn = telebot.types.InlineKeyboardButton(text='Остановить', callback_data='stop_working')
stop_game.add(stop_game_btn)

# Проверить платеж
check_payment_kb = telebot.types.InlineKeyboardMarkup(row_width=1)
check_btn = telebot.types.InlineKeyboardButton(text='Проверить платеж', callback_data='check_payment')
check_payment_kb.add(check_btn)

# Чисто подписка
subscribe_users_kb = telebot.types.InlineKeyboardMarkup(row_width=1)
subscribe_btn = telebot.types.InlineKeyboardButton(text='Подписка', callback_data='subscribe')
subscribe_users_kb.add(subscribe_btn)
