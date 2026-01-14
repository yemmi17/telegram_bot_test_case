"""
Модуль для получения данных о курсе валют с сайта Центробанка
"""
from datetime import datetime, timedelta
from pycbrf import ExchangeRates
import pandas as pd
from typing import Optional


class CurrencyDataFetcher:
    """Класс для получения и обработки данных о курсе валют"""
    
    def __init__(self):
        # Инициализация не требуется, ExchangeRates создается при каждом запросе
        pass
    
    def get_usd_rate(self, date: datetime) -> Optional[float]:
        """
        Получить курс USD к RUB на указанную дату
        
        Args:
            date: Дата для получения курса
            
        Returns:
            Курс USD к RUB или None если данные недоступны
        """
        try:
            rates = ExchangeRates(date)
            # В pycbrf 1.1.0 rates.rates - это список объектов ExchangeRate
            # Ищем USD в списке
            for rate_obj in rates.rates:
                if hasattr(rate_obj, 'code') and rate_obj.code == 'USD':
                    return float(rate_obj.value)
            return None
        except Exception as e:
            print(f"Ошибка при получении курса на {date}: {e}")
            return None
    
    def fetch_data_range(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
        Получить данные о курсе USD за период
        
        Args:
            start_date: Начальная дата
            end_date: Конечная дата
            
        Returns:
            DataFrame с колонками: date, usd_rate
        """
        data = []
        current_date = start_date
        failed_attempts = 0
        max_failed_attempts = 5
        
        while current_date <= end_date:
            rate = self.get_usd_rate(current_date)
            if rate is not None:
                data.append({
                    'date': current_date.date(),
                    'usd_rate': rate
                })
                failed_attempts = 0  # Сбрасываем счетчик при успехе
            else:
                failed_attempts += 1
                if failed_attempts >= max_failed_attempts:
                    print(f"Прервано после {max_failed_attempts} неудачных попыток")
                    break
            
            current_date += timedelta(days=1)
            
            # Небольшая задержка для избежания rate limiting
            if len(data) % 10 == 0:
                import time
                time.sleep(0.1)
        
        df = pd.DataFrame(data)
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            df = df.reset_index(drop=True)
        
        return df
    
    def supplement_data(self, existing_data: pd.DataFrame, cutoff_date: datetime) -> pd.DataFrame:
        """
        Дополнить существующие данные новыми данными с Центробанка
        
        Args:
            existing_data: DataFrame с существующими данными (колонки: date, usd_rate)
            cutoff_date: Дата, до которой данные уже есть (01.11.2021)
            
        Returns:
            Объединенный DataFrame с дополненными данными
        """
        # Преобразуем cutoff_date если это строка
        if isinstance(cutoff_date, str):
            cutoff_date = datetime.strptime(cutoff_date, '%d.%m.%Y')
        
        # Получаем данные с даты после cutoff_date до сегодня
        start_date = cutoff_date + timedelta(days=1)
        end_date = datetime.now()
        
        print(f"Получение данных с {start_date.date()} по {end_date.date()}")
        new_data = self.fetch_data_range(start_date, end_date)
        
        if new_data.empty:
            print("Не удалось получить новые данные")
            return existing_data
        
        # Объединяем данные
        if existing_data.empty:
            return new_data
        
        # Убеждаемся, что колонка date в datetime формате
        existing_data['date'] = pd.to_datetime(existing_data['date'])
        new_data['date'] = pd.to_datetime(new_data['date'])
        
        # Объединяем и удаляем дубликаты
        combined = pd.concat([existing_data, new_data], ignore_index=True)
        combined = combined.drop_duplicates(subset=['date'], keep='last')
        combined = combined.sort_values('date').reset_index(drop=True)
        
        return combined

