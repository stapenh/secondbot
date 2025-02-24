from typing import Optional, List, Dict
import psycopg2
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.state import State, StatesGroup
from logger_config import logger
import config
import re
from datetime import datetime, timezone
from dateutil.parser import isoparse


router = Router()

now = datetime.now(timezone.utc)


# Параметры подключения к базе данных
DB_NAME = config.DB_NAME
DB_USER = config.DB_USER
DB_PASSWORD = config.DB_PASSWORD
DB_HOST = config.DB_HOST
DB_PORT = config.DB_PORT

def get_connection():
    """Создает и возвращает соединение с базой данных."""
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        logger.info("Успешное подключение к базе данных")
        return conn
    except psycopg2.Error as e:
        logger.error(f"Ошибка подключения к базе данных: {e}")
        return None

def fetch_records(query: str, params: Optional[tuple] = None) -> List[Dict]:
    """Выполняет SQL-запрос и возвращает результат в виде списка словарей."""
    conn = get_connection()
    if not conn:
        return []

    try:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            column_names = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            records = [dict(zip(column_names, row)) for row in rows]
            logger.info(f"Успешно выполнено: {query}")
            return records
    except psycopg2.Error as e:
        logger.error(f"Ошибка выполнения запроса: {e}")
        return []
    finally:
        conn.close()

def get_user(email: str) -> Optional[Dict]:
    """Возвращает информацию о пользователе по email."""
    query = "SELECT * FROM nc_users_v2 WHERE email = %s"
    records = fetch_records(query, (email,))
    if records:
        logger.info(f"Найден пользователь: {records[0]}")
        return records[0]
    else:
        logger.info(f"Пользователь с email {email} не найден")
        return None

def is_valid_email(email: str) -> bool:
    """Проверяет, является ли email корректным."""
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(pattern, email) is not None

class UserState(StatesGroup):
    WAITING_FOR_USER_INPUT = State()

@router.message(Command("find"))
async def find_command(message: Message, state: FSMContext):
    await message.answer("Привет! Введите e-mail:")
    await state.set_state(UserState.WAITING_FOR_USER_INPUT)
    logger.info("Состояние установлено: WAITING_FOR_USER_INPUT")

@router.message(UserState.WAITING_FOR_USER_INPUT)
async def handle_user_input(message: Message, state: FSMContext):

    logger.info(f"Получен ввод: {message.text}")
    user_input = message.text.strip()

    if not is_valid_email(user_input):
        await message.answer("❌ Пожалуйста, введите корректный e-mail.")
        return

    try:
        user_data = get_user(user_input)
        time =isoparse(user_data.get('invite_token_expires'))

        if user_data:
            if time > now:
                response_text = (
                    f"✅ Найден пользователь:\n"
                    f"ID: {user_data.get('id')}\n"
                    f"Email: {user_data.get('email')}\n"
                    f"Invite Link: http://localhost:8080/dashboard/#/signup{user_data.get('invite_token')}\n"

                )
            else:
                response_text = (
                    f"✅ Найден пользователь:\n"
                    f"ID: {user_data.get('id')}\n"
                    f"Email: {user_data.get('email')}\n"
                )
        else:
            response_text = "❌ Пользователь не найден."

        await message.answer(response_text)
    except Exception as e:
        logger.error(f"Ошибка при получении пользователя: {e}")
        await message.answer("⚠ Ошибка при поиске пользователя. Попробуйте позже.")

    await state.clear()