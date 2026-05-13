import json
import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
import requests
from dotenv import load_dotenv


load_dotenv()


logger = logging.getLogger(__name__)

def load_user_settings() -> Dict[str, List[str]]:
    """
    Загрузка пользовательских настроек из файла user_settings.json
    """
    settings_path = Path('user_settings.json')

    default_settings: Dict[str, List[str]] = {
        "user_currencies": ["USD", "EUR"],
        "user_stocks": ["AAPL", "AMZN", "GOOGL", "MSFT", "TSLA"]
    }

    try:
        if settings_path.exists():
            with open(settings_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                logger.info("Настройки успешно загружены из user_settings.json")
                return settings
        else:
            logger.warning("Файл user_settings.json не найден, используются настройки по умолчанию")
            return default_settings
    except Exception as e:
        logger.error(f"Ошибка при загрузке настроек: {e}")
        return default_settings


def get_greeting() -> str:
    """
    Функция, которая приветствует в зависимости от текущего времени суток.
    Возвращает строку приветствия в зависимости от времени.
    """
    current_hour = datetime.now().hour

    if 0 <= current_hour < 6 or 22 <= current_hour <= 23:
        return "Доброй ночи"
    elif 17 <= current_hour <= 22:
        return "Добрый вечер"
    elif 7 <= current_hour <= 11:
        return "Доброе утро"
    else:
        return "Добрый день"


def get_date_range(input_date: datetime) -> Tuple[datetime, datetime]:
    """
    Получение диапазона дат для анализа (с начала месяца по входную дату)
    """
    start_of_month = input_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    end_date = input_date.replace(hour=23, minute=59, second=59)

    return start_of_month, end_date


def read_excel(excel_file_path: str) -> Optional[List[Dict[str, Any]]]:
    """ Преобразование Excel файла в список словарей с транзакциями """
    path = Path(excel_file_path)
    if not path.exists():
        print(f"❌ Excel файл не найден: {excel_file_path}")
        return None

    try:
        df = pd.read_excel(path)

        excel_dict: List[Dict[str, Any]] = df.to_dict(orient='records')
        logger.info(f"Загружено {len(excel_dict)} транзакций из {path.name}")
        return excel_dict
    except Exception as e:
        print(f"Ошибка при чтении файла Excel: {e}")
        return None


def parse_date(date_value: Any) -> Optional[datetime]:
    """Преобразует дату из разных форматов в datetime"""
    # перестраховка на случай неверного формата даты
    if date_value is None:
        return None

        # Если уже datetime
    if isinstance(date_value, datetime):
        return date_value

        # Если строка
    if isinstance(date_value, str):
        formats = [
            '%Y-%m-%d %H:%M:%S',  # 2021-12-31 16:44:00
            '%d.%m.%Y %H:%M:%S',  # 31.12.2021 16:44:00
            '%d.%m.%Y %H:%M',  # 31.12.2021 16:44
            '%Y-%m-%d',  # 2021-12-31
            '%d.%m.%Y',  # 31.12.2021
            '%Y/%m/%d',  # 2021/12/31
            '%d/%m/%Y'  # 31/12/2021
            ]
        for fmt in formats:
            try:
                dt = datetime.strptime(date_value, fmt)
                return dt
            except ValueError:
                continue

    if hasattr(date_value, 'to_pydatetime'):
        result = date_value.to_pydatetime()
        if isinstance(result, datetime):
            return result

    return None


def filter_transactions_by_date(
    transactions: List[Dict[str, Any]],
    start_date: datetime,
    end_date: datetime
) -> List[Dict[str, Any]]:
    """Фильтрация транзакций по диапазону дат"""
    if not transactions:
        return []

    filtered = []

    for transaction in transactions:
        date_value = transaction.get('date') or transaction.get('Дата') or transaction.get('Дата операции')

        transaction_date = parse_date(date_value)

        if transaction_date and start_date <= transaction_date <= end_date:
            filtered.append(transaction)

    logger.info(f"Отфильтровано {len(filtered)} транзакций за период")
    return filtered


# Статистика по картам
def get_card_number(t: Dict) -> str:
    """Извлекает номер карты из транзакции"""
    return str(t.get('card_number') or t.get('Номер карты') or t.get('Карта', ''))


def get_amount(t: Dict) -> float:
    """Извлекает сумму из транзакции"""
    return float(t.get('amount') or t.get('Сумма') or t.get('Сумма операции', 0))


def calculate_card_stats(transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Расчет статистики по картам"""
    if not transactions:
        return []

    card_totals: Dict[str, float] = {}
    for t in transactions:
        card = get_card_number(t)
        amount = get_amount(t)
        if card:
            card_totals[card] = card_totals.get(card, 0) + amount

    return [{
        "last_4_digits": card[-4:] if len(card) >= 4 else card,
        "total_spent": round(total, 2),
        "cashback": int(total // 100)
    } for card, total in card_totals.items()]


# Топ-5 транзакций
def get_description(t: Dict) -> str:
    """Извлекает описание из транзакции"""
    return str(t.get('description') or t.get('Описание') or t.get('Назначение платежа', ''))


def get_date(t: Dict) -> str:
    """Извлекает дату из транзакции"""
    return str(t.get('date') or t.get('Дата') or t.get('Дата операции', ''))


def get_top_transactions(transactions: List[Dict[str, Any]], top_n: int = 5) -> List[Dict[str, Any]]:
    """Получение топ-N транзакций по сумме платежа """
    if not transactions:
        return []

    sorted_transactions = sorted(transactions, key=lambda t: get_amount(t), reverse=True)

    top_transactions = []
    for transaction in sorted_transactions[:top_n]:
        amount = get_amount(transaction)
        card = get_card_number(transaction)

        top_transactions.append({
            "date": get_date(transaction),
            "amount": round(amount, 2),
            "description": get_description(transaction),
            "card_last_4": card[-4:] if len(card) >= 4 else card,
        })

    logger.info(f"Сформирован топ-{len(top_transactions)} транзакций")
    return top_transactions


def get_currency_rates(currencies: List[str]) -> Dict[str, float]:
    """ Получение курсов валют через API """

    # Загружаем настройки пользователя
    settings = load_user_settings()
    currencies = settings.get('user_currencies', ['USD', 'EUR'])

    apy_key = os.getenv("EXCHANGE_RATE_API_KEY")

    rates = {}
    # Базовая валюта, от которой мы считаем.
    base_currency = 'RUB'

    url = f"https://v6.exchangerate-api.com/v6/{apy_key}/latest/{base_currency}"

    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()

        data = response.json()

        if data.get('result') == 'success':
            all_rates = data.get('conversion_rates', {})

            for currency in currencies:
                currency_upper = currency.upper()
                if currency_upper in all_rates:
                    rates[currency_upper] = round(all_rates[currency_upper], 4)
                    logger.info(f"Курс {currency_upper}: {rates[currency_upper]} RUB")

                else:
                    logger.warning(f"Курс для {currency_upper} не найден")
                    rates[currency_upper] = 0.0

        else:
            error_type = data.get('error-type', 'Неизвестная ошибка')
            logger.error(f"Ошибка API: {error_type}")
            rates = {currency.upper(): 0.0 for currency in currencies}

    except Exception as e:
        logger.error(f"Ошибка при запросе: {e}")
        rates = {currency.upper(): 0.0 for currency in currencies}

    return rates


def get_stock_prices(stocks: List[str]) -> Dict[str, float]:
    """Получение цен акций S&P500"""
    settings = load_user_settings()
    stocks = settings.get('user_stocks', ['AAPL', 'AMZN', 'GOOGL', 'MSFT', 'TSLA'])

    api_key = os.getenv("ALPHA_VANTAGE_API_KEY")

    prices = {}

    for stock in stocks:
        try:
            url = "https://www.alphavantage.co/query"
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': stock,
                'apikey': api_key
            }

            logger.info(f"Запрос цены для {stock}...")
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            if 'Global Quote' in data and data['Global Quote']:
                price = float(data['Global Quote'].get('05. price', 0))
                prices[stock] = round(price, 2)
                logger.info(f"Цена {stock}: ${prices[stock]}")
            else:
                logger.warning(f"Не удалось получить цену для {stock}")
                prices[stock] = 0.0

        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка сети при запросе {stock}: {e}")
            prices[stock] = 0.0
        except Exception as e:
            logger.error(f"Ошибка при получении цены {stock}: {e}")
            prices[stock] = 0.0

    return prices


def generate_analytics_data(date_string: str, excel_path: str = 'data/operations.xlsx') -> Dict[str, Any]:
    """Главная функция принимает на вход дату для формирования аналитических даннных для JSON-ответа"""
    logger.info(f"Запуск генерации аналитики для даты: {date_string}")
    # Ввод даты
    input_datetime = datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S')

    # Получение диапазона дат
    start_date, end_date = get_date_range(input_datetime)
    logger.info(f"Диапазон анализа: {start_date.date()} - {end_date.date()}")

    # Получение приветствия
    greeting = get_greeting()

    # Загрузка настроек пользователя
    settings = load_user_settings()
    user_currencies = settings.get('user_currencies', ['USD', 'EUR'])
    user_stocks = settings.get('user_stocks', ['AAPL', 'AMZN', 'GOOGL', 'MSFT', 'TSLA'])

    # Загрузка транзакций из Excel
    all_transactions = read_excel(excel_path)

    if all_transactions is None:
        all_transactions = []
        logger.warning("Не удалось загрузить транзакции")

    # Фильтрация транзакций по датам
    filtered_transactions = filter_transactions_by_date(all_transactions, start_date, end_date)

    # Расчет статистики по картам
    card_stats = calculate_card_stats(filtered_transactions)

    # Получение топ-5 транзакций
    top_transactions = get_top_transactions(filtered_transactions, 5)

    # Получение курсов валют
    currency_rates = get_currency_rates(user_currencies)

    # Получение цен акций
    stock_prices = get_stock_prices(user_stocks)

    # Формирование итогового JSON-ответа
    response = {
        "greeting": greeting,
        "cards": card_stats,
        "top_transactions": top_transactions,
        "currency_rates": currency_rates,
        "stock_prices": stock_prices,
        "analysis_period": {
            "start_date": start_date.strftime('%Y-%m-%d'),
            "end_date": end_date.strftime('%Y-%m-%d'),
        }
    }

    logger.info("Аналитика успешно сгенерирована")
    return response
