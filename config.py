"""
Конфигурация приложения
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Telegram API настройки
API_ID = int(os.getenv('API_ID', '0'))
API_HASH = os.getenv('API_HASH', '')
PHONE = os.getenv('PHONE', '')
SESSION_NAME = os.getenv('SESSION_NAME', 'stalker_session')

# Управляющий бот
BOT_TOKEN = os.getenv('BOT_TOKEN', '')

# Система админов
SUPER_ADMIN_ID = 5375230735  # Максимальный создатель
ADMIN_IDS_STR = os.getenv('ADMIN_ID', '5375230735')
ADMIN_ID = SUPER_ADMIN_ID  # Для обратной совместимости

def get_admin_list():
    """Получает список всех админов из настроек"""
    try:
        from database.json_db import JsonDatabase
        db = JsonDatabase()
        settings = db.load_settings()
        
        # Получаем список админов из базы
        admin_list = settings.get('admin_ids', [])
        
        # Если список пуст, инициализируем из .env
        if not admin_list:
            admin_ids = [int(id.strip()) for id in ADMIN_IDS_STR.split(',') if id.strip().isdigit()]
            admin_list = admin_ids
            settings['admin_ids'] = admin_list
            db.save_settings(settings)
        
        # Убеждаемся, что суперадмин всегда в списке
        if SUPER_ADMIN_ID not in admin_list:
            admin_list.append(SUPER_ADMIN_ID)
            settings['admin_ids'] = admin_list
            db.save_settings(settings)
        
        return admin_list
    except ImportError:
        # Если база данных недоступна, используем .env
        return [int(id.strip()) for id in ADMIN_IDS_STR.split(',') if id.strip().isdigit()]

def is_admin(user_id: int) -> bool:
    """Проверяет, является ли пользователь админом"""
    return user_id in get_admin_list()

def is_super_admin(user_id: int) -> bool:
    """Проверяет, является ли пользователь суперадмином"""
    return user_id == SUPER_ADMIN_ID

# Каналы для мониторинга (по умолчанию, можно добавлять через бота)
DEFAULT_MONITORED_CHANNELS = {
    1495211598: "Работаем, ребята!",
    1271179843: "Salebot - ЧАТ взаимопомощи",
    1634118830: "ЗАКАЗЫ ДЛЯ ФРИЛАНСЕРОВ",
    1463866217: "Мари про отзывы — инфобизнес",
    1162626517: "Чат GetHelpers.ru для специалистов по GetCourse",
    1751373900: "МИР КРЕАТОРОВ"
}

def get_monitored_channels():
    """Получает список каналов для мониторинга из базы данных"""
    try:
        from database.json_db import JsonDatabase
        db = JsonDatabase()
        
        # Инициализируем каналы в базе, если их там нет
        channels_from_db = db.get_channels()
        if not channels_from_db:
            settings = db.load_settings()
            settings['channels'] = {str(k): v for k, v in DEFAULT_MONITORED_CHANNELS.items()}
            db.save_settings(settings)
            channels_from_db = db.get_channels()
        
        # Преобразуем строковые ID обратно в int
        return {int(k): v for k, v in channels_from_db.items()}
    except ImportError:
        # Если база данных недоступна, используем каналы по умолчанию
        return DEFAULT_MONITORED_CHANNELS

# Получаем актуальный список каналов
MONITORED_CHANNELS = get_monitored_channels()

# Ключевые слова для поиска
KEYWORDS = ["ищу", "wordpress"]

# Пути к файлам
DATA_DIR = "data"
FOUND_MESSAGES_FILE = os.path.join(DATA_DIR, "found_messages.json")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")
