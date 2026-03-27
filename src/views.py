# def day_time_now():
#     """
#     Функция, которая приветствует в зависимости от текущего времени суток.
#     Возвращает строку приветствия в зависимости от времени.
#     """
#     current_date_time = datetime.datetime.now()
#     hour = current_date_time.hour
#
#     if 0 <= hour < 6 or 22 <= hour <= 23:
#         return "Доброй ночи"
#     elif 17 <= hour <= 22:
#         return "Добрый вечер"
#     elif 7 <= hour <= 11:
#         return "Доброе утро"
#     else:
#         return "Добрый день"