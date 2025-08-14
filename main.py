"""
Главный файл запуска Stalker Bot
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path

# Добавляем текущую директорию в путь для импортов
sys.path.insert(0, str(Path(__file__).parent))

from config import API_ID, API_HASH, BOT_TOKEN, ADMIN_ID
from monitor import ChannelMonitor
from bot import ControlBot
from utils import setup_logging, ensure_directories, validate_config, get_app_info


logger = logging.getLogger(__name__)


class StalkerApp:
    """Основное приложение Stalker Bot"""
    
    def __init__(self):
        self.monitor = None
        self.control_bot = None
        self.running = False
    
    async def start(self):
        """Запуск приложения"""
        try:
            # Настройка логирования и директорий
            setup_logging()
            ensure_directories()
            
            logger.info("🚀 Запуск Stalker Bot...")
            
            # Проверка конфигурации
            config_errors = validate_config()
            if config_errors:
                logger.error("Ошибки конфигурации:")
                for error in config_errors:
                    logger.error(f"  - {error}")
                logger.error("Создайте файл .env на основе .env.example и заполните настройки")
                return
            
            # Вывод информации о приложении
            app_info = get_app_info()
            logger.info(f"📊 Каналов для мониторинга: {app_info['channels_count']}")
            logger.info(f"🔑 Ключевых слов: {app_info['keywords_count']}")
            logger.info(f"📨 Найдено сообщений: {app_info['messages_found']}")
            
            # Инициализация компонентов
            self.monitor = ChannelMonitor()
            self.control_bot = ControlBot(self.monitor)
            
            # Запуск монитора каналов
            logger.info("🔍 Запуск мониторинга каналов...")
            await self.monitor.start()
            
            # Отправка уведомления о запуске
            await self.control_bot.send_notification(
                "🟢 <b>Stalker Bot запущен!</b>\n\n"
                f"📺 Мониторится каналов: {app_info['channels_count']}\n"
                f"🔑 Ключевых слов: {app_info['keywords_count']}\n"
                f"📨 Найдено сообщений: {app_info['messages_found']}\n\n"
                "Бот готов к работе! 🎯"
            )
            
            self.running = True
            logger.info("✅ Stalker Bot успешно запущен!")
            
            # Запуск управляющего бота (блокирующий)
            await self.control_bot.start()
            
        except KeyboardInterrupt:
            logger.info("Получен сигнал завершения...")
            await self.stop()
        except Exception as e:
            logger.error(f"Критическая ошибка при запуске: {e}", exc_info=True)
            await self.stop()
    
    async def stop(self):
        """Остановка приложения"""
        if not self.running:
            return
        
        logger.info("🛑 Остановка Stalker Bot...")
        self.running = False
        
        try:
            # Отправка уведомления об остановке
            if self.control_bot:
                await self.control_bot.send_notification(
                    "🔴 <b>Stalker Bot остановлен</b>\n\n"
                    "Мониторинг приостановлен."
                )
            
            # Остановка компонентов
            if self.monitor:
                await self.monitor.stop()
                logger.info("✅ Монитор каналов остановлен")
            
            if self.control_bot:
                await self.control_bot.stop()
                logger.info("✅ Управляющий бот остановлен")
            
            logger.info("👋 Stalker Bot полностью остановлен")
            
        except Exception as e:
            logger.error(f"Ошибка при остановке: {e}")
    
    def setup_signal_handlers(self):
        """Настройка обработчиков сигналов"""
        def signal_handler(signum, frame):
            logger.info(f"Получен сигнал {signum}")
            asyncio.create_task(self.stop())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)


async def main():
    """Главная функция"""
    app = StalkerApp()
    app.setup_signal_handlers()
    await app.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 До свидания!")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        sys.exit(1)
