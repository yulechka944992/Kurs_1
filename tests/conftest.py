import pytest
import pandas as pd
import os

@pytest.fixture
def excel_file():
    """"""
    df = pd.DataFrame({
        'Описание': [
            'МТС оплата',
            'Покупка хлеба',
            'Билайн',
            'Продукты в магните',
            'Такси до работы',
            'Мегафон интернет',
            'Ужин в ресторане',
            'Проезд в метро'
        ],
        'Категория': [
            'Связь',
            'Еда',
            'Связь',
            'Еда',
            'Транспорт',
            'Связь',
            'Еда',
            'Транспорт'
        ],
        'Сумма': [
            300,
            150,
            500,
            800,
            400,
            600,
            1200,
            100
        ]
    })

    file = 'test_transactions.xlsx'
    df.to_excel(file, index=False)

    yield file

    if os.path.exists(file):
        os.remove(file)

