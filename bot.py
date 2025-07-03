import asyncio
import logging
import json
import sqlite3
from datetime import datetime
from typing import Optional, Dict, List
import os
import sys

import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

# ============================================================================
# 🚀 AI TELEGRAM BOT v3.0 by Закиржанов Жавахир
# ============================================================================

# ВАШИ НАСТРОЙКИ - УЖЕ НАСТРОЕНО!
BOT_TOKEN = "8179782484:AAEMeUjxA9IrCuFaddgiwgjZORZ_RWU7Rk0"
ADMIN_ID = 1395804259
AI_API_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "llama3:latest"

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ============================================================================
# 📊 БАЗА ДАННЫХ
# ============================================================================

def init_database():
    """Инициализация базы данных"""
    conn = sqlite3.connect('ai_bot.db')
    cursor = conn.cursor()
    
    # Таблица пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            message_count INTEGER DEFAULT 0,
            is_banned INTEGER DEFAULT 0
        )
    ''')
    
    # Таблица сообщений
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            message_text TEXT,
            ai_response TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            model_used TEXT,
            response_time REAL
        )
    ''')
    
    # Таблица ролей пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_roles (
            user_id INTEGER PRIMARY KEY,
            role_name TEXT,
            role_description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("База данных инициализирована")

# Инициализируем БД при запуске
init_database()

# ============================================================================
# 👤 ПОЛЬЗОВАТЕЛЬСКИЕ СЕССИИ
# ============================================================================

user_sessions = {}

class UserSession:
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.model = DEFAULT_MODEL
        self.history = []
        self.role = None
        self.role_description = ""
        self.load_role()
    
    def reset_history(self):
        self.history = []
        logger.info(f"История пользователя {self.user_id} сброшена")
    
    def set_role(self, role_name: str, description: str):
        self.role = role_name
        self.role_description = description
        self.save_role()
    
    def save_role(self):
        conn = sqlite3.connect('ai_bot.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO user_roles (user_id, role_name, role_description)
            VALUES (?, ?, ?)
        ''', (self.user_id, self.role, self.role_description))
        conn.commit()
        conn.close()
    
    def load_role(self):
        conn = sqlite3.connect('ai_bot.db')
        cursor = conn.cursor()
        cursor.execute('SELECT role_name, role_description FROM user_roles WHERE user_id = ?', (self.user_id,))
        result = cursor.fetchone()
        if result:
            self.role, self.role_description = result
        conn.close()

# ============================================================================
# 💾 ФУНКЦИИ БАЗЫ ДАННЫХ
# ============================================================================

def save_user_info(user: types.User):
    """Сохранение информации о пользователе"""
    conn = sqlite3.connect('ai_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO users (user_id, username, first_name, last_name, last_activity)
        VALUES (?, ?, ?, ?, ?)
    ''', (user.id, user.username, user.first_name, user.last_name, datetime.now()))
    conn.commit()
    conn.close()

def save_message(user_id: int, message: str, ai_response: str, model: str, response_time: float):
    """Сохранение сообщения и ответа"""
    conn = sqlite3.connect('ai_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO messages (user_id, message_text, ai_response, model_used, response_time)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, message, ai_response, model, response_time))
    
    cursor.execute('''
        UPDATE users SET message_count = message_count + 1, last_activity = ?
        WHERE user_id = ?
    ''', (datetime.now(), user_id))
    
    conn.commit()
    conn.close()

def get_user_stats(user_id: int) -> dict:
    """Получение статистики пользователя"""
    conn = sqlite3.connect('ai_bot.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT join_date, message_count, last_activity 
        FROM users WHERE user_id = ?
    ''', (user_id,))
    user_data = cursor.fetchone()
    
    if not user_data:
        conn.close()
        return None
    
    cursor.execute('''
        SELECT COUNT(*) FROM messages 
        WHERE user_id = ? AND timestamp > datetime('now', '-7 days')
    ''', (user_id,))
    week_messages = cursor.fetchone()[0]
    
    cursor.execute('''
        SELECT AVG(response_time) FROM messages 
        WHERE user_id = ? AND response_time IS NOT NULL
    ''', (user_id,))
    avg_response = cursor.fetchone()[0] or 0
    
    conn.close()
    
    return {
        'join_date': user_data[0],
        'message_count': user_data[1],
        'last_activity': user_data[2],
        'week_messages': week_messages,
        'avg_response_time': round(avg_response, 2)
    }

# ============================================================================
# ⌨️ КЛАВИАТУРЫ
# ============================================================================

def get_main_keyboard(is_admin: bool = False) -> ReplyKeyboardMarkup:
    """Основная клавиатура"""
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="🧠 Задать вопрос"),
        KeyboardButton(text="🎭 Установить роль")
    )
    builder.row(
        KeyboardButton(text="🔄 Сбросить диалог"),
        KeyboardButton(text="📊 Моя статистика")
    )
    builder.row(
        KeyboardButton(text="ℹ️ О боте"),
        KeyboardButton(text="🔧 Настройки")
    )
    
    if is_admin:
        builder.row(KeyboardButton(text="👑 АДМИНКА"))
    
    return builder.as_markup(resize_keyboard=True)

def get_admin_keyboard() -> ReplyKeyboardMarkup:
    """Админская клавиатура"""
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="👥 Статистика пользователей"),
        KeyboardButton(text="📈 Общая статистика")
    )
    builder.row(
        KeyboardButton(text="📝 Логи системы"),
        KeyboardButton(text="🔄 Перезапуск бота")
    )
    builder.row(
        KeyboardButton(text="🔙 Обычное меню")
    )
    return builder.as_markup(resize_keyboard=True)

def get_role_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для выбора ролей"""
    builder = InlineKeyboardBuilder()
    
    roles = [
        ("🤖 Программист", "prog"),
        ("📚 Учитель", "teach"),
        ("😈 Токсик", "toxic"),
        ("🎭 Актер", "actor"),
        ("💼 Бизнес-гуру", "biz"),
        ("🧙‍♂️ Мудрец", "wise"),
        ("🔥 Мотиватор", "motiv"),
        ("🚫 Сбросить роль", "reset")
    ]
    
    for role_name, role_code in roles:
        builder.row(InlineKeyboardButton(text=role_name, callback_data=f"role_{role_code}"))
    
    return builder.as_markup()

# ============================================================================
# 🎭 РОЛИ ДЛЯ ИИ
# ============================================================================

ROLE_DESCRIPTIONS = {
    "prog": ("Программист", "Ты опытный программист. Отвечай кратко и по делу. Если нужен код - пиши минимальный рабочий пример. Используй современные подходы."),
    "teach": ("Учитель", "Ты терпеливый учитель. Объясняй просто и кратко. Используй примеры и аналогии."),
    "toxic": ("Токсик", "Ты токсичный чувак. Можешь материться и быть резким. Отвечай коротко и с сарказмом. Но помогай по делу."),
    "actor": ("Актер", "Ты талантливый актер. Играй роли, вживайся в персонажей, но отвечай кратко."),
    "biz": ("Бизнес-гуру", "Ты бизнес-эксперт. Давай практические советы кратко. Фокусируйся на результате."),
    "wise": ("Мудрец", "Ты древний мудрец. Давай мудрые советы, но кратко. Используй притчи и метафоры."),
    "motiv": ("Мотиватор", "Ты энергичный мотиватор. Мотивируй и вдохновляй, но кратко. Используй эмоции!")
}

# ============================================================================
# 🧠 ИИ ФУНКЦИИ
# ============================================================================

def is_complex_request(prompt: str) -> bool:
    """Определяет сложный ли запрос"""
    complex_keywords = [
        "создай", "напиши код", "программа", "игра", "приложение", 
        "сайт", "алгоритм", "функция", "класс", "скрипт", "бот",
        "разработай", "построй", "сделай приложение"
    ]
    return any(keyword in prompt.lower() for keyword in complex_keywords)

async def send_to_ai(prompt: str, model: str = DEFAULT_MODEL, role_context: str = "") -> tuple[Optional[str], float]:
    """Оптимизированный запрос к ИИ с измерением времени"""
    start_time = datetime.now()
    
    try:
        is_complex = is_complex_request(prompt)
        
        # Подготавливаем промпт
        full_prompt = prompt
        if role_context:
            full_prompt = f"{role_context}\n\nПользователь: {prompt}"
        
        # Настройки в зависимости от сложности
        if is_complex:
            full_prompt += "\n\nОТВЕЧАЙ КРАТКО! Максимум 300 слов. Если код - только основная часть с комментариями."
            options = {
                "temperature": 0.3,
                "top_p": 0.8,
                "top_k": 20,
                "num_predict": 400,
                "repeat_penalty": 1.1
            }
            timeout = 120
        else:
            full_prompt += "\n\nОТВЕЧАЙ КРАТКО! Максимум 150 слов."
            options = {
                "temperature": 0.7,
                "top_p": 0.9,
                "top_k": 40,
                "num_predict": 200,
                "repeat_penalty": 1.1
            }
            timeout = 45
        
        payload = {
            "model": model,
            "prompt": full_prompt,
            "stream": False,
            "options": options
        }
        
        logger.info(f"Отправка {'сложного' if is_complex else 'простого'} запроса: {prompt[:50]}...")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                AI_API_URL, 
                json=payload,
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    ai_response = result.get("response", "Пустой ответ")
                    
                    # Вычисляем время ответа
                    response_time = (datetime.now() - start_time).total_seconds()
                    
                    logger.info(f"Получен ответ длиной {len(ai_response)} символов за {response_time:.2f}с")
                    return ai_response, response_time
                else:
                    logger.error(f"ИИ вернул статус {response.status}")
                    return None, 0
                    
    except asyncio.TimeoutError:
        response_time = (datetime.now() - start_time).total_seconds()
        logger.error(f"Таймаут запроса к ИИ ({timeout}с)")
        
        if is_complex_request(prompt):
            return (
                "⏰ <b>Слишком сложный запрос!</b>\n\n"
                "🔥 Попробуй:\n"
                "• Упрости вопрос\n"
                "• Раздели на части\n"
                "• Спроси конкретнее\n\n"
                "💡 Например: 'Покажи основу игры змейка' вместо 'Создай полную игру'"
            ), response_time
        else:
            return "⏰ Долго думаю, попробуй проще спросить", response_time
            
    except Exception as e:
        response_time = (datetime.now() - start_time).total_seconds()
        logger.error(f"Ошибка запроса к ИИ: {e}")
        return None, response_time

# ============================================================================
# 🔧 УТИЛИТЫ
# ============================================================================

def get_user_session(user_id: int) -> UserSession:
    """Получение сессии пользователя"""
    if user_id not in user_sessions:
        user_sessions[user_id] = UserSession(user_id)
        logger.info(f"Создана сессия для пользователя {user_id}")
    return user_sessions[user_id]

def is_admin(user_id: int) -> bool:
    """Проверка админских прав"""
    return user_id == ADMIN_ID

def format_time_ago(timestamp_str: str) -> str:
    """Форматирование времени 'назад'"""
    try:
        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        now = datetime.now()
        diff = now - timestamp
        
        if diff.days > 0:
            return f"{diff.days} дн. назад"
        elif diff.seconds > 3600:
            return f"{diff.seconds // 3600} ч. назад"
        elif diff.seconds > 60:
            return f"{diff.seconds // 60} мин. назад"
        else:
            return "только что"
    except:
        return "недавно"

# ============================================================================
# 📨 ОБРАБОТЧИКИ КОМАНД
# ============================================================================

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    """Обработчик команды /start"""
    save_user_info(message.from_user)
    user_session = get_user_session(message.from_user.id)
    
    admin_status = ""
    if is_admin(message.from_user.id):
        admin_status = "\n👑 <b>АДМИН РЕЖИМ АКТИВЕН</b>\n"
    
    welcome_text = (
        "🔥 <b>Добро пожаловать в ИИ-бота от Закиржанова Жавахира!</b>\n\n"
        "🧠 Я — продвинутый искусственный интеллект v3.0\n"
        "💪 Могу помочь с любыми вопросами, писать код, объяснять темы\n"
        "🎭 Умею играть разные роли и адаптироваться под твой стиль\n"
        "⚡ Оптимизирован для быстрых ответов\n"
        f"{admin_status}"
        "🚀 <b>Выбери действие из меню или просто напиши свой вопрос!</b>\n\n"
        "💡 <b>Совет:</b> Чем конкретнее вопрос, тем быстрее и точнее ответ!"
    )
    
    await message.answer(
        welcome_text,
        reply_markup=get_main_keyboard(is_admin(message.from_user.id)),
        parse_mode="HTML"
    )
    
    logger.info(f"Пользователь {message.from_user.id} ({message.from_user.username}) запустил бота")

@dp.message(lambda message: message.text == "🧠 Задать вопрос")
async def ask_question_handler(message: types.Message):
    """Обработчик кнопки 'Задать вопрос'"""
    user_session = get_user_session(message.from_user.id)
    role_info = f"\n🎭 <b>Активная роль:</b> {user_session.role}" if user_session.role else ""
    
    await message.answer(
        f"🧠 <b>Задай мне любой вопрос!</b>\n\n"
        "⚡ <b>Быстрые примеры:</b>\n"
        "• Что такое Python?\n"
        "• Как работает цикл for?\n"
        "• Покажи пример функции\n"
        "• Объясни переменные\n\n"
        "🐌 <b>Медленные примеры:</b>\n"
        "• Создай полную игру\n"
        "• Напиши большое приложение\n"
        "• Сделай сложный алгоритм{role_info}\n\n"
        "💡 <b>Совет:</b> Чем конкретнее вопрос, тем быстрее ответ!",
        parse_mode="HTML"
    )

@dp.message(lambda message: message.text == "🎭 Установить роль")
async def set_role_handler(message: types.Message):
    """Обработчик кнопки 'Установить роль'"""
    user_session = get_user_session(message.from_user.id)
    current_role = f"\n🎭 <b>Текущая роль:</b> {user_session.role}" if user_session.role else ""
    
    await message.answer(
        f"🎭 <b>Выбери роль для ИИ</b>\n\n"
        "🔥 Роли кардинально меняют стиль общения и поведение ИИ{current_role}\n\n"
        "👇 <b>Выбери роль из списка:</b>",
        reply_markup=get_role_keyboard(),
        parse_mode="HTML"
    )

@dp.callback_query(lambda c: c.data.startswith("role_"))
async def role_callback_handler(callback: types.CallbackQuery):
    """Обработчик выбора роли"""
    user_session = get_user_session(callback.from_user.id)
    
    role_code = callback.data.replace("role_", "")
    
    if role_code == "reset":
        user_session.role = None
        user_session.role_description = ""
        
        # Удаляем из БД
        conn = sqlite3.connect('ai_bot.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM user_roles WHERE user_id = ?', (callback.from_user.id,))
        conn.commit()
        conn.close()
        
        await callback.message.edit_text(
            "✅ <b>Роль сброшена!</b>\n\n"
            "🤖 Теперь я буду общаться в обычном режиме",
            parse_mode="HTML"
        )
    else:
        if role_code in ROLE_DESCRIPTIONS:
            role_name, role_description = ROLE_DESCRIPTIONS[role_code]
            user_session.set_role(role_name, role_description)
            
            await callback.message.edit_text(
                f"✅ <b>Роль установлена!</b>\n\n"
                f"🎭 <b>Новая роль:</b> {role_name}\n"
                f"📝 <b>Стиль:</b> {role_description}\n\n"
                "🚀 Теперь я буду общаться в этой роли!",
                parse_mode="HTML"
            )
    
    await callback.answer()

@dp.message(lambda message: message.text == "📊 Моя статистика")
async def my_stats_handler(message: types.Message):
    """Обработчик кнопки 'Моя статистика'"""
    stats = get_user_stats(message.from_user.id)
    
    if stats:
        stats_text = (
            f"📊 <b>Твоя статистика</b>\n\n"
            f"👤 <b>Пользователь:</b> {message.from_user.first_name}\n"
            f"📅 <b>Дата регистрации:</b> {stats['join_date'][:10]}\n"
            f"💬 <b>Всего сообщений:</b> {stats['message_count']}\n"
            f"📈 <b>За последнюю неделю:</b> {stats['week_messages']}\n"
            f"⚡ <b>Среднее время ответа:</b> {stats['avg_response_time']}с\n"
            f"🕐 <b>Последняя активность:</b> {format_time_ago(stats['last_activity'])}\n\n"
            "🔥 <b>Продолжай общаться!</b>"
        )
    else:
        stats_text = "❌ Статистика не найдена"
    
    await message.answer(stats_text, parse_mode="HTML")

@dp.message(lambda message: message.text == "🔄 Сбросить диалог")
async def reset_dialog_handler(message: types.Message):
    """Обработчик кнопки 'Сбросить диалог'"""
    user_session = get_user_session(message.from_user.id)
    user_session.reset_history()
    
    await message.answer(
        "🔄 <b>История диалога сброшена!</b>\n"
        "🆕 Можешь начинать новый разговор",
        parse_mode="HTML"
    )

@dp.message(lambda message: message.text == "ℹ️ О боте")
async def about_handler(message: types.Message):
    """Обработчик кнопки 'О боте'"""
    about_text = (
        "🤖 <b>ИИ-бот от Закиржанова Жавахира</b>\n\n"
        "🧠 <b>Возможности:</b>\n"
        "• Ответы на любые вопросы\n"
        "• Помощь с программированием\n"
        "• Объяснение сложных тем\n"
        "• Творческие задачи\n"
        "• Разные роли и стили общения\n"
        "• Без цензуры и ограничений\n\n"
        "🎭 <b>Роли:</b> Программист, Учитель, Токсик, Актер и другие\n"
        "💪 <b>Особенности:</b> Может материться, быть токсичным или мотивирующим\n\n"
        "⚡ <b>Оптимизация v3.0:</b>\n"
        "• Быстрые ответы на простые вопросы (до 45с)\n"
        "• Умная обработка сложных запросов (до 2 мин)\n"
        "• Автоматическое определение сложности\n"
        "• Улучшенная база данных\n\n"
        "🔥 <b>Создатель:</b> Закиржанов Жавахир\n"
        "⚡ <b>Версия:</b> 3.0 MEGA\n"
        "🖥️ <b>Система:</b> Ubuntu 22.04 | 8 CPU | 12GB RAM"
    )
    
    await message.answer(about_text, parse_mode="HTML")

# ============================================================================
# 👑 АДМИНСКИЕ КОМАНДЫ
# ============================================================================

@dp.message(lambda message: message.text == "👑 АДМИНКА" and is_admin(message.from_user.id))
async def admin_panel_handler(message: types.Message):
    """Админская панель"""
    await message.answer(
        "👑 <b>АДМИНСКАЯ ПАНЕЛЬ v3.0</b>\n\n"
        "🔥 Добро пожаловать в админку, босс!\n"
        "Выбери действие из меню:",
        reply_markup=get_admin_keyboard(),
        parse_mode="HTML"
    )

@dp.message(lambda message: message.text == "👥 Статистика пользователей" and is_admin(message.from_user.id))
async def users_stats_handler(message: types.Message):
    """Статистика пользователей для админа"""
    conn = sqlite3.connect('ai_bot.db')
    cursor = conn.cursor()
    
    # Общая статистика
    cursor.execute('SELECT COUNT(*) FROM users')
    total_users = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM users WHERE last_activity > datetime("now", "-1 day")')
    active_today = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM messages')
    total_messages = cursor.fetchone()[0]
    
    cursor.execute('SELECT AVG(response_time) FROM messages WHERE response_time IS NOT NULL')
    avg_response = cursor.fetchone()[0] or 0
    
    # Топ пользователей
    cursor.execute('''
        SELECT username, first_name, message_count 
        FROM users ORDER BY message_count DESC LIMIT 5
    ''')
    top_users = cursor.fetchall()
    
    stats_text = (
        f"👥 <b>АДМИН: Статистика пользователей</b>\n\n"
        f"👤 <b>Всего пользователей:</b> {total_users}\n"
        f"🟢 <b>Активных сегодня:</b> {active_today}\n"
        f"💬 <b>Всего сообщений:</b> {total_messages}\n"
        f"⚡ <b>Среднее время ответа:</b> {avg_response:.2f}с\n\n"
        f"🏆 <b>Топ пользователей:</b>\n"
    )
    
    for i, (username, first_name, msg_count) in enumerate(top_users, 1):
        name = username or first_name or "Неизвестный"
        stats_text += f"{i}. @{name} - {msg_count} сообщений\n"
    
    conn.close()
    await message.answer(stats_text, parse_mode="HTML")

@dp.message(lambda message: message.text == "📝 Логи системы" and is_admin(message.from_user.id))
async def logs_handler(message: types.Message):
    """Просмотр логов для админа"""
    try:
        with open('bot.log', 'r', encoding='utf-8') as f:
            logs = f.readlines()
        
        # Берем последние 20 строк
        recent_logs = ''.join(logs[-20:])
        
        if len(recent_logs) > 4000:
            recent_logs = recent_logs[-4000:]
        
        await message.answer(
            f"📝 <b>Последние логи системы:</b>\n\n"
            f"<code>{recent_logs}</code>",
            parse_mode="HTML"
        )
    except Exception as e:
        await message.answer(f"❌ Ошибка чтения логов: {e}")

@dp.message(lambda message: message.text == "🔙 Обычное меню" and is_admin(message.from_user.id))
async def back_to_normal_handler(message: types.Message):
    """Возврат к обычному меню"""
    await message.answer(
        "🔙 <b>Переключение на обычное меню</b>",
        reply_markup=get_main_keyboard(True),
        parse_mode="HTML"
    )

# ============================================================================
# 💬 ОСНОВНОЙ ОБРАБОТЧИК СООБЩЕНИЙ - ИСПРАВЛЕННАЯ ВЕРСИЯ!
# ============================================================================

@dp.message()
async def text_handler(message: types.Message):
    """Главный обработчик текстовых сообщений - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
    save_user_info(message.from_user)
    user_session = get_user_session(message.from_user.id)
    
    # Определяем сложность запроса
    is_complex = is_complex_request(message.text)
    
    # Показываем что бот печатает
    await bot.send_chat_action(message.chat.id, "typing")
    
    # Разные сообщения для разных типов запросов
    if is_complex:
        processing_text = (
            "🧠 <b>Думаю над сложным запросом...</b>\n"
            f"{'🎭 Роль: ' + user_session.role if user_session.role else '🤖 Обычный режим'}\n"
            "⏳ <i>Это может занять до 2 минут...</i>\n"
            "💡 <i>В следующий раз попробуй разбить на части</i>"
        )
    else:
        processing_text = (
            "🧠 <b>Быстро думаю...</b>\n"
            f"{'🎭 Роль: ' + user_session.role if user_session.role else '🤖 Обычный режим'}\n"
            "⚡ <i>Секундочку...</i>"
        )
    
    processing_msg = await message.answer(processing_text, parse_mode="HTML")
    
    # Отправляем запрос к ИИ
    role_context = user_session.role_description if user_session.role else ""
    response, response_time = await send_to_ai(message.text, user_session.model, role_context)
    
    # Удаляем сообщение о обработке
    try:
        await processing_msg.delete()
    except:
        pass
    
    if response:
        # Сохраняем в БД
        save_message(message.from_user.id, message.text, response, user_session.model, response_time)
        
        # Отправляем ответ
        role_emoji = "🎭" if user_session.role else "🤖"
        speed_emoji = "⚡" if not is_complex else "🐌"
        time_info = f" ({response_time:.1f}с)" if response_time > 0 else ""
        response_header = f"{role_emoji}{speed_emoji} <b>Ответ{time_info}:</b>\n\n"
        
        # 🔥 ИСПРАВЛЕННАЯ ЧАСТЬ - РАЗБИВКА ДЛИННЫХ СООБЩЕНИЙ
        max_length = 4096 - len(response_header) - 100  # Оставляем запас
        
        if len(response) > max_length:
            # Отправляем заголовок отдельно
            await message.answer(response_header, parse_mode="HTML")
            
            # Разбиваем ответ на части по 4000 символов
            for i in range(0, len(response), 4000):
                chunk = response[i:i+4000]
                
                # Если в куске есть код (содержит ``` или много пробелов)
                if "```" in chunk or chunk.count("    ") > 5:
                    await message.answer(f"```\n{chunk}\n```", parse_mode="Markdown")
                else:
                    await message.answer(chunk)
                
                # Небольшая задержка между частями
                await asyncio.sleep(0.1)
        else:
            # Короткий ответ - отправляем целиком
            full_response = f"{response_header}{response}"
            await message.answer(full_response, parse_mode="HTML")
        
        logger.info(f"Обработан {'сложный' if is_complex else 'простой'} запрос пользователя {message.from_user.id} за {response_time:.2f}с")
        
    else:
        await message.answer(
            "❌ <b>Не смог обработать запрос</b>\n\n"
            "🔄 <b>Попробуй:</b>\n"
            "• Переформулировать вопрос\n"
            "• Задать проще\n"
            "• Разбить на части\n"
            "• Попробовать позже\n\n"
            "🔧 Если проблема повторяется - сообщи админу",
            parse_mode="HTML"
        )

# ============================================================================
# 🚀 ЗАПУСК БОТА
# ============================================================================

async def main():
    """Главная функция запуска"""
    logger.info("🚀 Запуск MEGA ИИ-бота v3.0 от Закиржанова Жавахира...")
    logger.info(f"👑 Админ ID: {ADMIN_ID}")
    logger.info(f"🤖 Модель: {DEFAULT_MODEL}")
    logger.info(f"🌐 API URL: {AI_API_URL}")
    
    try:
        # Проверяем подключение к Ollama
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:11434/api/tags") as response:
                if response.status == 200:
                    logger.info("✅ Ollama работает")
                else:
                    logger.error("❌ Ошибка подключения к Ollama")
        
        logger.info("🤖 Бот запущен и готов к работе!")
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"❌ Ошибка запуска: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
