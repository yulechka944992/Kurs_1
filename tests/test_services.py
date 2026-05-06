import pytest
import json
import pandas as pd

from src.services import search_transactions


def test_search_found(excel_file):
    """Тест нормальной работы функции"""
    result = json.loads(search_transactions(excel_file, 'связь'))
    assert result['total_found'] == 3

def test_search_not_found(excel_file):
    """Тест несуществующего слова в транзакции"""
    result = json.loads(search_transactions(excel_file, 'бусики'))
    assert result['total_found'] == 0

def test_empty_query(excel_file):
    """Тест на пустой поиск"""
    result = json.loads(search_transactions(excel_file, ''))
    assert result['status'] == 'error'

def test_file_not_found():
    """Тест отсутствия Excel-файла"""
    result = json.loads(search_transactions('no_file.xlsx', 'мтс'))
    assert result['status'] == 'error'
