import pandas as pd
import logging
import json
from datetime import datetime
from dateutil.relativedelta import relativedelta
from functools import wraps
from typing import Optional
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
log_path = os.path.join(current_dir, "../logs/reports.log")

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)


def report_decorator():
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            report_data = func(*args, **kwargs)
            filename = f'report_{func.__name__}_{datetime.now().strftime("%Y%m%d-%H%M%S")}.json'
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=4)
            logger.info(f'Сохранено: {filename}')
            return report_data
        return wrapper
    return decorator

@report_decorator()
def spending_by_category(excel_path: str, category: str, date: Optional[str] = None):
    """"""
    logger.info(f'Загрузка файла: {excel_path}')

    df = pd.read_excel(excel_path)

    end_date = datetime.strptime(date, '%Y-%m-%d') if date else datetime.now()
    start_date = end_date - relativedelta(months=3)

    logger.info(f'Период: с {start_date.strftime("%Y-%m-%d")} по {end_date.strftime("%Y-%m-%d")}')

    df['Дата операции'] = pd.to_datetime(df['Дата операции'], format='%d.%m.%Y %H:%M:%S')
    if df['Сумма операции'].dtype == 'object':
        df['Сумма операции'] = df['Сумма операции'].str.replace(',', '.').astype(float)
    elif df['Сумма операции'].dtype in ['int64', 'int32']:
        df['Сумма операции'] = df['Сумма операции'].astype(float)

    filtered = df[(df['Категория'] == category) &
                  (df['Дата операции'] >= start_date) &
                  (df['Дата операции'] <= end_date)]

    logger.info(f'Найдено транзакций: {len(filtered)}')

    if filtered.empty:
        logger.warning(f'Нет транзакций по категории "{category}" за указанный период')
        return []

    filtered['Дата операции'] = filtered['Дата операции'].dt.strftime('%Y-%m-%d %H:%M:%S')

    logger.info(f'Возвращаем {len(filtered)} транзакций')

    return filtered.to_dict(orient='records')



# result = spending_by_category(
#     excel_path='data/operations.xlsx',
#     category='ЖКХ',
#     date='2021-12-15'
# )
#
#
# print(json.dumps(result, indent=2, ensure_ascii=False))