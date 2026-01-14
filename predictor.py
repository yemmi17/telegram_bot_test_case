"""
Модуль для прогнозирования курса валют
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.preprocessing import MinMaxScaler
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.holtwinters import ExponentialSmoothing
import warnings
warnings.filterwarnings('ignore')


class CurrencyPredictor:
    """Класс для прогнозирования курса валют"""
    
    def __init__(self):
        self.model = None
        self.scaler = MinMaxScaler()
        self.last_date = None
        self.last_rate = None
    
    def prepare_data(self, df: pd.DataFrame) -> pd.Series:
        """
        Подготовка данных для моделирования
        
        Args:
            df: DataFrame с колонками date и usd_rate
            
        Returns:
            Временной ряд курса валюты
        """
        df = df.copy()
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)
        
        # Создаем временной ряд
        ts = df.set_index('date')['usd_rate']
        
        # Сохраняем последние значения
        self.last_date = ts.index[-1]
        self.last_rate = ts.iloc[-1]
        
        return ts
    
    def fit_model(self, ts: pd.Series, method: str = 'arima') -> None:
        """
        Обучение модели прогнозирования
        
        Args:
            ts: Временной ряд
            method: Метод прогнозирования ('arima' или 'holt_winters')
        """
        if method == 'arima':
            # Автоматический подбор параметров ARIMA
            try:
                # Пробуем разные параметры ARIMA
                best_aic = np.inf
                best_model = None
                
                for p in range(0, 3):
                    for d in range(0, 2):
                        for q in range(0, 3):
                            try:
                                model = ARIMA(ts, order=(p, d, q))
                                fitted_model = model.fit()
                                if fitted_model.aic < best_aic:
                                    best_aic = fitted_model.aic
                                    best_model = fitted_model
                            except:
                                continue
                
                if best_model is not None:
                    self.model = best_model
                else:
                    # Fallback на простую модель
                    self.model = ARIMA(ts, order=(1, 1, 1)).fit()
            except Exception as e:
                print(f"Ошибка при обучении ARIMA: {e}")
                # Используем простую модель
                self.model = ARIMA(ts, order=(1, 1, 1)).fit()
        
        elif method == 'holt_winters':
            # Модель Холта-Винтерса
            try:
                self.model = ExponentialSmoothing(
                    ts,
                    trend='add',
                    seasonal=None,
                    seasonal_periods=None
                ).fit()
            except Exception as e:
                print(f"Ошибка при обучении Holt-Winters: {e}")
                # Fallback на ARIMA
                self.fit_model(ts, method='arima')
    
    def predict(self, days: int = 7) -> pd.DataFrame:
        """
        Прогнозирование курса на указанное количество дней
        
        Args:
            days: Количество дней для прогноза
            
        Returns:
            DataFrame с прогнозами (date, predicted_rate)
        """
        if self.model is None:
            raise ValueError("Модель не обучена. Сначала вызовите fit_model()")
        
        # Получаем прогноз
        forecast = self.model.forecast(steps=days)
        
        # Создаем даты для прогноза
        start_date = self.last_date + timedelta(days=1)
        dates = pd.date_range(start=start_date, periods=days, freq='D')
        
        # Формируем результат
        result = pd.DataFrame({
            'date': dates,
            'predicted_rate': forecast.values
        })
        
        return result
    
    def predict_with_confidence(self, days: int = 7, confidence: float = 0.95) -> pd.DataFrame:
        """
        Прогнозирование с доверительными интервалами
        
        Args:
            days: Количество дней для прогноза
            confidence: Уровень доверия (0.95 = 95%)
            
        Returns:
            DataFrame с прогнозами и доверительными интервалами
        """
        if self.model is None:
            raise ValueError("Модель не обучена. Сначала вызовите fit_model()")
        
        # Получаем прогноз с доверительными интервалами
        forecast_result = self.model.get_forecast(steps=days)
        forecast = forecast_result.predicted_mean
        conf_int = forecast_result.conf_int(alpha=1-confidence)
        
        # Создаем даты для прогноза
        start_date = self.last_date + timedelta(days=1)
        dates = pd.date_range(start=start_date, periods=days, freq='D')
        
        # Формируем результат
        result = pd.DataFrame({
            'date': dates,
            'predicted_rate': forecast.values,
            'lower_bound': conf_int.iloc[:, 0].values,
            'upper_bound': conf_int.iloc[:, 1].values
        })
        
        return result

