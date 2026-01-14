"""
Скрипт для тестирования компонентов бота
"""
from datetime import datetime
import pandas as pd
from data_fetcher import CurrencyDataFetcher
from predictor import CurrencyPredictor


def test_data_fetcher():
    """Тест модуля получения данных"""
    print("=" * 50)
    print("Тест модуля получения данных")
    print("=" * 50)
    
    fetcher = CurrencyDataFetcher()
    
    # Тест получения курса на сегодня
    today = datetime.now()
    rate = fetcher.get_usd_rate(today)
    print(f"Курс USD на {today.date()}: {rate}")
    
    # Тест получения данных за последние 7 дней
    end_date = datetime.now()
    start_date = end_date - pd.Timedelta(days=7)
    data = fetcher.fetch_data_range(start_date, end_date)
    print(f"\nДанные за последние 7 дней:")
    print(data)
    
    # Тест дополнения данных
    cutoff_date = datetime(2021, 11, 1)
    existing_data = pd.DataFrame(columns=['date', 'usd_rate'])
    supplemented = fetcher.supplement_data(existing_data, cutoff_date)
    print(f"\nВсего записей после дополнения: {len(supplemented)}")
    if len(supplemented) > 0:
        print(f"Первая дата: {supplemented['date'].min()}")
        print(f"Последняя дата: {supplemented['date'].max()}")


def test_predictor():
    """Тест модуля прогнозирования"""
    print("\n" + "=" * 50)
    print("Тест модуля прогнозирования")
    print("=" * 50)
    
    # Создаем тестовые данные
    fetcher = CurrencyDataFetcher()
    cutoff_date = datetime(2021, 11, 1)
    existing_data = pd.DataFrame(columns=['date', 'usd_rate'])
    
    # Получаем данные за последние 90 дней для теста
    end_date = datetime.now()
    start_date = end_date - pd.Timedelta(days=90)
    test_data = fetcher.fetch_data_range(start_date, end_date)
    
    if len(test_data) < 30:
        print("Недостаточно данных для теста (нужно минимум 30 записей)")
        return
    
    print(f"Используется {len(test_data)} записей для обучения")
    
    predictor = CurrencyPredictor()
    ts = predictor.prepare_data(test_data)
    predictor.fit_model(ts, method='arima')
    
    # Генерируем прогноз
    forecast = predictor.predict_with_confidence(days=7, confidence=0.95)
    print("\nПрогноз на ближайшую неделю:")
    print(forecast.to_string())


if __name__ == '__main__':
    try:
        test_data_fetcher()
        test_predictor()
        print("\n" + "=" * 50)
        print("Все тесты завершены!")
        print("=" * 50)
    except Exception as e:
        print(f"\nОшибка при тестировании: {e}")
        import traceback
        traceback.print_exc()

