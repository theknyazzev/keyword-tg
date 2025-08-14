"""
Модуль мониторинга каналов через Telethon
"""

import asyncio
import logging
import re
from typing import List, Set
from datetime import datetime, timezone, timedelta
from telethon import TelegramClient, events
from telethon.tl.types import Channel, Chat
from telethon.errors import FloodWaitError, ChannelPrivateError

from config import API_ID, API_HASH, PHONE, SESSION_NAME, KEYWORDS, get_monitored_channels
from database import JsonDatabase


logger = logging.getLogger(__name__)


class ChannelMonitor:
    """Класс для мониторинга каналов Telegram"""
    
    def __init__(self):
        self.client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
        self.db = JsonDatabase()
        self.is_monitoring = False
        self._load_channels_and_keywords()
        self.message_callback = None
    
    def _load_channels_and_keywords(self):
        """Загружает актуальный список каналов и ключевых слов"""
        # Получаем каналы из базы данных
        self.monitored_channels: Set[int] = set(get_monitored_channels().keys())
        
        # Получаем ключевые слова из настроек
        settings = self.db.load_settings()
        self.keywords: List[str] = settings.get('keywords', KEYWORDS.copy())
        
        logger.info(f"Загружено каналов: {len(self.monitored_channels)}")
        logger.info(f"Загружено ключевых слов: {len(self.keywords)}")
    
    async def reload_config(self):
        """Перезагружает конфигурацию каналов и ключевых слов"""
        self._load_channels_and_keywords()
        logger.info("Конфигурация каналов и ключевых слов обновлена")
    
    async def start(self):
        """Запуск клиента"""
        await self.client.start(phone=PHONE)
        logger.info("Telethon клиент запущен")
        
        # Проверяем доступность каналов
        await self._check_channels_access()
        
        # Регистрируем обработчик новых сообщений
        self.client.add_event_handler(self._handle_new_message, events.NewMessage)
        
        self.is_monitoring = True
        logger.info("Мониторинг каналов запущен")
    
    async def stop(self):
        """Остановка мониторинга"""
        self.is_monitoring = False
        await self.client.disconnect()
        logger.info("Мониторинг остановлен")
    
    async def _check_channels_access(self):
        """Проверяет доступность каналов"""
        accessible_channels = set()
        
        for channel_id in self.monitored_channels:
            try:
                entity = await self.client.get_entity(int(f"-100{channel_id}"))
                if isinstance(entity, (Channel, Chat)):
                    accessible_channels.add(channel_id)
                    channels_dict = get_monitored_channels()
                    channel_name = channels_dict.get(channel_id, f"Channel {channel_id}")
                    logger.info(f"Канал {channel_name} доступен")
                else:
                    logger.warning(f"Канал {channel_id} не является каналом или чатом")
            except ChannelPrivateError:
                logger.error(f"Канал {channel_id} приватный или недоступен")
            except Exception as e:
                logger.error(f"Ошибка при проверке канала {channel_id}: {e}")
        
        self.monitored_channels = accessible_channels
        logger.info(f"Доступно каналов для мониторинга: {len(accessible_channels)}")
    
    async def _handle_new_message(self, event):
        """Обработчик новых сообщений"""
        if not self.is_monitoring:
            return
        
        try:
            # Получаем ID канала
            if hasattr(event.chat, 'id'):
                channel_id = abs(event.chat.id)
                if str(channel_id).startswith('100'):
                    channel_id = int(str(channel_id)[3:])
            else:
                return
            
            # Проверяем, что это наш отслеживаемый канал
            if channel_id not in self.monitored_channels:
                return
            
            message_text = event.message.message
            if not message_text:
                return
            
            # Проверяем наличие ключевых слов (поиск целых слов)
            message_lower = message_text.lower()
            found_keywords = []
            
            for kw in self.keywords:
                kw_lower = kw.lower()
                # Ищем ключевое слово как отдельное слово
                # Используем более надежный способ для кириллицы
                words = re.findall(r'\b\w+\b', message_lower, re.UNICODE)
                if kw_lower in words:
                    found_keywords.append(kw)
            
            if not found_keywords:
                return
            
            # Формируем данные сообщения
            channels_dict = get_monitored_channels()
            channel_name = channels_dict.get(channel_id, f"Channel {channel_id}")
            
            # Получаем информацию о пользователе
            sender_info = await self._get_sender_info(event.message)
            
            # Конвертируем время в московское (+2 UTC)
            moscow_time = None
            if event.message.date:
                moscow_tz = timezone(timedelta(hours=2))  # MSK = UTC+2
                moscow_time = event.message.date.replace(tzinfo=timezone.utc).astimezone(moscow_tz)
            
            message_data = {
                'message_id': event.message.id,
                'channel_id': channel_id,
                'channel_name': channel_name,
                'text': message_text,
                'found_keywords': found_keywords,
                'date': event.message.date.isoformat() if event.message.date else None,
                'moscow_time': moscow_time.isoformat() if moscow_time else None,
                'sender_id': event.message.sender_id,
                'sender_username': sender_info.get('username'),
                'sender_first_name': sender_info.get('first_name'),
                'sender_last_name': sender_info.get('last_name'),
                'sender_full_name': sender_info.get('full_name'),
                'is_forwarded': bool(event.message.forward)
            }
            
            # Сохраняем в базу данных
            if self.db.add_found_message(message_data):
                logger.info(f"Найдено сообщение с ключевыми словами {found_keywords} в канале {message_data['channel_name']}")
                
                # Вызываем callback если он установлен
                if self.message_callback:
                    await self.message_callback(message_data)
        
        except FloodWaitError as e:
            logger.warning(f"Flood control, ждем {e.seconds} секунд")
            await asyncio.sleep(e.seconds)
        except Exception as e:
            logger.error(f"Ошибка при обработке сообщения: {e}")
    
    async def _get_sender_info(self, message):
        """Получает информацию об отправителе сообщения"""
        sender_info = {
            'username': None,
            'first_name': None,
            'last_name': None,
            'full_name': None
        }
        
        try:
            if message.sender_id:
                sender = await self.client.get_entity(message.sender_id)
                
                # Получаем username (если есть)
                if hasattr(sender, 'username') and sender.username:
                    sender_info['username'] = f"@{sender.username}"
                
                # Получаем имя и фамилию
                if hasattr(sender, 'first_name') and sender.first_name:
                    sender_info['first_name'] = sender.first_name
                
                if hasattr(sender, 'last_name') and sender.last_name:
                    sender_info['last_name'] = sender.last_name
                
                # Формируем полное имя
                name_parts = []
                if sender_info['first_name']:
                    name_parts.append(sender_info['first_name'])
                if sender_info['last_name']:
                    name_parts.append(sender_info['last_name'])
                
                if name_parts:
                    sender_info['full_name'] = ' '.join(name_parts)
                elif sender_info['username']:
                    sender_info['full_name'] = sender_info['username']
                else:
                    sender_info['full_name'] = f"ID: {message.sender_id}"
                    
        except Exception as e:
            logger.warning(f"Не удалось получить информацию об отправителе: {e}")
            sender_info['full_name'] = f"ID: {message.sender_id}" if message.sender_id else "Неизвестный"
        
        return sender_info
    
    def set_message_callback(self, callback):
        """Устанавливает callback для обработки найденных сообщений"""
        self.message_callback = callback
    
    def update_keywords(self, keywords: List[str]):
        """Обновляет список ключевых слов"""
        self.keywords = keywords
        logger.info(f"Обновлены ключевые слова: {keywords}")
    
    def get_monitored_channels_count(self) -> int:
        """Возвращает количество отслеживаемых каналов"""
        return len(self.monitored_channels)
    
    def get_keywords_count(self) -> int:
        """Возвращает количество ключевых слов"""
        return len(self.keywords)
    
    async def get_channel_info(self, channel_id: int):
        """Получает информацию о канале"""
        try:
            entity = await self.client.get_entity(int(f"-100{channel_id}"))
            return {
                'id': channel_id,
                'title': getattr(entity, 'title', 'Unknown'),
                'username': getattr(entity, 'username', None),
                'participants_count': getattr(entity, 'participants_count', 0)
            }
        except Exception as e:
            logger.error(f"Ошибка при получении информации о канале {channel_id}: {e}")
            return None
    
    async def get_recent_messages_from_channel(self, channel_id: int, limit: int = 10):
        """Получает последние сообщения из канала"""
        try:
            entity = await self.client.get_entity(int(f"-100{channel_id}"))
            messages = []
            
            async for message in self.client.iter_messages(entity, limit=limit):
                if message.message:
                    messages.append({
                        'id': message.id,
                        'text': message.message,
                        'date': message.date.isoformat() if message.date else None,
                        'sender_id': message.sender_id
                    })
            
            return messages
        except Exception as e:
            logger.error(f"Ошибка при получении сообщений из канала {channel_id}: {e}")
            return []
