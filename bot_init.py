import telebot
from bot_secrets import BOT_TOKEN

token = BOT_TOKEN  # Задаем значение переменной токена бота в один файл
bot = telebot.TeleBot(token)  # Создаем переменную bot(бот нашего пользователя
