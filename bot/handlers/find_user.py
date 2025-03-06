from typing import Optional, List, Dict
import psycopg2
from aiogram.fsm.context import FSMContext
from aiogram import Router
from aiogram.types import Message, CallbackQuery
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

@router.callback_query(lambda c: c.data == "find")
async def find_command(callback: CallbackQuery, state: FSMContext):
    if callback.message:
        await callback.message.answer("Введите e-mail пользователя:")
        await state.set_state(UserState.WAITING_FOR_USER_INPUT)
        logger.info("Состояние установлено: WAITING_FOR_USER_INPUT")
        return
    await callback.answer("caput.", show_alert=True)
    return

@router.message(UserState.WAITING_FOR_USER_INPUT)
async def handle_user_input(message: Message, state: FSMContext):
    logger.info(f"Получен ввод: {message.text}")
    if message.text:
        user_input = message.text.strip()
    else:
        await message.answer("Ошибка: сообщение пустое.")
        return

    if not is_valid_email(user_input):
        await message.answer("Пожалуйста, введите корректный e-mail.")
        return

    try:
        user_data = get_user(user_input)
        if user_data:
            invite_token_expires = user_data.get('invite_token_expires')
            if invite_token_expires:
                time = isoparse(invite_token_expires)
            else:
                time = None
        else:
            await message.answer("Пользователь не найден.")
            return

        if user_data:
            if time and time > now:

                response_text = (
                    f"Найден пользователь:\n"
                    f"ID: <code>{user_data.get('id')}</code>\n"
                    f"Email: <code>{user_data.get('email')}</code>\n"
                    f"Ссылка для приглашения: <code>{config.INVITE_URL}/{user_data.get('invite_token')}</code>"
                )

            else:
                response_text = (
                    f"Найден пользователь:\n"
                    f"ID: {user_data.get('id')}\n"
                    f"Email: {user_data.get('email')}\n"
                )
        else:
            response_text = "Пользователь не найден."

        await message.answer(response_text, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка при получении пользователя: {e}")
        await message.answer("Ошибка при поиске пользователя. Попробуйте позже.")

    await state.clear()