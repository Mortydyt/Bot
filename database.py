from peewee import SqliteDatabase, Model, IntegerField, CharField, FloatField

# База данных всех пользователей
db = SqliteDatabase('1win_analiz.db')


class BaseModelData(Model):
    """
    Базовый класс для каждого пользователя
    """
    class Meta:
        database = db


class UsersData(BaseModelData):
    """
    Класс учеников для хранения информации о них
    args: user_id: ID пользователя telegram
          once_row: количество в ряд
          rate: коэффициент
          need_rate: ожидаемый коэффициент
          good_step: подсчет выполненных условий
          game_round: количество сыгранных раундов
          check: переключатель
    """
    user_id = IntegerField(primary_key=True)
    once_row = IntegerField()
    rate = FloatField()
    need_rate = FloatField()
    good_step = IntegerField()
    game_round = IntegerField()
    check = CharField()

    class Meta:
        db_table = 'users_data'


class HistoryData(BaseModelData):
    """
    Класс историй раундов
    """
    round_num = IntegerField(primary_key=True)
    coefficient = FloatField()

    class Meta:
        db_table = 'history_data'


class UsersInfo(BaseModelData):
    """
    Класс ID пользователей telegram
    args: user_id: ID пользователя telegram
          amount: цена подписки
    """
    user_id = IntegerField(primary_key=True)
    amount = CharField()
    subscribe_date = CharField()
    coefficient = CharField()
    check = CharField()
    try_period = IntegerField()
    order_num = CharField()

    class Meta:
        db_table = 'id_info'
