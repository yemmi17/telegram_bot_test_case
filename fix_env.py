#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Скрипт для создания/исправления файла .env"""
import os
import sys

def main():
    print("=" * 60)
    print("Исправление файла .env")
    print("=" * 60)
    
    # Проверяем текущий файл
    env_path = '.env'
    if os.path.exists(env_path):
        size = os.path.getsize(env_path)
        print(f"\nТекущий файл .env существует, размер: {size} байт")
        if size > 0:
            with open(env_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                print(f"Текущее содержимое:\n{repr(content[:100])}")
    
    print("\n" + "=" * 60)
    print("Введите токен Telegram-бота")
    print("=" * 60)
    print("\nЕсли у вас нет токена:")
    print("1. Откройте Telegram")
    print("2. Найдите @BotFather")
    print("3. Отправьте /newbot")
    print("4. Следуйте инструкциям")
    print("5. Скопируйте полученный токен\n")
    
    token = input("TELEGRAM_BOT_TOKEN: ").strip()
    
    if not token:
        print("\nОШИБКА: Токен не может быть пустым!")
        return 1
    
    # Проверяем формат токена (обычно это длинная строка)
    if len(token) < 20:
        print(f"\nПРЕДУПРЕЖДЕНИЕ: Токен кажется слишком коротким ({len(token)} символов)")
        print("Обычно токен от BotFather длиннее. Продолжить? (y/n): ", end='')
        if input().strip().lower() != 'y':
            return 1
    
    # Создаем содержимое файла
    content = f"TELEGRAM_BOT_TOKEN={token}\n"
    
    # Записываем файл
    try:
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Проверяем, что записалось
        if os.path.exists(env_path):
            size = os.path.getsize(env_path)
            print(f"\n{'='*60}")
            print("ФАЙЛ УСПЕШНО СОЗДАН!")
            print(f"{'='*60}")
            print(f"\nПуть: {os.path.abspath(env_path)}")
            print(f"Размер: {size} байт")
            print(f"\nСодержимое:")
            print(content)
            
            # Проверяем загрузку
            from dotenv import load_dotenv
            load_dotenv(override=True)
            loaded_token = os.getenv('TELEGRAM_BOT_TOKEN')
            if loaded_token == token:
                print("\nПРОВЕРКА: Токен успешно загружен из файла!")
                print(f"Длина загруженного токена: {len(loaded_token)} символов")
            else:
                print("\nПРЕДУПРЕЖДЕНИЕ: Токен не загрузился правильно")
                print(f"Ожидалось: {len(token)} символов")
                print(f"Загружено: {len(loaded_token) if loaded_token else 0} символов")
            
            print(f"\n{'='*60}")
            print("Теперь можно запустить бота: python bot.py")
            print(f"{'='*60}")
            return 0
        else:
            print("\nОШИБКА: Файл не был создан!")
            return 1
            
    except Exception as e:
        print(f"\nОШИБКА при записи файла: {e}")
        return 1

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nОтменено пользователем.")
        sys.exit(1)
    except Exception as e:
        print(f"\nКРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

