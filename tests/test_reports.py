import pytest

from src.reports import spending_by_category


def test_spending_by_category(excel_file):
    """Тест нормальной работы функции со всеми вводными данными"""
    result = spending_by_category(excel_file, category='Еда', date='2024-03-20')

    assert len(result) > 0
    assert all('Категория' in item for item in result)
    assert all(item['Категория'] == 'Еда' for item in result)

def test_spending_by_not_category(excel_file):
    """Тест 2: Категория, которой нет в данных."""
    result =  spending_by_category(excel_file, category='бусики')
    assert len(result) == 0
    assert result == []
