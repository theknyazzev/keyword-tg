"""
Обработчики команд для управляющего бота
"""

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import ADMIN_ID, MONITORED_CHANNELS
from database import JsonDatabase
from .globals import get_monitor_instance


logger = logging.getLogger(__name__)
router = Router()


def get_monitor_from_context():
    """Получает монитор из глобального контекста"""
    return get_monitor_instance()


class AdminStates(StatesGroup):
    waiting_for_keywords = State()


def admin_only(func):
    """Декоратор для проверки прав администратора"""
    async def wrapper(message: Message, *args, **kwargs):
        if message.from_user.id != ADMIN_ID:
            await message.answer("⛔ У вас нет прав для выполнения этой команды")
            return
        return await func(message, *args, **kwargs)
    return wrapper


# ============ ГЛАВНОЕ МЕНЮ ============

@router.message(Command("start"))
@admin_only
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Статус", callback_data="menu_status"),
            InlineKeyboardButton(text="📝 Ключевые слова", callback_data="menu_keywords")
        ],
        [
            InlineKeyboardButton(text="📺 Каналы", callback_data="menu_channels"),
            InlineKeyboardButton(text="📨 Последние сообщения", callback_data="menu_recent")
        ],
        [
            InlineKeyboardButton(text="⚙️ Настройки", callback_data="menu_settings"),
            InlineKeyboardButton(text="🧹 Очистить базу", callback_data="menu_clear")
        ],
        [
            InlineKeyboardButton(text="ℹ️ Помощь", callback_data="menu_help"),
            InlineKeyboardButton(text="🔄 Обновить меню", callback_data="menu_refresh")
        ]
    ])
    
    text = (
        "🤖 <b>Stalker Bot - Панель управления</b>\n\n"
        "🎯 <b>Что умеет бот:</b>\n"
        "• Мониторит 6 каналов в режиме реального времени\n"
        "• Ищет сообщения с ключевыми словами\n"
        "• Сохраняет найденные сообщения в базу\n"
        "• Отправляет уведомления о новых находках\n\n"
        "👇 <b>Выберите действие:</b>"
    )
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data == "menu_refresh")
async def callback_menu_refresh(callback: CallbackQuery):
    """Обновление главного меню"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Статус", callback_data="menu_status"),
            InlineKeyboardButton(text="📝 Ключевые слова", callback_data="menu_keywords")
        ],
        [
            InlineKeyboardButton(text="📺 Каналы", callback_data="menu_channels"),
            InlineKeyboardButton(text="📨 Последние сообщения", callback_data="menu_recent")
        ],
        [
            InlineKeyboardButton(text="⚙️ Настройки", callback_data="menu_settings"),
            InlineKeyboardButton(text="🧹 Очистить базу", callback_data="menu_clear")
        ],
        [
            InlineKeyboardButton(text="ℹ️ Помощь", callback_data="menu_help"),
            InlineKeyboardButton(text="🔄 Обновить меню", callback_data="menu_refresh")
        ]
    ])
    
    text = (
        "🤖 <b>Stalker Bot - Панель управления</b>\n\n"
        "🎯 <b>Что умеет бот:</b>\n"
        "• Мониторит 6 каналов в режиме реального времени\n"
        "• Ищет сообщения с ключевыми словами\n"
        "• Сохраняет найденные сообщения в базу\n"
        "• Отправляет уведомления о новых находках\n\n"
        "👇 <b>Выберите действие:</b>"
    )
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer("Меню обновлено!")


# ============ СТАТУС ============

@router.message(Command("status"))
@admin_only
async def cmd_status(message: Message):
    """Команда /status"""
    await show_status(message)


@router.callback_query(F.data == "menu_status")
async def callback_menu_status(callback: CallbackQuery):
    """Статус через кнопку"""
    await show_status(callback.message, callback)


async def show_status(message: Message, callback: CallbackQuery = None):
    """Показать статус мониторинга"""
    monitor = get_monitor_from_context()
    db = JsonDatabase()
    settings = db.load_settings()
    recent_messages = db.get_recent_messages(1)
    
    monitoring_status = "🟢 Активен" if settings.get("monitoring_enabled", False) else "🔴 Неактивен"
    channels_count = len(MONITORED_CHANNELS)
    keywords_count = len(settings.get("keywords", []))
    total_messages = len(db.load_found_messages())
    
    last_message_time = "Нет сообщений"
    if recent_messages:
        last_message_time = recent_messages[-1].get('timestamp', 'Неизвестно')
    
    text = (
        f"📊 <b>Статус мониторинга</b>\n\n"
        f"🔸 Статус: {monitoring_status}\n"
        f"🔸 Каналов отслеживается: {channels_count}\n"
        f"🔸 Ключевых слов: {keywords_count}\n"
        f"🔸 Всего найдено сообщений: {total_messages}\n"
        f"🔸 Последнее сообщение: {last_message_time}\n\n"
        f"📺 <b>Отслеживаемые каналы:</b>\n"
    )
    
    for channel_id, channel_name in MONITORED_CHANNELS.items():
        messages_from_channel = len(db.get_messages_by_channel(channel_id))
        text += f"• {channel_name} ({messages_from_channel} сообщений)\n"
    
    if callback:
        back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Обновить статус", callback_data="menu_status"),
                InlineKeyboardButton(text="⚙️ Настройки", callback_data="menu_settings")
            ],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu_refresh")]
        ])
        await callback.message.edit_text(text, reply_markup=back_keyboard, parse_mode="HTML")
        await callback.answer()
    else:
        await message.answer(text, parse_mode="HTML")


# ============ КЛЮЧЕВЫЕ СЛОВА ============

@router.message(Command("keywords"))
@admin_only
async def cmd_keywords(message: Message):
    """Команда /keywords"""
    await show_keywords(message)


@router.callback_query(F.data == "menu_keywords")
async def callback_menu_keywords(callback: CallbackQuery):
    """Ключевые слова через кнопку"""
    await show_keywords(callback.message, callback)


async def show_keywords(message: Message, callback: CallbackQuery = None):
    """Показать ключевые слова"""
    db = JsonDatabase()
    settings = db.load_settings()
    current_keywords = settings.get("keywords", [])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Изменить ключевые слова", callback_data="edit_keywords")],
        [
            InlineKeyboardButton(text="🔄 Обновить", callback_data="menu_keywords"),
            InlineKeyboardButton(text="📊 Статистика", callback_data="keywords_stats")
        ],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu_refresh")]
    ])
    
    text = (
        f"🔑 <b>Управление ключевыми словами</b>\n\n"
        f"<b>Текущие ключевые слова:</b>\n"
        f"{'• ' + chr(10).join(current_keywords) if current_keywords else 'Нет ключевых слов'}\n\n"
        f"📈 Всего: <b>{len(current_keywords)}</b> слов(а)\n\n"
        f"💡 <i>Поиск ведется без учета регистра</i>"
    )
    
    if callback:
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer()
    else:
        await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data == "edit_keywords")
async def callback_edit_keywords(callback: CallbackQuery, state: FSMContext):
    """Редактирование ключевых слов"""
    await callback.message.edit_text(
        "✏️ <b>Введите новые ключевые слова через запятую:</b>\n\n"
        "Например: <code>ищу, wordpress, freelance, работа</code>\n\n"
        "💡 <i>Отправьте /cancel для отмены</i>",
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.waiting_for_keywords)
    await callback.answer()


@router.message(StateFilter(AdminStates.waiting_for_keywords))
async def process_keywords_input(message: Message, state: FSMContext):
    """Обработка ввода ключевых слов"""
    if message.text == "/cancel":
        await message.answer("❌ Изменение ключевых слов отменено")
        await state.clear()
        return
    
    keywords_input = message.text.strip()
    
    if not keywords_input:
        await message.answer("❌ Пустой ввод. Попробуйте еще раз:")
        return
    
    # Разделяем по запятым и очищаем
    new_keywords = [kw.strip().lower() for kw in keywords_input.split(',') if kw.strip()]
    
    if not new_keywords:
        await message.answer("❌ Не удалось обработать ключевые слова. Попробуйте еще раз:")
        return
    
    # Сохраняем в базу
    monitor = get_monitor_from_context()
    db = JsonDatabase()
    settings = db.load_settings()
    settings["keywords"] = new_keywords
    db.save_settings(settings)
    
    # Обновляем в мониторе если он доступен
    if monitor:
        monitor.update_keywords(new_keywords)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 К ключевым словам", callback_data="menu_keywords")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu_refresh")]
    ])
    
    await message.answer(
        f"✅ <b>Ключевые слова обновлены!</b>\n\n"
        f"🔑 Новые ключевые слова:\n• {chr(10).join(new_keywords)}",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    
    await state.clear()


@router.callback_query(F.data == "keywords_stats")
async def callback_keywords_stats(callback: CallbackQuery):
    """Статистика по ключевым словам"""
    db = JsonDatabase()
    all_messages = db.load_found_messages()
    
    keyword_stats = {}
    for msg in all_messages:
        keywords = msg.get('found_keywords', [])
        for kw in keywords:
            keyword_stats[kw] = keyword_stats.get(kw, 0) + 1
    
    text = "📈 <b>Статистика по ключевым словам</b>\n\n"
    
    if keyword_stats:
        text += "🔑 <b>Популярность слов:</b>\n"
        for keyword, count in sorted(keyword_stats.items(), key=lambda x: x[1], reverse=True):
            text += f"• <b>{keyword}</b>: {count} упоминаний\n"
    else:
        text += "📭 Пока нет статистики по ключевым словам"
    
    back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 К ключевым словам", callback_data="menu_keywords")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu_refresh")]
    ])
    
    await callback.message.edit_text(text, reply_markup=back_keyboard, parse_mode="HTML")
    await callback.answer()


# ============ КАНАЛЫ ============

@router.message(Command("channels"))
@admin_only
async def cmd_channels(message: Message):
    """Команда /channels"""
    await show_channels(message)


@router.callback_query(F.data == "menu_channels")
async def callback_menu_channels(callback: CallbackQuery):
    """Каналы через кнопку"""
    await show_channels(callback.message, callback)


async def show_channels(message: Message, callback: CallbackQuery = None):
    """Показать каналы"""
    db = JsonDatabase()
    
    text = "📺 <b>Отслеживаемые каналы</b>\n\n"
    
    for channel_id, channel_name in MONITORED_CHANNELS.items():
        messages_count = len(db.get_messages_by_channel(channel_id))
        text += f"🔸 <b>{channel_name}</b>\n"
        text += f"   ID: <code>{channel_id}</code>\n"
        text += f"   Найдено: {messages_count} сообщений\n\n"
    
    text += f"📊 Всего активных каналов: <b>{len(MONITORED_CHANNELS)}</b>"
    
    if callback:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Обновить", callback_data="menu_channels"),
                InlineKeyboardButton(text="📊 Статистика", callback_data="channels_stats")
            ],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu_refresh")]
        ])
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer()
    else:
        await message.answer(text, parse_mode="HTML")


@router.callback_query(F.data == "channels_stats")
async def callback_channels_stats(callback: CallbackQuery):
    """Статистика по каналам"""
    db = JsonDatabase()
    all_messages = db.load_found_messages()
    
    channel_stats = {}
    for msg in all_messages:
        channel_name = msg.get('channel_name', 'Неизвестный канал')
        channel_stats[channel_name] = channel_stats.get(channel_name, 0) + 1
    
    text = "📊 <b>Детальная статистика по каналам</b>\n\n"
    
    if channel_stats:
        total_messages = sum(channel_stats.values())
        text += f"📈 Всего найдено сообщений: <b>{total_messages}</b>\n\n"
        
        for channel, count in sorted(channel_stats.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_messages) * 100 if total_messages > 0 else 0
            text += f"🔸 <b>{channel}</b>\n"
            text += f"   Сообщений: {count} ({percentage:.1f}%)\n\n"
    else:
        text += "📭 Пока нет сообщений для статистики"
    
    back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 К каналам", callback_data="menu_channels")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu_refresh")]
    ])
    
    await callback.message.edit_text(text, reply_markup=back_keyboard, parse_mode="HTML")
    await callback.answer()


# ============ ПОСЛЕДНИЕ СООБЩЕНИЯ ============

@router.message(Command("recent"))
@admin_only
async def cmd_recent(message: Message):
    """Команда /recent"""
    # Парсим количество из команды
    args = message.text.split()
    limit = 5  # по умолчанию
    
    if len(args) > 1:
        try:
            limit = int(args[1])
            limit = min(max(limit, 1), 20)  # от 1 до 20
        except ValueError:
            pass
    
    await show_recent_messages(message, limit)


@router.callback_query(F.data == "menu_recent")
async def callback_menu_recent(callback: CallbackQuery):
    """Выбор количества последних сообщений"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📨 5 последних", callback_data="recent_5"),
            InlineKeyboardButton(text="📨 10 последних", callback_data="recent_10")
        ],
        [
            InlineKeyboardButton(text="📨 20 последних", callback_data="recent_20"),
            InlineKeyboardButton(text="📨 Все сегодня", callback_data="recent_today")
        ],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu_refresh")]
    ])
    
    text = (
        "📨 <b>Последние найденные сообщения</b>\n\n"
        "Выберите количество сообщений для просмотра:"
    )
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("recent_"))
async def callback_show_recent(callback: CallbackQuery):
    """Показ последних сообщений"""
    data = callback.data.split("_")[1]
    
    if data == "today":
        # Показать сообщения за сегодня
        from datetime import datetime, date
        db = JsonDatabase()
        all_messages = db.load_found_messages()
        today = date.today().isoformat()
        recent_messages = [msg for msg in all_messages if msg.get('timestamp', '').startswith(today)]
        limit_text = "за сегодня"
    else:
        limit = int(data)
        db = JsonDatabase()
        recent_messages = db.get_recent_messages(limit)
        limit_text = f"{limit} последних"
    
    await show_recent_messages(callback.message, recent_messages, limit_text, callback)


async def show_recent_messages(message: Message, limit_or_messages, limit_text: str = None, callback: CallbackQuery = None):
    """Показать последние сообщения"""
    if isinstance(limit_or_messages, int):
        db = JsonDatabase()
        recent_messages = db.get_recent_messages(limit_or_messages)
        limit_text = f"{limit_or_messages} последних"
    else:
        recent_messages = limit_or_messages
    
    if not recent_messages:
        text = f"📭 <b>Нет сообщений {limit_text if limit_text else ''}</b>"
    else:
        text = f"📨 <b>{len(recent_messages)} сообщений {limit_text if limit_text else ''}:</b>\n\n"
        
        for i, msg in enumerate(recent_messages, 1):
            channel_name = msg.get('channel_name', 'Неизвестный канал')
            keywords = ', '.join(msg.get('found_keywords', []))
            message_text = msg.get('text', '')[:150] + '...' if len(msg.get('text', '')) > 150 else msg.get('text', '')
            timestamp = msg.get('timestamp', 'Неизвестно')
            
            text += (
                f"<b>{i}. {channel_name}</b>\n"
                f"🔑 <i>{keywords}</i>\n"
                f"📅 {timestamp}\n"
                f"💬 {message_text}\n"
                f"{'─' * 25}\n\n"
            )
    
    if callback:
        back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Обновить", callback_data=callback.data),
                InlineKeyboardButton(text="🔙 Назад", callback_data="menu_recent")
            ],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu_refresh")]
        ])
        
        # Разбиваем длинное сообщение
        if len(text) > 4096:
            parts = [text[i:i+4000] for i in range(0, len(text), 4000)]
            for i, part in enumerate(parts):
                if i == len(parts) - 1:  # Последняя часть
                    await callback.message.edit_text(part, reply_markup=back_keyboard, parse_mode="HTML")
                else:
                    await callback.message.answer(part, parse_mode="HTML")
        else:
            await callback.message.edit_text(text, reply_markup=back_keyboard, parse_mode="HTML")
        await callback.answer()
    else:
        # Разбиваем длинное сообщение для обычной команды
        if len(text) > 4096:
            parts = [text[i:i+4096] for i in range(0, len(text), 4096)]
            for part in parts:
                await message.answer(part, parse_mode="HTML")
        else:
            await message.answer(text, parse_mode="HTML")


# ============ НАСТРОЙКИ ============

@router.message(Command("settings"))
@admin_only
async def cmd_settings(message: Message):
    """Команда /settings"""
    await show_settings(message)


@router.callback_query(F.data == "menu_settings")
async def callback_menu_settings(callback: CallbackQuery):
    """Настройки через кнопку"""
    await show_settings(callback.message, callback)


async def show_settings(message: Message, callback: CallbackQuery = None):
    """Показать настройки"""
    db = JsonDatabase()
    settings = db.load_settings()
    
    monitoring_status = "🟢 Включен" if settings.get("monitoring_enabled", False) else "🔴 Выключен"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🔄 Переключить мониторинг", 
            callback_data="toggle_monitoring"
        )],
        [
            InlineKeyboardButton(text="📊 Статистика", callback_data="show_stats"),
            InlineKeyboardButton(text="🔄 Обновить", callback_data="menu_settings")
        ],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu_refresh")]
    ])
    
    text = (
        f"⚙️ <b>Настройки бота</b>\n\n"
        f"🔸 Мониторинг: {monitoring_status}\n"
        f"🔸 Каналов: {len(MONITORED_CHANNELS)}\n"
        f"🔸 Ключевых слов: {len(settings.get('keywords', []))}\n"
        f"🔸 Последнее обновление: {settings.get('last_update', 'Неизвестно')}\n\n"
        f"💡 <i>Управляйте настройками с помощью кнопок ниже</i>"
    )
    
    if callback:
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer()
    else:
        await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data == "toggle_monitoring")
async def callback_toggle_monitoring(callback: CallbackQuery):
    """Переключение мониторинга"""
    db = JsonDatabase()
    settings = db.load_settings()
    
    # Переключаем статус
    current_status = settings.get("monitoring_enabled", False)
    settings["monitoring_enabled"] = not current_status
    db.save_settings(settings)
    
    new_status = "🟢 Включен" if settings["monitoring_enabled"] else "🔴 Выключен"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🔄 Переключить мониторинг", 
            callback_data="toggle_monitoring"
        )],
        [
            InlineKeyboardButton(text="📊 Статистика", callback_data="show_stats"),
            InlineKeyboardButton(text="🔄 Обновить", callback_data="menu_settings")
        ],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu_refresh")]
    ])
    
    text = (
        f"⚙️ <b>Настройки бота</b>\n\n"
        f"🔸 Мониторинг: {new_status}\n"
        f"🔸 Каналов: {len(MONITORED_CHANNELS)}\n"
        f"🔸 Ключевых слов: {len(settings.get('keywords', []))}\n"
        f"🔸 Последнее обновление: {settings.get('last_update', 'Неизвестно')}\n\n"
        f"💡 <i>Управляйте настройками с помощью кнопок ниже</i>"
    )
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer(f"Мониторинг {'включен' if settings['monitoring_enabled'] else 'выключен'}!")


@router.callback_query(F.data == "show_stats")
async def callback_show_stats(callback: CallbackQuery):
    """Детальная статистика"""
    db = JsonDatabase()
    all_messages = db.load_found_messages()
    
    # Статистика по каналам и ключевым словам
    channel_stats = {}
    keyword_stats = {}
    
    for msg in all_messages:
        channel_name = msg.get('channel_name', f'Channel {msg.get("channel_id", "Unknown")}')
        keywords = msg.get('found_keywords', [])
        
        channel_stats[channel_name] = channel_stats.get(channel_name, 0) + 1
        
        for kw in keywords:
            keyword_stats[kw] = keyword_stats.get(kw, 0) + 1
    
    text = "📊 <b>Детальная статистика</b>\n\n"
    
    text += "📺 <b>По каналам:</b>\n"
    for channel, count in sorted(channel_stats.items(), key=lambda x: x[1], reverse=True):
        text += f"• {channel}: {count} сообщений\n"
    
    text += f"\n🔑 <b>По ключевым словам:</b>\n"
    for keyword, count in sorted(keyword_stats.items(), key=lambda x: x[1], reverse=True):
        text += f"• {keyword}: {count} упоминаний\n"
    
    back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 К настройкам", callback_data="menu_settings")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu_refresh")]
    ])
    
    await callback.message.edit_text(text, reply_markup=back_keyboard, parse_mode="HTML")
    await callback.answer()


# ============ ОЧИСТКА БАЗЫ ============

@router.message(Command("clear"))
@admin_only
async def cmd_clear(message: Message):
    """Команда /clear"""
    await show_clear_confirm(message)


@router.callback_query(F.data == "menu_clear")
async def callback_menu_clear(callback: CallbackQuery):
    """Очистка через кнопку"""
    await show_clear_confirm(callback.message, callback)


async def show_clear_confirm(message: Message, callback: CallbackQuery = None):
    """Показать подтверждение очистки"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да, очистить", callback_data="confirm_clear"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="menu_refresh")
        ]
    ])
    
    db = JsonDatabase()
    total_messages = len(db.load_found_messages())
    
    text = (
        f"⚠️ <b>Подтверждение очистки</b>\n\n"
        f"Вы уверены, что хотите удалить все найденные сообщения?\n\n"
        f"📊 Будут удалены: <b>{total_messages}</b> сообщений\n\n"
        f"<i>⚠️ Это действие нельзя отменить!</i>"
    )
    
    if callback:
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer()
    else:
        await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data == "confirm_clear")
async def callback_confirm_clear(callback: CallbackQuery):
    """Подтверждение очистки"""
    db = JsonDatabase()
    db.clear_messages()
    
    await callback.message.edit_text(
        "✅ <b>База данных очищена!</b>\n\n"
        "Все найденные сообщения были удалены.",
        parse_mode="HTML"
    )
    await callback.answer("База очищена!")


# ============ СПРАВКА ============

@router.message(Command("help"))
@admin_only
async def cmd_help(message: Message):
    """Команда /help"""
    await show_help(message)


@router.callback_query(F.data == "menu_help")
async def callback_menu_help(callback: CallbackQuery):
    """Справка через кнопку"""
    await show_help(callback.message, callback)


async def show_help(message: Message, callback: CallbackQuery = None):
    """Показать справку"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Команды", callback_data="help_commands"),
            InlineKeyboardButton(text="🔧 Настройка", callback_data="help_setup")
        ],
        [
            InlineKeyboardButton(text="❓ FAQ", callback_data="help_faq"),
            InlineKeyboardButton(text="🐛 Проблемы", callback_data="help_troubleshooting")
        ],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu_refresh")]
    ])
    
    text = (
        "📖 <b>Справка по Stalker Bot</b>\n\n"
        "🤖 <b>Что делает бот:</b>\n"
        "• Мониторит 6 Telegram каналов\n"
        "• Ищет сообщения с ключевыми словами\n"
        "• Сохраняет находки в базу данных\n"
        "• Отправляет уведомления в реальном времени\n\n"
        "👇 <b>Выберите раздел справки:</b>"
    )
    
    if callback:
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer()
    else:
        await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data == "help_commands")
async def callback_help_commands(callback: CallbackQuery):
    """Справка по командам"""
    text = (
        "📋 <b>Все команды бота</b>\n\n"
        "🏠 <b>Основные:</b>\n"
        "• /start - Главное меню\n"
        "• /help - Справка\n\n"
        "📊 <b>Мониторинг:</b>\n"
        "• /status - Статус системы\n"
        "• /keywords - Управление ключевыми словами\n"
        "• /channels - Информация о каналах\n"
        "• /recent [N] - Последние N сообщений\n\n"
        "⚙️ <b>Управление:</b>\n"
        "• /settings - Настройки бота\n"
        "• /clear - Очистить базу данных\n\n"
        "💡 <i>Все команды также доступны через кнопки меню!</i>"
    )
    
    back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 К справке", callback_data="menu_help")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu_refresh")]
    ])
    
    await callback.message.edit_text(text, reply_markup=back_keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "help_setup")
async def callback_help_setup(callback: CallbackQuery):
    """Справка по настройке"""
    text = (
        "🔧 <b>Настройка Stalker Bot</b>\n\n"
        f"📝 <b>Файл .env должен содержать:</b>\n"
        f"• API_ID - ID Telegram API\n"
        f"• API_HASH - хеш Telegram API\n"
        f"• PHONE - номер телефона\n"
        f"• BOT_TOKEN - токен бота\n"
        f"• ADMIN_ID - ваш ID пользователя\n\n"
        f"🔗 <b>Где получить:</b>\n"
        f"• API: https://my.telegram.org/\n"
        f"• Bot Token: @BotFather\n"
        f"• User ID: @userinfobot\n\n"
        f"⚠️ <b>Важно:</b>\n"
        f"• Ваш аккаунт должен быть в отслеживаемых каналах\n"
        f"• При первом запуске нужен код подтверждения"
    )
    
    back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 К справке", callback_data="menu_help")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu_refresh")]
    ])
    
    await callback.message.edit_text(text, reply_markup=back_keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "help_faq")
async def callback_help_faq(callback: CallbackQuery):
    """FAQ"""
    text = (
        "❓ <b>Часто задаваемые вопросы</b>\n\n"
        "❓ <b>Бот не находит сообщения?</b>\n"
        "• Проверьте, что ваш аккаунт присоединен к каналам\n"
        "• Убедитесь, что мониторинг включен\n"
        "• Проверьте правильность ключевых слов\n\n"
        "❓ <b>Бот не отправляет уведомления?</b>\n"
        "• Проверьте BOT_TOKEN и ADMIN_ID\n"
        "• Убедитесь, что бот запущен\n\n"
        "❓ <b>Как добавить новые ключевые слова?</b>\n"
        "• Используйте меню 'Ключевые слова'\n"
        "• Вводите слова через запятую\n\n"
        "❓ <b>Сколько каналов отслеживается?</b>\n"
        "• В данный момент: 6 каналов\n"
        "• Список можно посмотреть в 'Каналы'"
    )
    
    back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 К справке", callback_data="menu_help")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu_refresh")]
    ])
    
    await callback.message.edit_text(text, reply_markup=back_keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "help_troubleshooting")
async def callback_help_troubleshooting(callback: CallbackQuery):
    """Решение проблем"""
    text = (
        "🐛 <b>Решение проблем</b>\n\n"
        "🔴 <b>Ошибки авторизации:</b>\n"
        "• Проверьте API_ID, API_HASH, PHONE\n"
        "• Убедитесь в правильности номера телефона\n"
        "• При первом запуске введите код из SMS\n\n"
        "🔴 <b>Канал недоступен:</b>\n"
        "• Присоединитесь к каналу вручную\n"
        "• Проверьте ID канала в настройках\n\n"
        "🔴 <b>Бот не реагирует:</b>\n"
        "• Перезапустите приложение\n"
        "• Проверьте логи в stalker_bot.log\n"
        "• Убедитесь в правильности ADMIN_ID\n\n"
        "📞 <b>Если проблема не решена:</b>\n"
        "• Проверьте файл stalker_bot.log\n"
        "• Убедитесь, что все зависимости установлены"
    )
    
    back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 К справке", callback_data="menu_help")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu_refresh")]
    ])
    
    await callback.message.edit_text(text, reply_markup=back_keyboard, parse_mode="HTML")
    await callback.answer()
