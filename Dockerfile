FROM python:3.11-slim

WORKDIR /app

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY . .

# Создаем директорию для данных
RUN mkdir -p /app/data

# Переменные окружения (можно переопределить через docker-compose или -e)
ENV PYTHONUNBUFFERED=1

# Запуск бота
CMD ["python", "bot.py"]

