import os
from dotenv import load_dotenv, find_dotenv

if not find_dotenv():  # Функция поиска переменных окружения
    exit("Переменные окружения не загружены, так как отсутствует файл .env")
else:
    load_dotenv()  # Загрузка переменных окружения


BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
SHOP_ID = os.getenv("SHOP_ID")
SHOP_SECRET_KEY = os.getenv("SHOP_SECRET_KEY")
YKASSA_URL = os.getenv("YKASSA_URL")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
