"""
Модуль для работы с Google Sheets
"""
import gspread
from google.auth.transport.requests import Request
import pandas as pd
from typing import Optional
import os
import pickle


class GoogleSheetsManager:
    """Класс для работы с Google Sheets"""
    
    def __init__(self, token_file: str = 'token.pickle', spreadsheet_name: str = None, spreadsheet_url: str = None):
        """
        Инициализация менеджера Google Sheets
        
        Args:
            token_file: Путь к файлу с OAuth токеном (token.pickle)
            spreadsheet_name: Название таблицы Google Sheets (альтернатива spreadsheet_url)
            spreadsheet_url: URL таблицы Google Sheets (можно использовать вместо названия)
        """
        self.token_file = token_file
        self.spreadsheet_name = spreadsheet_name
        self.spreadsheet_url = spreadsheet_url
        self.client = None
        self.spreadsheet = None
        self._connect()
    
    def _connect(self) -> None:
        """Подключение к Google Sheets через OAuth токен"""
        try:
            creds = None
            
            # Загружаем сохраненный токен
            if os.path.exists(self.token_file):
                with open(self.token_file, 'rb') as token:
                    creds = pickle.load(token)
            
            # Если токен истек, обновляем его
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                # Сохраняем обновленный токен
                with open(self.token_file, 'wb') as token:
                    pickle.dump(creds, token)
            
            if not creds:
                raise ValueError(
                    f"Токен не найден. Запустите скрипт get_google_token.py для получения токена.\n"
                    f"Или создайте файл {self.token_file} с сохраненным токеном."
                )
            
            # Подключаемся к API
            self.client = gspread.authorize(creds)
            
            # Открываем таблицу
            if self.spreadsheet_url:
                # Открываем по URL
                self.spreadsheet = self.client.open_by_url(self.spreadsheet_url)
            elif self.spreadsheet_name:
                # Открываем по названию
                try:
                    self.spreadsheet = self.client.open(self.spreadsheet_name)
                except gspread.exceptions.SpreadsheetNotFound:
                    # Если таблица не найдена, создаем новую
                    self.spreadsheet = self.client.create(self.spreadsheet_name)
                    print(f"Создана новая таблица: {self.spreadsheet_name}")
            else:
                raise ValueError("Необходимо указать либо spreadsheet_name, либо spreadsheet_url")
            
        except Exception as e:
            print(f"Ошибка при подключении к Google Sheets: {e}")
            raise
    
    def get_or_create_worksheet(self, worksheet_name: str) -> gspread.Worksheet:
        """
        Получить или создать лист в таблице
        
        Args:
            worksheet_name: Название листа
            
        Returns:
            Объект листа
        """
        try:
            worksheet = self.spreadsheet.worksheet(worksheet_name)
        except gspread.exceptions.WorksheetNotFound:
            worksheet = self.spreadsheet.add_worksheet(
                title=worksheet_name,
                rows=1000,
                cols=10
            )
        
        return worksheet
    
    def write_forecast(self, forecast_df: pd.DataFrame, worksheet_name: str = 'Прогноз') -> None:
        """
        Записать прогноз в Google Sheets
        
        Args:
            forecast_df: DataFrame с прогнозом (колонки: date, predicted_rate)
            worksheet_name: Название листа для записи
        """
        worksheet = self.get_or_create_worksheet(worksheet_name)
        
        # Очищаем лист
        worksheet.clear()
        
        # Записываем заголовки
        headers = ['Дата', 'Прогноз курса USD/RUB', 'Нижняя граница', 'Верхняя граница']
        worksheet.append_row(headers)
        
        # Записываем данные
        for _, row in forecast_df.iterrows():
            date_str = row['date'].strftime('%d.%m.%Y')
            predicted = round(row['predicted_rate'], 2)
            
            if 'lower_bound' in row and 'upper_bound' in row:
                lower = round(row['lower_bound'], 2)
                upper = round(row['upper_bound'], 2)
                worksheet.append_row([date_str, predicted, lower, upper])
            else:
                worksheet.append_row([date_str, predicted, '', ''])
        
        print(f"Прогноз записан в лист '{worksheet_name}'")
    
    def read_forecast(self, worksheet_name: str = 'Прогноз') -> Optional[pd.DataFrame]:
        """
        Прочитать прогноз из Google Sheets
        
        Args:
            worksheet_name: Название листа для чтения
            
        Returns:
            DataFrame с прогнозом или None если лист пуст
        """
        try:
            worksheet = self.get_or_create_worksheet(worksheet_name)
            records = worksheet.get_all_records()
            
            if not records:
                return None
            
            df = pd.DataFrame(records)
            df['date'] = pd.to_datetime(df['Дата'], format='%d.%m.%Y')
            
            return df
        except Exception as e:
            print(f"Ошибка при чтении прогноза: {e}")
            return None
    
    def write_historical_data(self, data_df: pd.DataFrame, worksheet_name: str = 'Исторические данные') -> None:
        """
        Записать исторические данные в Google Sheets
        
        Args:
            data_df: DataFrame с историческими данными
            worksheet_name: Название листа для записи
        """
        worksheet = self.get_or_create_worksheet(worksheet_name)
        
        # Очищаем лист
        worksheet.clear()
        
        # Записываем заголовки
        headers = ['Дата', 'Курс USD/RUB']
        worksheet.append_row(headers)
        
        # Записываем данные
        for _, row in data_df.iterrows():
            date_str = pd.to_datetime(row['date']).strftime('%d.%m.%Y')
            rate = round(row['usd_rate'], 2)
            worksheet.append_row([date_str, rate])
        
        print(f"Исторические данные записаны в лист '{worksheet_name}'")

