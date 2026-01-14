"""
Скрипт для инициализации исторических данных
Используйте этот скрипт, если у вас есть данные до 01.11.2021
"""
import pandas as pd
from datetime import datetime


def create_initial_data_file(data_list: list, output_file: str = 'historical_data.csv'):
    """
    Создать файл с историческими данными
    
    Args:
        data_list: Список словарей с ключами 'date' и 'usd_rate'
                  Пример: [{'date': '2020-01-01', 'usd_rate': 61.9057}, ...]
        output_file: Имя выходного файла
    """
    df = pd.DataFrame(data_list)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
    df.to_csv(output_file, index=False)
    print(f"Данные сохранены в {output_file}")
    print(f"Всего записей: {len(df)}")
    print(f"Период: {df['date'].min().date()} - {df['date'].max().date()}")


def create_example_data():
    """Создать пример файла с тестовыми данными"""
    # Пример: создаем несколько записей для демонстрации
    # В реальности здесь должны быть ваши данные до 01.11.2021
    example_data = [
        {'date': '2021-10-25', 'usd_rate': 70.5},
        {'date': '2021-10-26', 'usd_rate': 70.6},
        {'date': '2021-10-27', 'usd_rate': 70.7},
        {'date': '2021-10-28', 'usd_rate': 70.8},
        {'date': '2021-10-29', 'usd_rate': 70.9},
        {'date': '2021-10-30', 'usd_rate': 71.0},
        {'date': '2021-10-31', 'usd_rate': 71.1},
    ]
    
    create_initial_data_file(example_data, 'historical_data_example.csv')
    print("\nПример файла создан. Замените данные на ваши реальные данные.")


if __name__ == '__main__':
    print("Скрипт инициализации данных")
    print("=" * 50)
    print("\nЕсли у вас есть данные до 01.11.2021, отредактируйте этот скрипт")
    print("и добавьте их в список data_list в функции create_initial_data_file()")
    print("\nИли создайте CSV файл вручную со следующей структурой:")
    print("date,usd_rate")
    print("2020-01-01,61.9057")
    print("2020-01-02,61.9057")
    print("...")
    print("\nСоздать пример файла? (y/n): ", end='')
    
    # Для автоматического запуска создаем пример
    create_example_data()

