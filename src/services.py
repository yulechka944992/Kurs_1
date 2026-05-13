import json
import logging
import os
import sys

import pandas as pd

# current_dir = os.path.dirname(os.path.abspath(__file__))
# log_path = os.path.join(current_dir, "../logs/services.log")
#
# logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO)
# file_handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
# file_handler.setLevel(logging.INFO)
# file_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
# file_handler.setFormatter(file_formatter)
# logger.addHandler(file_handler)

logger = logging.getLogger(__name__)

def search_transactions(excel_file_path: str, search_query: str) -> str:
    """Поиск транзакций по строке в описании или категории из Excel файла"""
    try:
        logger.info(f"Поиск: {search_query} в файле {excel_file_path}")
        df = pd.read_excel(excel_file_path)
        df.columns = df.columns.str.lower()
        logger.info(f"Столбцы приведены к нижнему регистру: {list(df.columns)}")
    except Exception as e:
        logger.error(f"Файл не найден: {e}")
        return json.dumps(
            {"status": "error", "message": f"Файл {excel_file_path} не найден"}, ensure_ascii=False, indent=4
        )

    if "description" in df.columns:
        desc = "description"
    elif "описание" in df.columns:
        desc = "описание"
    else:
        logger.error(f"Нет столбца description/описание в {list(df.columns)}")
        return json.dumps({"status": "error", "message": "Нет столбца с описанием"})

    cat = None
    if "category" in df.columns:
        cat = "category"
    elif "категория" in df.columns:
        cat = "категория"
    else:
        logger.warning("Нет столбца с категорией, ищем только по описанию")

    if not search_query or search_query.strip() == "":
        logger.warning("Пустой запрос")
        return json.dumps({"status": "error", "message": "Запрос не может быть пустым"})

    found_transactions = []
    try:
        for index, row in df.iterrows():
            description_text = str(row[desc])

            if search_query.lower() in description_text.lower():
                found_transactions.append(row.to_dict())
            elif cat and search_query.lower() in str(row[cat]).lower():
                found_transactions.append(row.to_dict())
    except Exception as e:
        logger.error(f"Ошибка при поиске: {str(e)}")
        return json.dumps({"status": "error", "message": f"Ошибка при поиске: {str(e)}", "query": search_query})

    logger.info(f"Найдено: {len(found_transactions)}")
    return json.dumps(
        {
            "status": "success",
            "query": search_query,
            "total_found": len(found_transactions),
            "transactions": found_transactions,
        },
        ensure_ascii=False,
        indent=4,
        default=str,
    )


# result = search_transactions("data/operations.xlsx", "пополнения")
# print(result)
