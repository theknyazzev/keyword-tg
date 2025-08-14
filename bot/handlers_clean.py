"""
Обработчики команд для управляющего бота - ОЧИЩЕННАЯ ВЕРСИЯ БЕЗ GMAIL
"""
import logging
import inspect
import os
import html
import math
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
    waiting_for_message_search = State()

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

def escape_html(text):
    """Экранирует HTML символы для безопасного отображения в Telegram"""
    if not text:
        return ""
    return html.escape(str(text))

def get_main_menu(user_id: int = None):
    """Создает простое главное меню"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📺 Каналы"),
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

async def safe_callback_answer(callback: CallbackQuery, text: str = "OK"):
    """Безопасный ответ на callback query с обработкой старых запросов"""
    try:
        await callback.answer(text)
    except TelegramBadRequest as e:
        error_message = str(e).lower()
        if "query is too old" in error_message or "query id is invalid" in error_message:
            # Игнорируем ошибки старых callback queries
            logger.debug(f"Игнорируем старый callback query: {e}")
            pass
        else:
            # Логируем другие ошибки
            logger.error(f"Ошибка callback.answer(): {e}")
    except Exception as e:
        logger.error(f"Неожиданная ошибка callback.answer(): {e}")

async def safe_edit_message(callback: CallbackQuery, text: str, reply_markup=None, parse_mode="HTML"):
    """Безопасное редактирование сообщения с обработкой старых queries"""
    try:
        if reply_markup is not None:
            await callback.message.edit_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
        else:
            await callback.message.edit_text(text, parse_mode=parse_mode)
        await safe_callback_answer(callback)
    except TelegramBadRequest as e:
        error_message = str(e).lower()
        if "message is not modified" in error_message:
            await safe_callback_answer(callback, "✅ Данные актуальны!")
        elif "query is too old" in error_message or "query id is invalid" in error_message:
            # Пытаемся отправить новое сообщение вместо редактирования
            try:
                await callback.message.answer(text, reply_markup=reply_markup, parse_mode=parse_mode)
            except Exception as send_error:
                logger.error(f"Не удалось отправить новое сообщение: {send_error}")
        else:
            logger.error(f"Ошибка при редактировании сообщения: {e}")
            await safe_callback_answer(callback, "❌ Ошибка при обновлении")
    except Exception as e:
        logger.error(f"Неожиданная ошибка при редактировании сообщения: {e}")
        await safe_callback_answer(callback, "❌ Произошла ошибка")

def get_monitor_from_context():
    """Получает монитор из глобального контекста"""
    return get_monitor_instance()

# ============ ОСНОВНЫЕ КОМАНДЫ ============

@router.message(Command("start"))
@admin_only
async def cmd_start(message: Message, state: FSMContext = None):
    """Обработчик команды /start"""
    # Сбрасываем любое активное состояние
    if state:
        await state.clear()
    
    db = JsonDatabase()
    
    inline_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔄 Обновить", callback_data="menu_refresh"),
            InlineKeyboardButton(text="📊 Статус", callback_data="menu_status")
        ]
    ])
    
    text = (
        "🎯 <b>Stalker Bot</b> - Система мониторинга каналов\n\n"
        "🚀 <b>Возможности бота:</b>\n"
        "• 🔍 Мониторинг каналов в реальном времени\n"
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

@router.message(Command("cancel"))
@admin_only
async def cmd_cancel(message: Message, state: FSMContext):
    """Обработчик команды /cancel для сброса состояния"""
    await state.clear()
    await message.answer(
        "❌ <b>Операция отменена</b>\n\n"
        "Все активные действия сброшены.",
        parse_mode="HTML",
        reply_markup=get_main_menu(message.from_user.id)
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
async def menu_home_button(message: Message, state: FSMContext = None):
    """Обработчик кнопки Главное меню"""
    # Сбрасываем любое активное состояние
    if state:
        await state.clear()
    await cmd_start(message, state)

# ============ ОБРАБОТЧИКИ КНОПОК КАНАЛОВ ============

@router.message(F.text == "📊 Статус каналов")
@admin_only
async def menu_channels_status_button(message: Message):
    """Обработчик кнопки Статус каналов"""
    await show_channels_status(message)

@router.message(F.text == "🔍 Поиск в сообщениях")
@admin_only
async def menu_search_messages_button(message: Message, state: FSMContext):
    """Обработчик кнопки Поиск в сообщениях"""
    await state.set_state(AdminStates.waiting_for_message_search)
    await message.answer(
        "🔍 <b>Поиск в сообщениях каналов</b>\n\n"
        "📝 Введите текст для поиска в найденных сообщениях:\n\n"
        "💡 <b>Примеры поиска:</b>\n"
        "• криптовалюта\n"
        "• скидка\n"
        "• новости\n\n"
        "🔎 Поиск будет выполнен среди всех сохраненных сообщений\n\n"
        "❌ Для отмены введите /cancel",
        parse_mode="HTML",
        reply_markup=get_back_menu()
    )

@router.message(F.text == "📝 Ключевые слова")
@admin_only
async def menu_keywords_button(message: Message, state: FSMContext):
    """Обработчик кнопки Ключевые слова"""
    db = JsonDatabase()
    settings = db.load_settings()
    current_keywords = settings.get("keywords", [])
    
    text = (
        f"🔑 <b>Управление ключевыми словами</b>\n\n"
        f"<b>Текущие ключевые слова:</b>\n"
        f"{'• ' + chr(10).join(current_keywords) if current_keywords else 'Нет ключевых слов'}\n\n"
        f"📈 Всего: <b>{len(current_keywords)}</b> слов(а)\n\n"
        f"💡 <i>Поиск ведется без учета регистра</i>\n\n"
    )
    
    # Создаем inline клавиатуру для управления ключевыми словами
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✏️ Изменить слова", callback_data="keywords_edit"),
            InlineKeyboardButton(text="🔄 Обновить список", callback_data="keywords_refresh")
        ]
    ])
    
    await message.answer(text, parse_mode="HTML", reply_markup=keyboard)

@router.message(F.text == "📨 Найденные сообщения")
@admin_only
async def menu_found_messages_button(message: Message):
    """Обработчик кнопки Найденные сообщения"""
    await show_recent_messages(message, 50, 1)

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

@router.message(F.text == "👥 Управление админами")
@super_admin_only
async def menu_admin_management_button(message: Message):
    """Обработчик кнопки Управление админами"""
    await show_admin_management(message)

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

async def show_recent_messages(message: Message, limit: int = 50, page: int = 1):
    """Показать последние сообщения с пагинацией"""
    db = JsonDatabase()
    recent_messages = db.get_recent_messages(limit)
    
    if not recent_messages:
        text = f"📭 <b>Нет найденных сообщений</b>\n\nСообщения появятся здесь после срабатывания по ключевым словам."
        await message.answer(text, parse_mode="HTML", reply_markup=get_back_menu())
        return
    
    # Настройки пагинации
    messages_per_page = 5
    total_messages = len(recent_messages)
    total_pages = math.ceil(total_messages / messages_per_page)
    
    # Проверяем корректность страницы
    if page < 1:
        page = 1
    elif page > total_pages:
        page = total_pages
    
    # Вычисляем индексы для текущей страницы
    start_idx = (page - 1) * messages_per_page
    end_idx = min(start_idx + messages_per_page, total_messages)
    page_messages = recent_messages[start_idx:end_idx]
    
    # Формируем текст сообщения
    text = f"📨 <b>Найденные сообщения</b>\n"
    text += f"📄 Страница {page} из {total_pages} (всего: {total_messages})\n\n"
    
    for i, msg in enumerate(page_messages, start_idx + 1):
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
    
    # Создаем inline клавиатуру для пагинации
    keyboard_buttons = []
    
    if total_pages > 1:
        nav_buttons = []
        
        # Кнопка "Назад" (если не первая страница)
        if page > 1:
            nav_buttons.append(InlineKeyboardButton(
                text="⬅️ Назад", 
                callback_data=f"messages_page_{page-1}"
            ))
        
        # Кнопка с номером страницы
        nav_buttons.append(InlineKeyboardButton(
            text=f"📄 {page}/{total_pages}",
            callback_data="messages_page_current"
        ))
        
        # Кнопка "Вперед" (если не последняя страница)
        if page < total_pages:
            nav_buttons.append(InlineKeyboardButton(
                text="Вперед ➡️", 
                callback_data=f"messages_page_{page+1}"
            ))
        
        keyboard_buttons.append(nav_buttons)
    
    # Кнопка обновления
    keyboard_buttons.append([
        InlineKeyboardButton(text="🔄 Обновить", callback_data="messages_refresh")
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    await message.answer(text, parse_mode="HTML", reply_markup=keyboard)

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

async def show_help(message: Message):
    """Показать справку"""
    text = (
        "📖 <b>Справка по Stalker Bot</b>\n\n"
        "🤖 <b>Что делает бот:</b>\n"
        "• Мониторит Telegram каналы\n"
        "• Ищет сообщения с ключевыми словами\n"
        "• Сохраняет находки в базу данных\n"
        "• Отправляет уведомления в реальном времени\n\n"
        "📺 <b>Раздел каналов:</b>\n"
        "• Добавление/удаление каналов\n"
        "• Просмотр найденных сообщений\n"
        "• Статистика по каналам\n\n"
        "⚙️ <b>Настройки:</b>\n"
        "• Управление ключевыми словами\n"
        "• Очистка базы данных\n"
        "• Управление администраторами\n\n"
        "💡 <b>Совет:</b> Используйте кнопки меню для навигации!"
    )
    
    await message.answer(text, parse_mode="HTML", reply_markup=get_back_menu())

# ============ ФУНКЦИИ УПРАВЛЕНИЯ КАНАЛАМИ ============

@router.message(F.text == "➕ Добавить канал")
@admin_only
async def menu_add_channel_button(message: Message, state: FSMContext):
    """Обработчик кнопки добавления канала"""
    await state.set_state(AdminStates.waiting_for_channel_id)
    text = (
        "➕ <b>Добавление канала</b>\n\n"
        "📝 Введите ID канала для мониторинга:\n\n"
        "💡 <b>Как получить ID канала:</b>\n"
        "1. Перешлите сообщение из канала в @userinfobot\n"
        "2. Или используйте @getmyid_bot\n"
        "3. ID канала начинается с -100\n\n"
        "📌 <b>Пример:</b> -1001234567890\n\n"
        "❌ Для отмены введите /cancel"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=get_back_menu())

@router.message(F.text == "➖ Удалить канал")
@admin_only
async def menu_remove_channel_button(message: Message, state: FSMContext):
    """Обработчик кнопки удаления канала"""
    db = JsonDatabase()
    channels = db.get_channels()
    
    if not channels:
        await message.answer(
            "❌ <b>Нет каналов для удаления</b>\n\n"
            "Сначала добавьте каналы для мониторинга.",
            parse_mode="HTML",
            reply_markup=get_back_menu()
        )
        return
    
    await state.set_state(AdminStates.waiting_for_remove_channel_id)
    
    text = (
        "➖ <b>Удаление канала</b>\n\n"
        "📝 Введите ID канала для удаления:\n\n"
        "📺 <b>Текущие каналы:</b>\n\n"
    )
    
    for channel_id, channel_name in channels.items():
        text += f"• <b>{channel_name}</b>\n   ID: <code>{channel_id}</code>\n\n"
    
    text += "❌ Для отмены введите /cancel"
    
    await message.answer(text, parse_mode="HTML", reply_markup=get_back_menu())

# ============ ОСТАЛЬНЫЕ ФУНКЦИИ И ОБРАБОТЧИКИ ============
# (Добавлю остальные функции без Gmail...)

# Заглушка для остальных функций - они будут добавлены в следующих обновлениях
