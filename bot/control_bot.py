"""
Основной модуль управляющего бота
"""

import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from .handlers import router
from .globals import set_monitor_instance, get_monitor_instance


logger = logging.getLogger(__name__)


class ControlBot:
    """Класс управляющего бота на aiogram"""
    
    def __init__(self, monitor=None):
        self.bot = Bot(token=BOT_TOKEN)
        self.storage = MemoryStorage()
        self.dp = Dispatcher(storage=self.storage)
        self.monitor = monitor
        
        # Устанавливаем глобальный экземпляр монитора
        set_monitor_instance(monitor)
        
        # Регистрируем роутер
        self.dp.include_router(router)
    
    async def start(self):
        """Запуск бота"""
        logger.info("Запуск управляющего бота...")
        
        # Устанавливаем callback для монитора
        if self.monitor:
            self.monitor.set_message_callback(self._handle_found_message)
        
        await self.dp.start_polling(self.bot)
    
    async def stop(self):
        """Остановка бота"""
        logger.info("Остановка управляющего бота...")
        await self.bot.session.close()
    
    async def _handle_found_message(self, message_data):
        """Обработка найденного сообщения"""
        try:
            from config import get_admin_list
            from datetime import datetime
            
            # Формируем сообщение для админов
            channel_name = message_data.get('channel_name', 'Неизвестный канал')
            keywords = ', '.join(message_data.get('found_keywords', []))
            message_text = message_data.get('text', '')
            
            # Получаем информацию о пользователе
            sender_full_name = message_data.get('sender_full_name', 'Неизвестный')
            sender_username = message_data.get('sender_username', '')
            
            # Формируем строку с информацией об отправителе
            sender_info = sender_full_name
            if sender_username and sender_username != sender_full_name:
                sender_info = f"{sender_full_name} ({sender_username})"
            
            # Получаем московское время
            moscow_time_str = "Неизвестно"
            if message_data.get('moscow_time'):
                try:
                    moscow_dt = datetime.fromisoformat(message_data['moscow_time'])
                    moscow_time_str = moscow_dt.strftime("%d.%m.%Y %H:%M:%S MSK")
                except:
                    moscow_time_str = message_data.get('moscow_time', 'Неизвестно')
            
            # Обрезаем длинное сообщение
            if len(message_text) > 500:
                message_text = message_text[:500] + '...'
            
            notification_text = (
                f"🎯 <b>Найдено новое сообщение!</b>\n\n"
                f"📺 <b>Канал:</b> {channel_name}\n"
                f"� <b>Пользователь:</b> {sender_info}\n"
                f"�🔑 <b>Ключевые слова:</b> <i>{keywords}</i>\n"
                f"📅 <b>Время:</b> {moscow_time_str}\n\n"
                f"💬 <b>Текст сообщения:</b>\n{message_text}"
            )
            
            # Отправляем уведомление всем админам
            admin_list = get_admin_list()
            for admin_id in admin_list:
                try:
                    await self.bot.send_message(
                        chat_id=admin_id,
                        text=notification_text,
                        parse_mode="HTML"
                    )
                except Exception as e:
                    logger.warning(f"Не удалось отправить уведомление админу {admin_id}: {e}")
            
            logger.info(f"Уведомления отправлены {len(admin_list)} админам о новом сообщении из {channel_name}")
            
        except Exception as e:
            logger.error(f"Ошибка при отправке уведомления: {e}")
    
    async def send_notification(self, text: str, chat_id: int = None):
        """Отправка уведомления"""
        if chat_id is None:
            from config import get_admin_list
            admin_list = get_admin_list()
            for admin_id in admin_list:
                try:
                    await self.bot.send_message(chat_id=admin_id, text=text, parse_mode="HTML")
                except Exception as e:
                    logger.warning(f"Не удалось отправить уведомление админу {admin_id}: {e}")
        else:
            try:
                await self.bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML")
            except Exception as e:
                logger.error(f"Ошибка при отправке уведомления: {e}")
    
    async def send_notification_with_data(self, title: str, content: str, data: dict = None):
        """
        Отправка уведомления с дополнительными данными (для Gmail и других источников)
        
        Args:
            title: Заголовок уведомления
            content: Содержимое уведомления
            data: Дополнительные данные (опционально)
        """
        try:
            notification_text = f"{title}\n\n{content}"
            
            # Отправляем уведомление всем админам
            from config import get_admin_list
            admin_list = get_admin_list()
            for admin_id in admin_list:
                try:
                    await self.bot.send_message(
                        chat_id=admin_id,
                        text=notification_text,
                        parse_mode="HTML"
                    )
                except Exception as e:
                    logger.warning(f"Не удалось отправить уведомление админу {admin_id}: {e}")
            
            logger.info(f"Уведомления отправлены {len(admin_list)} админам: {title}")
            
        except Exception as e:
            logger.error(f"Ошибка при отправке уведомления с данными: {e}")
