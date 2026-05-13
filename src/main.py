import os
import json
import logging
import sys
from pathlib import Path
from dotenv import load_dotenv

from reports import spending_by_category
from services import search_transactions
from utils import generate_analytics_data, load_user_settings

sys.path.insert(0, str(Path(__file__).parent.parent))


def setup_logging():
    """Настройка логирования"""
    log_dir = Path(__file__).parent.parent / 'logs'
    log_dir.mkdir(exist_ok=True)

    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler(log_dir / 'main.log', mode='w', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )


def setup_environment():
    """Загрузка переменных окружения"""
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        setup_logging()


def main():
    """Главная функция приложения"""
    setup_logging()
    setup_environment()
    logger = logging.getLogger(__name__)
    logger.info("Запуск программы")


    while True:
        print("\n" + "=" * 50)
        print("        Добро пожаловать в приложение")
        print("=" * 50)
        print("1. Гланая страница. Полный анализ транзакций")
        print("2. Поиск транзакций по описанию")
        print("3. Отчёт по категории (за последние 3 месяца)")
        print("4. Настройки")
        print("0. Выход")
        print("=" * 50)


        choice = input("Выберите действие (0-4): ").strip()

        if choice == '0':
            print("До свидания!")
            logger.info("Программа завершена")
            break

        elif choice == '1':
            print("Выбран полный анализ транзакций")
            date = input("Дата (ГГГГ-ММ-ДД ЧЧ:ММ:СС): ").strip()
            file_path = input("Путь к Excel файлу (Enter - по умолчанию): ").strip()

            if not file_path:
                file_path = "data/operations.xlsx"

            try:
                result = generate_analytics_data(date, file_path)

                print(json.dumps(result, ensure_ascii=False, indent=2))

                logger.info("Аналитика выполнена успешно")

            except Exception as e:
                print(f"❌ Ошибка: {e}")
                logger.error(f"Ошибка в аналитике: {e}")


        elif choice == '2':
            print("Выбран поиск транзакций")

            file_path = input("Путь к Excel файлу (Enter - по умолчанию): ").strip()

            if not file_path:
                file_path = 'data/operations.xlsx'
                print(f"   Используем файл по умолчанию: {file_path}")


            query = input("Поисковый запрос: ").strip()

            if not query:
                print("❌ Ошибка: поисковый запрос не может быть пустым!")
                continue

            try:
                result = search_transactions(file_path, query)

                if isinstance(result, str):
                    data = json.loads(result)
                    if data.get('status') == 'error':
                        print(f"Ошибка {data.get('message')}")
                        continue
                    transactions = data.get('transactions', [])
                else:
                    transactions = result

                print(f"\n✅ Найдено: {len(transactions)}")

                for t in transactions:
                    print(t)

                logger.info(f"Поиск по ключевому слову {query} завершен")

            except Exception as e:
                print(f"❌ Ошибка: {e}")
                logger.error(f"Ошибка при поиске: {e}")

        elif choice == '3':
            print("Выбран отчет по категории")

            file_path = input("Путь к Excel файлу (Enter - по умолчанию): ").strip()

            if not file_path:
                file_path = 'data/operations.xlsx'
                print(f"   Используем файл по умолчанию: {file_path}")

            category = input("Категория (Еда, Связь, Транспорт...): ").strip()

            if not category:
                print("❌ Ошибка: категория не может быть пустой!")
                continue

            date = input("Дата (ГГГГ-ММ-ДД, Enter - сегодня): ").strip()

            if not date:
                date = None

            try:
                result = spending_by_category(file_path, category, date)

                print(f"\n✅ Найдено транзакций: {len(result)}")

                for t in result:
                    print(t)

                logger.info(f"Отчёт по категории '{category}' выполнен")

            except Exception as e:
                print(f"Ошибка: {e}")
                logger.error(f"Ошибка в отчёте: {e}")

        elif choice == '4':
            print("\n⚙️ НАСТРОЙКИ")

            settings = load_user_settings()
            print(f"   Валюты: {', '.join(settings.get('user_currencies', []))}")
            print(f"   Акции: {', '.join(settings.get('user_stocks', []))}")

        else:
            print("❌ Неверный выбор. Введите 0, 1, 2, 3 или 4.")

        input("\nНажмите Enter для продолжения...")


if __name__ == "__main__":
    main()