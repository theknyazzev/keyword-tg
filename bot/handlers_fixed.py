"""
Обработчики команд для управляющего бота - ИСПРАВЛЕННАЯ ВЕРСИЯ
"""
import logging
import inspect
from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramBadRequest

from config import get_admin_list, is_admin, is_super_admin, SUPER_ADMIN_ID, get_monitored_channels
from database import JsonDatabase
from .globals import get_monitor_instance

logger = logging.getLogger(__name__)
router = Router()

# Получаем актуальный список каналов для отображения
MONITORED_CHANNELS = get_monitored_channels()

class AdminStates(StatesGroup):
    waiting_for_keywords = State()
    waiting_for_channel_id = State()
    waiting_for_channel_name = State()
    waiting_for_remove_channel_id = State()
    waiting_for_new_admin_id = State()
    waiting_for_remove_admin_id = State()
    waiting_for_email_data = State()
    waiting_for_email_recipient = State()
    waiting_for_email_subject = State()
    waiting_for_email_body = State()

def admin_only(func):
    """Декоратор для проверки прав администратора"""
    async def wrapper(message: Message, *args, **kwargs):
        if not is_admin(message.from_user.id):
            await message.answer("⛔ У вас нет прав для выполнения этой команды")
            return
        
        sig = inspect.signature(func)
        filtered_kwargs = {}
        for param_name in sig.parameters:
            if param_name in kwargs:
                filtered_kwargs[param_name] = kwargs[param_name]
        
        return await func(message, *args, **filtered_kwargs)
    return wrapper

def super_admin_only(func):
    """Декоратор для проверки прав суперадминистратора"""
    async def wrapper(message: Message, *args, **kwargs):
        if not is_super_admin(message.from_user.id):
            await message.answer("⛔ Эта команда доступна только создателю бота")
            return
        
        sig = inspect.signature(func)
        filtered_kwargs = {}
        for param_name in sig.parameters:
            if param_name in kwargs:
                filtered_kwargs[param_name] = kwargs[param_name]
        
        return await func(message, *args, **filtered_kwargs)
    return wrapper

def format_moscow_time(time_data):
    """Форматирует время в московском часовом поясе"""
    if not time_data:
        return "Неизвестно"
    
    if isinstance(time_data, dict):
        moscow_time_str = time_data.get('moscow_time')
        if moscow_time_str:
            try:
                moscow_dt = datetime.fromisoformat(moscow_time_str)
                return moscow_dt.strftime("%d.%m.%Y %H:%M:%S MSK")
            except:
                pass
        
        timestamp = time_data.get('timestamp')
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp)
                moscow_dt = dt.replace(tzinfo=None) + timedelta(hours=2)
                return moscow_dt.strftime("%d.%m.%Y %H:%M:%S MSK")
            except:
                pass
    
    if isinstance(time_data, str):
        try:
            dt = datetime.fromisoformat(time_data)
            moscow_dt = dt.replace(tzinfo=None) + timedelta(hours=2)
            return moscow_dt.strftime("%d.%m.%Y %H:%M:%S MSK")
        except:
            return time_data
    
    return "Неизвестно"

def format_sender_info(msg_data):
    """Форматирует информацию об отправителе"""
    sender_full_name = msg_data.get('sender_full_name', 'Неизвестный')
    sender_username = msg_data.get('sender_username', '')
    
    if sender_username and sender_username != sender_full_name:
        return f"{sender_full_name} ({sender_username})"
    return sender_full_name

def get_main_menu(user_id: int = None):
    """Создает простое главное меню из 3 кнопок"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📺 Каналы"),
                KeyboardButton(text="📧 Почта"),
                KeyboardButton(text="⚙️ Настройки")
            ],
            [
                KeyboardButton(text="ℹ️ Помощь")
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Выберите раздел..."
    )
    return keyboard

def get_channels_menu(user_id: int = None):
    """Создает меню раздела каналов"""
    keyboard_rows = []
    
    keyboard_rows.append([
        KeyboardButton(text="📊 Статус каналов"),
        KeyboardButton(text="🔍 Поиск в сообщениях")
    ])
    
    keyboard_rows.append([
        KeyboardButton(text="📝 Ключевые слова"),
        KeyboardButton(text="📨 Найденные сообщения")
    ])
    
    keyboard_rows.append([
        KeyboardButton(text="📈 Статистика каналов"),
        KeyboardButton(text="📺 Управление каналами")
    ])
    
    if user_id and is_admin(user_id):
        keyboard_rows.append([
            KeyboardButton(text="➕ Добавить канал"),
            KeyboardButton(text="➖ Удалить канал")
        ])
    
    keyboard_rows.append([
        KeyboardButton(text="🏠 Главное меню")
    ])
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=keyboard_rows,
        resize_keyboard=True,
        one_time_keyboard=False
    )
    return keyboard

def get_email_menu(user_id: int = None):
    """Создает меню раздела почты"""
    keyboard_rows = []
    
    keyboard_rows.append([
        KeyboardButton(text="📊 Статус почты"),
        KeyboardButton(text="🔍 Поиск в письмах")
    ])
    
    keyboard_rows.append([
        KeyboardButton(text="📬 Входящие письма"),
        KeyboardButton(text="📩 Непрочитанные")
    ])
    
    keyboard_rows.append([
        KeyboardButton(text="✉️ Отправить письмо"),
        KeyboardButton(text="📈 Статистика почты")
    ])
    
    keyboard_rows.append([
        KeyboardButton(text="🏠 Главное меню")
    ])
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=keyboard_rows,
        resize_keyboard=True,
        one_time_keyboard=False
    )
    return keyboard

def get_settings_menu(user_id: int = None):
    """Создает меню настроек"""
    keyboard_rows = []
    
    keyboard_rows.append([
        KeyboardButton(text="📝 Ключевые слова"),
        KeyboardButton(text="📊 Статус системы")
    ])
    
    if user_id and is_admin(user_id):
        keyboard_rows.append([
            KeyboardButton(text="➕ Добавить канал"),
            KeyboardButton(text="🧹 Очистить сообщения")
        ])
    
    if user_id and is_super_admin(user_id):
        keyboard_rows.append([
            KeyboardButton(text="👥 Управление админами")
        ])
    
    keyboard_rows.append([
        KeyboardButton(text="🏠 Главное меню")
    ])
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=keyboard_rows,
        resize_keyboard=True,
        one_time_keyboard=False
    )
    return keyboard

def get_back_menu():
    """Создает меню с кнопкой возврата"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏠 Главное меню")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    return keyboard

async def safe_edit_message(callback: CallbackQuery, text: str, reply_markup=None, parse_mode="HTML"):
    """Безопасное редактирование сообщения"""
    try:
        if reply_markup is not None:
            await callback.message.edit_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
        else:
            await callback.message.edit_text(text, parse_mode=parse_mode)
        await callback.answer()
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            await callback.answer("✅ Данные актуальны!")
        else:
            logger.error(f"Ошибка при редактировании сообщения: {e}")
            await callback.answer("❌ Ошибка при обновлении")
    except Exception as e:
        logger.error(f"Неожиданная ошибка при редактировании сообщения: {e}")
        await callback.answer("❌ Произошла ошибка")

def get_monitor_from_context():
    """Получает монитор из глобального контекста"""
    return get_monitor_instance()

# ============ ОСНОВНЫЕ КОМАНДЫ ============

@router.message(Command("start"))
@admin_only
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    db = JsonDatabase()
    current_mode = db.get_bot_mode()
    
    inline_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔄 Обновить", callback_data="menu_refresh"),
            InlineKeyboardButton(text="📊 Статус", callback_data="menu_status")
        ]
    ])
    
    mode_icon = "📺" if current_mode == 'channels' else "📧"
    mode_name = "каналов" if current_mode == 'channels' else "почты"
    
    text = (
        "🎯 <b>Stalker Bot</b> - Система мониторинга\n\n"
        f"{mode_icon} <b>Текущий режим:</b> {mode_name}\n\n"
        "🚀 <b>Возможности бота:</b>\n"
        "• 🔍 Мониторинг в реальном времени\n"
        "• 🎯 Поиск по ключевым словам\n"
        "• 💾 Сохранение результатов\n"
        "• 🔔 Мгновенные уведомления\n"
        "• 📊 Детальная статистика\n\n"
        "👇 <b>Выберите действие в меню:</b>"
    )
    
    await message.answer(
        text, 
        reply_markup=get_main_menu(message.from_user.id), 
        parse_mode="HTML"
    )
    await message.answer(
        "⚡ <i>Быстрые действия:</i>",
        reply_markup=inline_keyboard,
        parse_mode="HTML"
    )

# ============ ИСПРАВЛЕННЫЕ ОБРАБОТЧИКИ КНОПОК ============

@router.message(F.text == "📺 Каналы")
@admin_only
async def menu_channels_section_button(message: Message):
    """Обработчик кнопки раздела Каналы"""
    await message.answer(
        "📺 <b>Раздел управления каналами</b>\n\n"
        "🔍 Мониторинг Telegram каналов в реальном времени\n"
        "🎯 Поиск сообщений по ключевым словам\n\n"
        "👇 Выберите действие:",
        parse_mode="HTML",
        reply_markup=get_channels_menu(message.from_user.id)
    )

@router.message(F.text == "📧 Почта")
@admin_only
async def menu_email_section_button(message: Message):
    """Обработчик кнопки раздела Почта"""
    await message.answer(
        "📧 <b>Раздел управления почтой</b>\n\n"
        "📬 Мониторинг Gmail в реальном времени\n"
        "🔍 Поиск и обработка входящих писем\n\n"
        "👇 Выберите действие:",
        parse_mode="HTML",
        reply_markup=get_email_menu(message.from_user.id)
    )

@router.message(F.text == "⚙️ Настройки")
@admin_only
async def menu_settings_section_button(message: Message):
    """Обработчик кнопки раздела Настройки"""
    await message.answer(
        "⚙️ <b>Настройки системы</b>\n\n"
        "🎛️ Выберите раздел настроек:",
        parse_mode="HTML",
        reply_markup=get_settings_menu(message.from_user.id)
    )

@router.message(F.text == "ℹ️ Помощь")
@admin_only
async def menu_help_button(message: Message):
    """Обработчик кнопки Помощь"""
    await show_help(message)

@router.message(F.text == "🏠 Главное меню")
@admin_only
async def menu_home_button(message: Message):
    """Обработчик кнопки Главное меню"""
    await cmd_start(message)

# ============ ОБРАБОТЧИКИ КНОПОК КАНАЛОВ ============

@router.message(F.text == "📊 Статус каналов")
@admin_only
async def menu_channels_status_button(message: Message):
    """Обработчик кнопки Статус каналов"""
    await show_channels_status(message)

@router.message(F.text == "🔍 Поиск в сообщениях")
@admin_only
async def menu_search_messages_button(message: Message):
    """Обработчик кнопки Поиск в сообщениях"""
    await message.answer(
        "🔍 <b>Поиск в сообщениях каналов</b>\n\n"
        "Введите текст для поиска в найденных сообщениях:",
        parse_mode="HTML",
        reply_markup=get_back_menu()
    )

@router.message(F.text == "📝 Ключевые слова")
@admin_only
async def menu_keywords_button(message: Message):
    """Обработчик кнопки Ключевые слова"""
    await show_keywords(message)

@router.message(F.text == "📨 Найденные сообщения")
@admin_only
async def menu_found_messages_button(message: Message):
    """Обработчик кнопки Найденные сообщения"""
    await show_recent_messages(message, 10)

@router.message(F.text == "📈 Статистика каналов")
@admin_only
async def menu_channels_stats_button(message: Message):
    """Обработчик кнопки Статистика каналов"""
    await show_channels_stats(message)

@router.message(F.text == "📺 Управление каналами")
@admin_only
async def menu_channel_management_button(message: Message):
    """Обработчик управления каналами"""
    await show_channels(message)

# ============ ОБРАБОТЧИКИ КНОПОК ПОЧТЫ ============

@router.message(F.text == "📊 Статус почты")
@admin_only
async def menu_email_status_button(message: Message):
    """Обработчик кнопки Статус почты"""
    await show_email_status(message)

@router.message(F.text == "📬 Входящие письма")
@admin_only
async def menu_inbox_button(message: Message):
    """Обработчик кнопки Входящие письма"""
    await show_inbox_emails(message)

@router.message(F.text == "📩 Непрочитанные")
@admin_only
async def menu_unread_emails_button(message: Message):
    """Обработчик кнопки Непрочитанные письма"""
    await show_unread_emails(message)

@router.message(F.text == "✉️ Отправить письмо")
@admin_only
async def menu_send_email_button(message: Message, state: FSMContext):
    """Обработчик кнопки Отправить письмо"""
    await send_email_start(message, state)

@router.message(F.text == "🔍 Поиск в письмах")
@admin_only
async def menu_email_search_button(message: Message):
    """Обработчик кнопки Поиск в письмах"""
    await message.answer(
        "🔍 <b>Поиск в письмах</b>\n\n"
        "Введите текст для поиска в письмах:",
        parse_mode="HTML",
        reply_markup=get_back_menu()
    )

@router.message(F.text == "📈 Статистика почты")
@admin_only
async def menu_email_stats_button(message: Message):
    """Обработчик кнопки Статистика почты"""
    await show_email_stats(message)

# ============ ФУНКЦИИ ПРОСМОТРА ДАННЫХ ============

async def show_channels_status(message: Message):
    """Показать статус каналов"""
    monitor = get_monitor_from_context()
    db = JsonDatabase()
    settings = db.load_settings()
    channels = db.get_channels()
    
    monitoring_status = "🟢 Активен" if settings.get("monitoring_enabled", False) else "🔴 Неактивен"
    channels_count = len(channels)
    keywords_count = len(settings.get("keywords", []))
    total_messages = len(db.load_found_messages())
    
    text = (
        f"📊 <b>Статус каналов</b>\n"
        f"{'═' * 30}\n\n"
        f"🔸 <b>Мониторинг:</b> {monitoring_status}\n"
        f"🔸 <b>Каналов:</b> {channels_count}\n"
        f"🔸 <b>Ключевых слов:</b> {keywords_count}\n"
        f"🔸 <b>Найдено сообщений:</b> {total_messages}\n\n"
    )
    
    if channels:
        text += "📺 <b>Отслеживаемые каналы:</b>\n\n"
        for str_channel_id, channel_name in channels.items():
            channel_id = int(str_channel_id)
            messages_from_channel = len(db.get_messages_by_channel(channel_id))
            text += f"📌 <b>{channel_name}</b> — {messages_from_channel} сообщений\n"
    else:
        text += "❌ <i>Каналы не настроены</i>\n"
    
    text += f"\n{'═' * 30}"
    
    await message.answer(text, parse_mode="HTML", reply_markup=get_back_menu())

async def show_keywords(message: Message):
    """Показать ключевые слова"""
    db = JsonDatabase()
    settings = db.load_settings()
    current_keywords = settings.get("keywords", [])
    
    text = (
        f"🔑 <b>Управление ключевыми словами</b>\n\n"
        f"<b>Текущие ключевые слова:</b>\n"
        f"{'• ' + chr(10).join(current_keywords) if current_keywords else 'Нет ключевых слов'}\n\n"
        f"📈 Всего: <b>{len(current_keywords)}</b> слов(а)\n\n"
        f"💡 <i>Поиск ведется без учета регистра</i>\n\n"
        f"Для изменения ключевых слов введите новые через запятую:"
    )
    
    await message.answer(text, parse_mode="HTML", reply_markup=get_back_menu())

async def show_recent_messages(message: Message, limit: int):
    """Показать последние сообщения"""
    db = JsonDatabase()
    recent_messages = db.get_recent_messages(limit)
    
    if not recent_messages:
        text = f"📭 <b>Нет найденных сообщений</b>\n\nСообщения появятся здесь после срабатывания по ключевым словам."
    else:
        text = f"📨 <b>Последние {len(recent_messages)} найденных сообщений:</b>\n\n"
        
        for i, msg in enumerate(recent_messages, 1):
            channel_name = msg.get('channel_name', 'Неизвестный канал')
            keywords = ', '.join(msg.get('found_keywords', []))
            message_text = msg.get('text', '')[:150] + '...' if len(msg.get('text', '')) > 150 else msg.get('text', '')
            
            moscow_time = format_moscow_time(msg)
            sender_info = format_sender_info(msg)
            
            text += (
                f"<b>{i}. {channel_name}</b>\n"
                f"👤 {sender_info}\n"
                f"🔑 <i>{keywords}</i>\n"
                f"📅 {moscow_time}\n"
                f"💬 {message_text}\n"
                f"{'─' * 25}\n\n"
            )
    
    # Разбиваем длинное сообщение
    if len(text) > 4096:
        parts = [text[i:i+4000] for i in range(0, len(text), 4000)]
        for part in parts:
            await message.answer(part, parse_mode="HTML")
    else:
        await message.answer(text, parse_mode="HTML")
    
    await message.answer("💡 <i>Основное меню:</i>", reply_markup=get_back_menu(), parse_mode="HTML")

async def show_channels_stats(message: Message):
    """Показать статистику каналов"""
    db = JsonDatabase()
    all_messages = db.load_found_messages()
    
    if not all_messages:
        await message.answer(
            "📭 <b>Нет данных для статистики</b>\n\n"
            "Статистика появится после нахождения сообщений.",
            parse_mode="HTML",
            reply_markup=get_back_menu()
        )
        return
    
    channel_stats = {}
    keyword_stats = {}
    
    for msg in all_messages:
        channel_name = msg.get('channel_name', 'Неизвестный канал')
        channel_stats[channel_name] = channel_stats.get(channel_name, 0) + 1
        
        keywords = msg.get('found_keywords', [])
        for kw in keywords:
            keyword_stats[kw] = keyword_stats.get(kw, 0) + 1
    
    text = "📈 <b>Статистика каналов</b>\n\n"
    
    total_messages = sum(channel_stats.values())
    text += f"📊 Всего найдено сообщений: <b>{total_messages}</b>\n\n"
    
    text += "📺 <b>По каналам:</b>\n"
    for channel, count in sorted(channel_stats.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total_messages) * 100 if total_messages > 0 else 0
        text += f"🔸 <b>{channel}</b>: {count} ({percentage:.1f}%)\n"
    
    text += "\n🔑 <b>По ключевым словам:</b>\n"
    for keyword, count in sorted(keyword_stats.items(), key=lambda x: x[1], reverse=True)[:10]:
        text += f"• <b>{keyword}</b>: {count} упоминаний\n"
    
    await message.answer(text, parse_mode="HTML", reply_markup=get_back_menu())

async def show_channels(message: Message):
    """Показать каналы"""
    db = JsonDatabase()
    channels = db.get_channels()
    
    text = "📺 <b>Управление каналами</b>\n\n"
    
    if channels:
        text += "📋 <b>Отслеживаемые каналы:</b>\n\n"
        for str_channel_id, channel_name in channels.items():
            channel_id = int(str_channel_id)
            messages_count = len(db.get_messages_by_channel(channel_id))
            text += f"🔸 <b>{channel_name}</b>\n"
            text += f"   ID: <code>{channel_id}</code>\n"
            text += f"   Найдено: {messages_count} сообщений\n\n"
        
        text += f"📊 Всего каналов: <b>{len(channels)}</b>"
    else:
        text += "📭 <b>Нет отслеживаемых каналов</b>\n\n"
        text += "Добавьте каналы для начала мониторинга."
    
    await message.answer(text, parse_mode="HTML", reply_markup=get_back_menu())

# ============ ФУНКЦИИ РАБОТЫ С ПОЧТОЙ ============

async def show_email_status(message: Message):
    """Показать статус почты"""
    try:
        from gmail_module import get_gmail_monitor
        gmail_monitor = get_gmail_monitor()
        
        if not gmail_monitor:
            await message.answer(
                "❌ <b>Gmail монитор недоступен</b>\n\n"
                "Модуль Gmail не инициализирован.",
                parse_mode="HTML",
                reply_markup=get_back_menu()
            )
            return
        
        stats = gmail_monitor.get_stats()
        
        status = "🟢 Активен" if stats.get('running', False) else "🔴 Неактивен"
        auth_status = "✅ Авторизован" if stats.get('authenticated', False) else "❌ Не авторизован"
        
        text = (
            f"📊 <b>Статус почтового мониторинга</b>\n"
            f"{'═' * 30}\n\n"
            f"📧 <b>Статус:</b> {status}\n"
            f"🔐 <b>Авторизация:</b> {auth_status}\n"
            f"⏱️ <b>Интервал проверки:</b> {stats.get('check_interval', 60)} сек\n"
            f"🕒 <b>Последняя проверка:</b> {stats.get('last_check', 'Никогда')[:16] if stats.get('last_check') else 'Никогда'}\n\n"
            f"📬 <b>Обработано писем:</b> {stats.get('processed_emails_count', 0)}\n\n"
            f"{'═' * 30}"
        )
        
        await message.answer(text, parse_mode="HTML", reply_markup=get_back_menu())
        
    except Exception as e:
        logger.error(f"Ошибка при получении статуса почты: {e}")
        await message.answer(
            "❌ <b>Ошибка получения статуса</b>\n\n"
            "Не удалось получить статус почтового мониторинга.",
            parse_mode="HTML",
            reply_markup=get_back_menu()
        )

async def show_inbox_emails(message: Message):
    """Показать входящие письма"""
    try:
        from gmail_module import get_gmail_monitor
        gmail_monitor = get_gmail_monitor()
        
        if not gmail_monitor:
            await message.answer(
                "❌ <b>Gmail монитор недоступен</b>\n\n"
                "Модуль Gmail не инициализирован.",
                parse_mode="HTML",
                reply_markup=get_back_menu()
            )
            return
        
        emails = gmail_monitor.get_recent_emails(limit=10)
        
        if not emails:
            await message.answer(
                "📭 <b>Нет входящих писем</b>\n\n"
                "В папке входящих пока нет писем.",
                parse_mode="HTML",
                reply_markup=get_back_menu()
            )
            return
        
        text = f"📬 <b>Последние {len(emails)} входящих писем:</b>\n\n"
        
        for i, email in enumerate(emails, 1):
            sender = email.get('sender', 'Неизвестный')
            subject = email.get('subject', 'Без темы')
            date = email.get('date', 'Неизвестно')
            snippet = email.get('snippet', '')[:100] + '...' if len(email.get('snippet', '')) > 100 else email.get('snippet', '')
            
            text += (
                f"<b>{i}. {subject}</b>\n"
                f"👤 От: {sender}\n"
                f"📅 {date}\n"
                f"💬 {snippet}\n"
                f"{'─' * 25}\n\n"
            )
        
        await message.answer(text, parse_mode="HTML", reply_markup=get_back_menu())
        
    except Exception as e:
        logger.error(f"Ошибка при получении входящих писем: {e}")
        await message.answer(
            "❌ <b>Ошибка получения писем</b>\n\n"
            "Не удалось получить список входящих писем.",
            parse_mode="HTML",
            reply_markup=get_back_menu()
        )

async def show_unread_emails(message: Message):
    """Показать непрочитанные письма"""
    try:
        from gmail_module import get_gmail_monitor
        gmail_monitor = get_gmail_monitor()
        
        if not gmail_monitor:
            await message.answer(
                "❌ <b>Gmail монитор недоступен</b>\n\n"
                "Модуль Gmail не инициализирован.",
                parse_mode="HTML",
                reply_markup=get_back_menu()
            )
            return
        
        unread_emails = gmail_monitor.get_unread_emails()
        
        if not unread_emails:
            await message.answer(
                "✅ <b>Нет непрочитанных писем</b>\n\n"
                "Все письма прочитаны!",
                parse_mode="HTML",
                reply_markup=get_back_menu()
            )
            return
        
        text = f"📩 <b>Непрочитанных писем: {len(unread_emails)}</b>\n\n"
        
        for i, email in enumerate(unread_emails[:10], 1):
            sender = email.get('sender', 'Неизвестный')
            subject = email.get('subject', 'Без темы')
            date = email.get('date', 'Неизвестно')
            snippet = email.get('snippet', '')[:100] + '...' if len(email.get('snippet', '')) > 100 else email.get('snippet', '')
            
            text += (
                f"<b>📧 {i}. {subject}</b>\n"
                f"👤 От: {sender}\n"
                f"📅 {date}\n"
                f"💬 {snippet}\n"
                f"{'─' * 25}\n\n"
            )
        
        if len(unread_emails) > 10:
            text += f"... и еще {len(unread_emails) - 10} писем"
        
        await message.answer(text, parse_mode="HTML", reply_markup=get_back_menu())
        
    except Exception as e:
        logger.error(f"Ошибка при получении непрочитанных писем: {e}")
        await message.answer(
            "❌ <b>Ошибка получения писем</b>\n\n"
            "Не удалось получить список непрочитанных писем.",
            parse_mode="HTML",
            reply_markup=get_back_menu()
        )

async def show_email_stats(message: Message):
    """Показать статистику почты"""
    try:
        from gmail_module import get_gmail_monitor
        gmail_monitor = get_gmail_monitor()
        
        if not gmail_monitor:
            await message.answer(
                "❌ <b>Gmail монитор недоступен</b>\n\n"
                "Модуль Gmail не инициализирован.",
                parse_mode="HTML",
                reply_markup=get_back_menu()
            )
            return
        
        stats = gmail_monitor.get_detailed_stats()
        
        text = (
            f"📈 <b>Статистика почты</b>\n"
            f"{'═' * 30}\n\n"
            f"📊 <b>Общая статистика:</b>\n"
            f"📬 Всего писем: {stats.get('total_emails', 0)}\n"
            f"📩 Непрочитанных: {stats.get('unread_count', 0)}\n"
            f"✅ Прочитанных: {stats.get('read_count', 0)}\n\n"
            f"📅 <b>За последние 24 часа:</b>\n"
            f"📨 Получено: {stats.get('today_received', 0)}\n\n"
            f"🎯 <b>Мониторинг:</b>\n"
            f"⏱️ Время работы: {stats.get('uptime', 'Неизвестно')}\n\n"
            f"{'═' * 30}"
        )
        
        await message.answer(text, parse_mode="HTML", reply_markup=get_back_menu())
        
    except Exception as e:
        logger.error(f"Ошибка при получении статистики почты: {e}")
        await message.answer(
            "❌ <b>Ошибка получения статистики</b>\n\n"
            "Не удалось получить статистику почты.",
            parse_mode="HTML",
            reply_markup=get_back_menu()
        )

async def send_email_start(message: Message, state: FSMContext):
    """Начать процесс отправки письма"""
    text = (
        "✉️ <b>Отправка письма</b>\n\n"
        "📝 Введите адрес получателя:\n\n"
        "💡 <b>Примеры:</b>\n"
        "• user@example.com\n"
        "• test.email@gmail.com\n\n"
        "❌ Для отмены отправьте /cancel"
    )
    
    await state.set_state(AdminStates.waiting_for_email_recipient)
    await message.answer(text, parse_mode="HTML", reply_markup=get_back_menu())

async def show_help(message: Message):
    """Показать справку"""
    text = (
        "📖 <b>Справка по Stalker Bot</b>\n\n"
        "🤖 <b>Что делает бот:</b>\n"
        "• Мониторит Telegram каналы\n"
        "• Мониторит Gmail почту\n"
        "• Ищет сообщения с ключевыми словами\n"
        "• Сохраняет находки в базу данных\n"
        "• Отправляет уведомления в реальном времени\n\n"
        "📺 <b>Раздел каналов:</b>\n"
        "• Добавление/удаление каналов\n"
        "• Просмотр найденных сообщений\n"
        "• Статистика по каналам\n\n"
        "📧 <b>Раздел почты:</b>\n"
        "• Просмотр входящих писем\n"
        "• Отправка писем\n"
        "• Статистика почты\n\n"
        "⚙️ <b>Настройки:</b>\n"
        "• Управление ключевыми словами\n"
        "• Очистка базы данных\n"
        "• Управление администраторами\n\n"
        "💡 <b>Совет:</b> Используйте кнопки меню для навигации!"
    )
    
    await message.answer(text, parse_mode="HTML", reply_markup=get_back_menu())
