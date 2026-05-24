import json
from datetime import datetime
from unittest.mock import patch, mock_open, MagicMock, Mock

import pytest

from src.utils import load_user_settings, get_greeting, get_date_range, read_excel, parse_date, \
    filter_transactions_by_date, get_card_number, get_amount, calculate_card_stats, get_description, get_date, \
    get_top_transactions, get_currency_rates, get_stock_prices, generate_analytics_data


def test_load_user_settings():
    """Тест загрузки файла пользовательских настроек"""
    test_settings = {"user_currencies": ["USD"], "user_stocks": ["AAPL"]}

    with patch('src.utils.Path') as mock_path:
        mock_path.return_value.exists.return_value = True

        with patch('src.utils.open', mock_open(read_data=json.dumps(test_settings))):
            result = load_user_settings()

    assert result == test_settings

def test_load_user_settings_not_exists():
    """Тест отсутствия файла, установка настроек по умолчанию"""
    with patch('src.utils.Path') as mock_path:
        mock_path.return_value.exists.return_value = False
        result = load_user_settings()

    expected = {
        "user_currencies": ["USD", "EUR"], "user_stocks": ["AAPL", "AMZN", "GOOGL", "MSFT", "TSLA"]
    }

    assert result == expected


@pytest.mark.parametrize("hour, expected", [
    (2, "Доброй ночи"),
    (10, "Доброе утро"),
    (15, "Добрый день"),
    (20, "Добрый вечер")
])
def test_get_greetings(hour, expected):
    """Тест корректной работы функции приветствия"""
    with patch('src.utils.datetime') as mock_datetime:
        mock_datetime.now.return_value = datetime(2022, 1, 1, hour, 0, 0, 0)
        mock_datetime.datetime = datetime
        assert get_greeting() == expected


def test_get_date_range():
    """Тест: функция получает на вход дату и отдает диапазон с начала месяца по входную дату"""
    input_date = datetime(2021, 10, 5, 15, 30, 45)
    start, end = get_date_range(input_date)
    assert start == datetime(2021, 10, 1, 0, 0, 0)
    assert end == datetime(2021, 10, 5, 23, 59, 59)

def test_get_date_range_last_day():
    """Тест: при вводе последнего дня месяца, функция отдает корректный диапазон"""
    input_date = datetime(2021, 10, 31, 15, 30, 45)
    start, end = get_date_range(input_date)
    assert start == datetime(2021, 10, 1, 0, 0, 0)
    assert end == datetime(2021, 10, 31, 23, 59, 59)

@patch("pandas.read_excel")
def test_read_excel(mock_read_excel, tmp_path):
    mock_df = MagicMock()
    mock_df.to_dict.return_value = [{"test": "data"}]
    mock_read_excel.return_value = mock_df

    excel_path = tmp_path / "test.xlsx"
    excel_path.touch()
    result = read_excel(str(excel_path))

    assert result is not None
    assert len(result) == 1
    assert result[0]["test"] == "data"

def test_read_excel_not_found():
    """"""
    result = read_excel("/non/existent/path/file.xlsx")
    assert result is None

def test_parse_date():
    """Тест корректной работы функции преобразования даты в datetime"""
    result = parse_date("31.12.2021")
    assert result == datetime(2021, 12, 31, 0, 0, 0)

def test_parse_date_none():
    """Тест: None на входе"""
    result = parse_date(None)
    assert result is None

def test_filter_transactions_by_date():
    """Тест: фильтрация работает правильно"""
    transactions = [
        {'date': datetime(2021, 12, 15), 'amount': 100},
        {'date': datetime(2021, 11, 15), 'amount': 100},
        {'Дата': datetime(2021, 12, 20), 'amount': 300}
    ]
    start = datetime(2021, 12, 1)
    end = datetime(2021, 12, 31)

    result = filter_transactions_by_date(transactions, start, end)

    assert len(result) == 2
    assert result[0]['date'] == datetime(2021, 12, 15)
    assert result[1]['Дата'] == datetime(2021, 12, 20)

def test_filter_transactions_by_date_empty():
    """Тест: пустой список"""
    start = datetime(2021, 12, 1)
    end = datetime(2021, 12, 31)
    result = filter_transactions_by_date([], start, end)
    assert result == []

def test_get_card_number_in_english():
    """Тест поиска номера карты с ключом на английском языке"""
    transaction = {'card_number': '****1234', 'amount': 100}
    assert get_card_number(transaction) == '****1234'

def test_get_card_number_in_russian():
    """Тест с ключом на русском языке"""
    transaction = {'Номер карты': '****5678', 'amount': 200}
    assert get_card_number(transaction) == '****5678'

def test_get_amount_in_russian():
    """Тест поиска суммы операции с ключом на русском языке"""
    transaction = {'Сумма операции': 2500.75}
    assert get_amount(transaction) == 2500.75

def test_get_amount_in_english():
    """Тест с ключом на английском языке"""
    transaction = {'amount': 1500.50}
    assert get_amount(transaction) == 1500.50

@pytest.mark.parametrize("transactions, expected", [
    ([], []),
    ([{"card_number": "****1234", "amount": 5000}],
     [{"last_4_digits": "1234", "total_spent": 5000.00, "cashback": 50}]),
    ([{"card_number": "****1234", "amount": 5000}, {"card_number": "****1234", "amount": 3000}],
     [{"last_4_digits": "1234", "total_spent": 8000.00, "cashback": 80}]),
    ([{"card_number": "****1234", "amount": 5000}, {"card_number": "****5678", "amount": 3000}],
     [{"last_4_digits": "1234", "total_spent": 5000.00, "cashback": 50},
      {"last_4_digits": "5678", "total_spent": 3000.00, "cashback": 30}]),
    ([{"card_number": "****1234", "amount": 150}], [{"last_4_digits": "1234", "total_spent": 150.00, "cashback": 1}]),
    ([{"card_number": "****1234", "amount": 50}], [{"last_4_digits": "1234", "total_spent": 50.00, "cashback": 0}]),
    ([{"Номер карты": "****1234", "Сумма операции": 5000}],
     [{"last_4_digits": "1234", "total_spent": 5000.00, "cashback": 50}]),
    ([{"card_number": "123", "amount": 1000}], [{"last_4_digits": "123", "total_spent": 1000.00, "cashback": 10}]),
])
def test_calculate_card_stats(transactions, expected):
    """Параметризированный тест для разных сценариев"""
    result = calculate_card_stats(transactions)
    if len(result) > 1:
        result = sorted(result, key=lambda x: x["last_4_digits"])
        expected = sorted(expected, key=lambda x: x["last_4_digits"])
    assert result == expected

def test_get_description_english():
    """Тест поиска описания транзакции на английском"""
    transaction = {'description': 'Выплата'}
    assert get_description(transaction) == 'Выплата'

def test_get_description_russian():
    """Тест поиска описания транзакции на русском"""
    transaction = {'Описание': 'Перевод'}
    assert get_description(transaction) == 'Перевод'

def test_get_date_english():
    """"""
    transaction = {'date': '2021.12.10'}
    assert get_date(transaction) == '2021.12.10'

def test_get_date_russian():
    transaction = {'Дата операции': '2021.11.25'}
    assert get_date(transaction) == '2021.11.25'

def test_get_top_transactions_empty():
    """Тест: пустой список"""
    result = get_top_transactions([])
    assert result == []


def test_get_top_transactions_sorted():
    """Тест: правильная сортировка по убыванию"""
    transactions = [
        {'card_number': '****1234', 'amount': 1000, 'date': '2021-12-01', 'description': 'Small'},
        {'card_number': '****1234', 'amount': 5000, 'date': '2021-12-02', 'description': 'Medium'},
        {'card_number': '****1234', 'amount': 10000, 'date': '2021-12-03', 'description': 'Large'},
    ]
    result = get_top_transactions(transactions, top_n=2)

    assert len(result) == 2
    assert result[0]['amount'] == 10000  # самая большая
    assert result[0]['description'] == 'Large'
    assert result[1]['amount'] == 5000

@patch("src.utils.load_user_settings")
@patch("src.utils.requests.get")
def test_get_currency_rates(mock_get, mock_load_settings):
    """"""
    mock_load_settings.return_value = {'user_currencies': ['USD', 'EUR']}

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'result': 'success',
            'conversion_rates': {
                'USD': 0.012,
                'EUR': 0.011,
                'GBP': 0.010
            }
    }

    mock_get.return_value = mock_response

    result = get_currency_rates(['USD', 'EUR'])

    assert result == {'USD': 0.012, 'EUR': 0.011}
    mock_get.assert_called_once()


@patch("src.utils.load_user_settings")
@patch("src.utils.requests.get")
def test_get_currency_rates_api_error(mock_get, mock_load_settings):
    """Тест: Ошибка API"""
    mock_load_settings.return_value = {'user_currencies': ['USD', 'EUR']}

    mock_response = Mock()
    mock_response.json.return_value = {
        'result': 'error',
        'error-type': 'invalid-api-key'
    }
    mock_get.return_value = mock_response

    result = get_currency_rates(['USD', 'EUR'])

    assert result == {'USD': 0.0, 'EUR': 0.0}

@patch("src.utils.load_user_settings")
@patch("src.utils.requests.get")
def test_get_stock_prices(mock_get, mock_load_settings):
    """"""
    mock_load_settings.return_value = {'user_stocks': ['AAPL', 'GOOGL']}

    def mock_response(url, params, timeout):
        mock_resp = Mock()
        symbol = params['symbol']

        if symbol == 'AAPL':
            mock_resp.json.return_value = {
                'Global Quote': {
                    '05. price': '175.3421'
                }
            }
        elif symbol == 'GOOGL':
            mock_resp.json.return_value = {
                'Global Quote': {
                    '05. price': '136.7890'
                }
            }
        mock_resp.status_code = 200
        return mock_resp

    mock_get.side_effect = mock_response

    result = get_stock_prices(['AAPL', 'GOOGL'])

    assert result == {'AAPL': 175.34, 'GOOGL': 136.79}

def test_generate_analytics_data_simple():
    """Просто проверяем, что функция не падает и возвращает словарь"""
    with patch('src.utils.read_excel') as mock_read:
        mock_read.return_value = []

        result = generate_analytics_data('2021-01-20 12:00:00')

        assert isinstance(result, dict)
        assert 'greeting' in result
        assert 'cards' in result


@patch('src.utils.get_stock_prices')
@patch('src.utils.get_currency_rates')
@patch('src.utils.get_top_transactions')
@patch('src.utils.calculate_card_stats')
@patch('src.utils.filter_transactions_by_date')
@patch('src.utils.read_excel')
@patch('src.utils.load_user_settings')
@patch('src.utils.get_greeting')
@patch('src.utils.get_date_range')
def test_generate_analytics_data_structure(
        mock_range, mock_greeting, mock_settings, mock_excel,
        mock_filter, mock_cards, mock_top, mock_currency, mock_stocks
):
    """Простой тест - проверка только структуры"""

    mock_range.return_value = (datetime(2024, 1, 1), datetime(2024, 1, 31))
    mock_greeting.return_value = "Hello"
    mock_settings.return_value = {}
    mock_excel.return_value = []
    mock_filter.return_value = []
    mock_cards.return_value = {}
    mock_top.return_value = []
    mock_currency.return_value = {}
    mock_stocks.return_value = {}

    result = generate_analytics_data('2024-01-20 12:00:00')

    expected_keys = {'greeting', 'cards', 'top_transactions',
                     'currency_rates', 'stock_prices', 'analysis_period'}
    assert set(result.keys()) == expected_keys
