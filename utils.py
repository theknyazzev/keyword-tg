"""
Утилиты для работы с приложением
"""

import logging
import sys
from pathlib import Path


def setup_logging(level=logging.INFO):
    """Настройка логирования"""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('stalker_bot.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )


def ensure_directories():
    """Создание необходимых директорий"""
    dirs = ['data', 'logs']
    for dir_name in dirs:
        Path(dir_name).mkdir(exist_ok=True)


def format_message_for_display(message_data):
    """Форматирует данные сообщения для отображения"""
    channel_name = message_data.get('channel_name', 'Неизвестный канал')
    keywords = ', '.join(message_data.get('found_keywords', []))
    text = message_data.get('text', '')
    date = message_data.get('date', 'Неизвестно')
    
    # Обрезаем длинный текст
    if len(text) > 200:
        text = text[:200] + '...'
    
    return {
        'channel': channel_name,
        'keywords': keywords,
        'text': text,
        'date': date,
        'formatted': f"📺 {channel_name}\n🔑 {keywords}\n💬 {text}\n📅 {date}"
    }


def validate_config():
    """Проверка конфигурации"""
    from config import API_ID, API_HASH, BOT_TOKEN, ADMIN_ID
    
    errors = []
    
    if not API_ID or API_ID == 0:
        errors.append("API_ID не настроен")
    
    if not API_HASH:
        errors.append("API_HASH не настроен")
    
    if not BOT_TOKEN:
        errors.append("BOT_TOKEN не настроен")
    
    if not ADMIN_ID or ADMIN_ID == 0:
        errors.append("ADMIN_ID не настроен")
    
    return errors


def get_app_info():
    """Получение информации о приложении"""
    from config import MONITORED_CHANNELS, KEYWORDS
    from database import JsonDatabase
    
    db = JsonDatabase()
    settings = db.load_settings()
    messages_count = len(db.load_found_messages())
    
    return {
        'channels_count': len(MONITORED_CHANNELS),
        'keywords_count': len(settings.get('keywords', KEYWORDS)),
        'messages_found': messages_count,
        'monitoring_enabled': settings.get('monitoring_enabled', True),
        'last_update': settings.get('last_update', 'Никогда')
    }
