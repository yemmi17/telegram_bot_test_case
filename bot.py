"""
Основной файл Telegram-бота для прогнозирования курса валют
"""
import os
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv
import pandas as pd

from data_fetcher import CurrencyDataFetcher
from predictor import CurrencyPredictor
from google_sheets import GoogleSheetsManager

# Настройка логирования (сначала, чтобы можно было логировать)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Загружаем переменные окружения
# Пробуем загрузить из .env файла
env_loaded = load_dotenv(override=True)
if not env_loaded:
    logger.warning("Файл .env не найден или пуст. Проверьте наличие файла .env с TELEGRAM_BOT_TOKEN")
else:
    # Проверяем, что токен загрузился
    token_check = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token_check:
        logger.warning("Файл .env загружен, но TELEGRAM_BOT_TOKEN не найден. Проверьте формат файла.")
    else:
        logger.info(f"Токен загружен (длина: {len(token_check)} символов)")


class CurrencyBot:
    """Класс Telegram-бота для прогнозирования курса валют"""
    
    def __init__(self):
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not self.token:
            error_msg = (
                "TELEGRAM_BOT_TOKEN не установлен в переменных окружения.\n"
                "Создайте файл .env в корне проекта со следующим содержимым:\n"
                "TELEGRAM_BOT_TOKEN=ваш_токен_от_BotFather\n\n"
                "Или установите переменную окружения TELEGRAM_BOT_TOKEN"
            )
            raise ValueError(error_msg)
        
        self.data_fetcher = CurrencyDataFetcher()
        self.predictor = CurrencyPredictor()
        
        # Инициализация Google Sheets (опционально, только если указан URL или название)
        spreadsheet_name = os.getenv('GOOGLE_SPREADSHEET_NAME', None)
        spreadsheet_url = os.getenv('GOOGLE_SPREADSHEET_URL', None)
        
        self.sheets_manager = None
        if spreadsheet_name or spreadsheet_url:
            token_file = os.getenv('GOOGLE_TOKEN_FILE', 'token.pickle')
            try:
                self.sheets_manager = GoogleSheetsManager(
                    token_file=token_file,
                    spreadsheet_name=spreadsheet_name,
                    spreadsheet_url=spreadsheet_url
                )
                logger.info("Подключение к Google Sheets успешно")
            except Exception as e:
                logger.warning(f"Не удалось подключиться к Google Sheets: {e}")
                logger.warning("Бот будет работать без Google Sheets")
                self.sheets_manager = None
        else:
            logger.info("Google Sheets не настроен, бот работает без него")
        
        # Загружаем и подготавливаем данные
        self.historical_data = None
        self._load_and_prepare_data()
    
    def _load_and_prepare_data(self) -> None:
        """Загрузка и подготовка данных для модели"""
        try:
            # Пытаемся загрузить данные из файла, если он существует
            if os.path.exists('historical_data.csv'):
                self.historical_data = pd.read_csv('historical_data.csv')
                self.historical_data['date'] = pd.to_datetime(self.historical_data['date'])
                logger.info("Загружены исторические данные из файла")
            else:
                # Создаем пустой DataFrame
                self.historical_data = pd.DataFrame(columns=['date', 'usd_rate'])
                logger.info("Создан пустой DataFrame для исторических данных")
            
            # Дополняем данные с Центробанка
            cutoff_date = datetime(2021, 11, 1)  # 01.11.2021
            self.historical_data = self.data_fetcher.supplement_data(
                self.historical_data,
                cutoff_date
            )
            
            # Сохраняем обновленные данные
            self.historical_data.to_csv('historical_data.csv', index=False)
            logger.info(f"Данные обновлены. Всего записей: {len(self.historical_data)}")
            
            # Обучаем модель
            if len(self.historical_data) > 0:
                ts = self.predictor.prepare_data(self.historical_data)
                self.predictor.fit_model(ts, method='arima')
                logger.info("Модель обучена")
                
                # Генерируем прогноз и записываем в Google Sheets (если настроено)
                if self.sheets_manager:
                    self._update_forecast()
            
        except Exception as e:
            logger.error(f"Ошибка при загрузке данных: {e}")
    
    def _update_forecast(self) -> None:
        """Обновление прогноза и запись в Google Sheets"""
        try:
            if self.predictor.model is None:
                return
            
            # Генерируем прогноз на неделю
            forecast = self.predictor.predict_with_confidence(days=7, confidence=0.95)
            
            # Записываем в Google Sheets
            if self.sheets_manager:
                self.sheets_manager.write_forecast(forecast, worksheet_name='Прогноз')
                logger.info("Прогноз обновлен в Google Sheets")
            
        except Exception as e:
            logger.error(f"Ошибка при обновлении прогноза: {e}")
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /start"""
        welcome_message = (
            "👋 Добро пожаловать в бот прогнозирования курса валют!\n\n"
            "Доступные команды:\n"
            "/start - Начать работу с ботом\n"
            "/forecast - Получить прогноз курса USD/RUB на ближайшую неделю\n"
            "/update - Обновить данные и пересчитать прогноз\n"
            "/help - Показать справку"
        )
        await update.message.reply_text(welcome_message)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /help"""
        help_text = (
            "📊 Бот для прогнозирования курса USD/RUB\n\n"
            "Команды:\n"
            "• /forecast - Получить прогноз на ближайшую неделю\n"
            "• /update - Обновить данные с Центробанка и пересчитать прогноз\n"
            "• /help - Показать эту справку\n\n"
            "Прогноз основан на исторических данных и модели ARIMA."
        )
        await update.message.reply_text(help_text)
    
    async def forecast(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /forecast"""
        try:
            # Пытаемся прочитать прогноз из Google Sheets
            if self.sheets_manager:
                try:
                    forecast_df = self.sheets_manager.read_forecast('Прогноз')
                    if forecast_df is not None and len(forecast_df) > 0:
                        # Форматируем сообщение
                        message = "📈 Прогноз курса USD/RUB на ближайшую неделю:\n\n"
                        
                        for _, row in forecast_df.iterrows():
                            date_str = pd.to_datetime(row['date']).strftime('%d.%m.%Y')
                            # Пробуем разные варианты названий колонок
                            predicted = None
                            if 'Прогноз курса USD/RUB' in row:
                                predicted = row['Прогноз курса USD/RUB']
                            elif 'predicted_rate' in row:
                                predicted = row['predicted_rate']
                            
                            if predicted is not None:
                                message += f"📅 {date_str}: {predicted:.2f} ₽"
                                
                                # Добавляем интервалы если есть
                                if 'Нижняя граница' in row and 'Верхняя граница' in row:
                                    lower = row['Нижняя граница']
                                    upper = row['Верхняя граница']
                                    if pd.notna(lower) and pd.notna(upper):
                                        message += f"\n   (интервал: {lower:.2f} - {upper:.2f} ₽)"
                                elif 'lower_bound' in row and 'upper_bound' in row:
                                    lower = row['lower_bound']
                                    upper = row['upper_bound']
                                    if pd.notna(lower) and pd.notna(upper):
                                        message += f"\n   (интервал: {lower:.2f} - {upper:.2f} ₽)"
                                
                                message += "\n\n"
                        
                        await update.message.reply_text(message)
                        return
                except Exception as e:
                    logger.warning(f"Не удалось прочитать из Google Sheets: {e}")
            
            # Если нет данных в Google Sheets, генерируем прогноз заново
            if self.predictor.model is None:
                await update.message.reply_text(
                    "❌ Модель не обучена. Используйте /update для обновления данных."
                )
                return
            
            forecast = self.predictor.predict_with_confidence(days=7, confidence=0.95)
            
            message = "📈 Прогноз курса USD/RUB на ближайшую неделю:\n\n"
            for _, row in forecast.iterrows():
                date_str = row['date'].strftime('%d.%m.%Y')
                predicted = row['predicted_rate']
                lower = row['lower_bound']
                upper = row['upper_bound']
                message += f"📅 {date_str}: {predicted:.2f} ₽\n"
                message += f"   (интервал: {lower:.2f} - {upper:.2f} ₽)\n\n"
            
            await update.message.reply_text(message)
            
        except Exception as e:
            logger.error(f"Ошибка при получении прогноза: {e}")
            await update.message.reply_text(
                f"❌ Ошибка при получении прогноза: {str(e)}"
            )
    
    async def update(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /update"""
        await update.message.reply_text("🔄 Обновление данных... Это может занять некоторое время.")
        
        try:
            # Обновляем данные
            cutoff_date = datetime(2021, 11, 1)
            self.historical_data = self.data_fetcher.supplement_data(
                self.historical_data,
                cutoff_date
            )
            
            # Сохраняем данные
            self.historical_data.to_csv('historical_data.csv', index=False)
            
            # Переобучаем модель
            if len(self.historical_data) > 0:
                ts = self.predictor.prepare_data(self.historical_data)
                self.predictor.fit_model(ts, method='arima')
                
                # Обновляем прогноз в Google Sheets
                self._update_forecast()
                
                await update.message.reply_text(
                    f"✅ Данные обновлены!\n"
                    f"Всего записей: {len(self.historical_data)}\n"
                    f"Последняя дата: {self.historical_data['date'].max().strftime('%d.%m.%Y')}\n"
                    f"Модель переобучена. Используйте /forecast для получения прогноза."
                )
            else:
                await update.message.reply_text("❌ Не удалось загрузить данные.")
                
        except Exception as e:
            logger.error(f"Ошибка при обновлении: {e}")
            await update.message.reply_text(f"❌ Ошибка при обновлении: {str(e)}")
    
    def run(self) -> None:
        """Запуск бота"""
        application = Application.builder().token(self.token).build()
        
        # Регистрируем обработчики команд
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CommandHandler("forecast", self.forecast))
        application.add_handler(CommandHandler("update", self.update))
        
        # Запускаем бота
        logger.info("Бот запущен")
        application.run_polling(allowed_updates=Update.ALL_TYPES)


def main():
    """Главная функция"""
    try:
        bot = CurrencyBot()
        bot.run()
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        raise


if __name__ == '__main__':
    main()

