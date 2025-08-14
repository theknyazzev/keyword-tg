"""
Модуль для работы с JSON базой данных
"""

import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from config import DATA_DIR, FOUND_MESSAGES_FILE, SETTINGS_FILE


class JsonDatabase:
    """Класс для работы с JSON базой данных"""
    
    def __init__(self):
        self._ensure_data_dir()
        self._init_files()
    
    def _ensure_data_dir(self):
        """Создает директорию для данных если её нет"""
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)
    
    def _init_files(self):
        """Инициализирует файлы базы данных"""
        if not os.path.exists(FOUND_MESSAGES_FILE):
            self.save_found_messages([])
        
        if not os.path.exists(SETTINGS_FILE):
            self.save_settings({
                "monitoring_enabled": True,
                "keywords": ["ищу", "wordpress"],
                "last_update": datetime.now().isoformat()
            })
    
    def load_found_messages(self) -> List[Dict[str, Any]]:
        """Загружает найденные сообщения"""
        try:
            with open(FOUND_MESSAGES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def save_found_messages(self, messages: List[Dict[str, Any]]):
        """Сохраняет найденные сообщения"""
        with open(FOUND_MESSAGES_FILE, 'w', encoding='utf-8') as f:
            json.dump(messages, f, ensure_ascii=False, indent=2)
    
    def add_found_message(self, message_data: Dict[str, Any]):
        """Добавляет новое найденное сообщение"""
        messages = self.load_found_messages()
        
        # Проверяем, нет ли уже такого сообщения
        message_id = message_data.get('message_id')
        channel_id = message_data.get('channel_id')
        
        for msg in messages:
            if msg.get('message_id') == message_id and msg.get('channel_id') == channel_id:
                return False  # Сообщение уже существует
        
        message_data['timestamp'] = datetime.now().isoformat()
        messages.append(message_data)
        
        # Ограничиваем количество сохраненных сообщений (последние 1000)
        if len(messages) > 1000:
            messages = messages[-1000:]
        
        self.save_found_messages(messages)
        return True
    
    def load_settings(self) -> Dict[str, Any]:
        """Загружает настройки"""
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {
                "monitoring_enabled": True,
                "keywords": ["ищу", "wordpress"],
                "last_update": datetime.now().isoformat()
            }
    
    def save_settings(self, settings: Dict[str, Any]):
        """Сохраняет настройки"""
        settings['last_update'] = datetime.now().isoformat()
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
    
    def get_recent_messages(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Получает последние найденные сообщения"""
        messages = self.load_found_messages()
        return messages[-limit:] if messages else []
    
    def clear_messages(self):
        """Очищает все найденные сообщения"""
        self.save_found_messages([])
    
    def get_messages_by_channel(self, channel_id: int) -> List[Dict[str, Any]]:
        """Получает сообщения по ID канала"""
        messages = self.load_found_messages()
        return [msg for msg in messages if msg.get('channel_id') == channel_id]
    
    def get_channels(self) -> Dict[int, str]:
        """Получает список каналов из настроек"""
        settings = self.load_settings()
        return settings.get('channels', {})
    
    def add_channel(self, channel_id: int, channel_name: str) -> bool:
        """Добавляет новый канал"""
        settings = self.load_settings()
        channels = settings.get('channels', {})
        
        # Преобразуем ID в строку для JSON совместимости
        str_channel_id = str(channel_id)
        
        if str_channel_id in channels:
            return False  # Канал уже существует
        
        channels[str_channel_id] = channel_name
        settings['channels'] = channels
        self.save_settings(settings)
        return True
    
    def remove_channel(self, channel_id: int) -> bool:
        """Удаляет канал"""
        settings = self.load_settings()
        channels = settings.get('channels', {})
        str_channel_id = str(channel_id)
        
        if str_channel_id not in channels:
            return False  # Канал не найден
        
        del channels[str_channel_id]
        settings['channels'] = channels
        self.save_settings(settings)
        return True
    
    def update_channel(self, channel_id: int, new_name: str) -> bool:
        """Обновляет название канала"""
        settings = self.load_settings()
        channels = settings.get('channels', {})
        str_channel_id = str(channel_id)
        
        if str_channel_id not in channels:
            return False  # Канал не найден
        
        channels[str_channel_id] = new_name
        settings['channels'] = channels
        self.save_settings(settings)
        return True
    
    def get_admin_ids(self) -> List[int]:
        """Получает список ID админов"""
        settings = self.load_settings()
        return settings.get('admin_ids', [])
    
    def add_admin(self, user_id: int) -> bool:
        """Добавляет админа"""
        settings = self.load_settings()
        admin_ids = settings.get('admin_ids', [])
        
        if user_id in admin_ids:
            return False  # Админ уже существует
        
        admin_ids.append(user_id)
        settings['admin_ids'] = admin_ids
        self.save_settings(settings)
        return True
    
    def remove_admin(self, user_id: int) -> bool:
        """Удаляет админа"""
        from config import SUPER_ADMIN_ID
        
        if user_id == SUPER_ADMIN_ID:
            return False  # Нельзя удалить суперадмина
        
        settings = self.load_settings()
        admin_ids = settings.get('admin_ids', [])
        
        if user_id not in admin_ids:
            return False  # Админ не найден
        
        admin_ids.remove(user_id)
        settings['admin_ids'] = admin_ids
        self.save_settings(settings)
        return True
    
    def get_admin_count(self) -> int:
        """Возвращает количество админов"""
        return len(self.get_admin_ids())
    
    def get_bot_mode(self) -> str:
        """Получает текущий режим работы бота (channels/email/none)"""
        settings = self.load_settings()
        return settings.get('bot_mode', 'none')
    
    def set_bot_mode(self, mode: str) -> bool:
        """Устанавливает режим работы бота"""
        if mode not in ['channels', 'email', 'none']:
            return False
        
        settings = self.load_settings()
        settings['bot_mode'] = mode
        self.save_settings(settings)
        return True
    
    def get_email_settings(self) -> Dict[str, Any]:
        """Получает настройки email"""
        settings = self.load_settings()
        return settings.get('email_settings', {
            'check_interval': 60,  # секунды
            'max_emails_per_check': 20,
            'auto_mark_read': False
        })
    
    def save_email_settings(self, email_settings: Dict[str, Any]):
        """Сохраняет настройки email"""
        settings = self.load_settings()
        settings['email_settings'] = email_settings
        self.save_settings(settings)
