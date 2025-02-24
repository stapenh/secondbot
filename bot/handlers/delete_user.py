

import psycopg2
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.state import State, StatesGroup
from logger_config import logger

from bot.handlers.find_user import get_connection, is_valid_email


def delete_user(email: str) -> bool:
    """Удаляет пользователя по email и возвращает True, если удаление прошло успешно."""
    query = "DELETE FROM nc_users_v2 WHERE email = %s RETURNING id, email, invite_token"
    conn = get_connection()
    if not conn:
        return False

    try:
        with conn.cursor() as cursor:
            cursor.execute(query, (email,))
            deleted_user = cursor.fetchone()
            if deleted_user:
                conn.commit()
                logger.info(f"Пользователь удален: {deleted_user}")
                return True
            else:
                logger.info(f"Пользователь с email {email} не найден для удаления")
                return False
    except psycopg2.Error as e:
        logger.error(f"Ошибка при удалении пользователя: {e}")
        return False
    finally:
        conn.close()

router = Router()
class DeleteState(StatesGroup):
    WAITING_FOR_USER_INPUT = State()



@router.message(Command("delete"))
async def find_command(message: Message, state: FSMContext):
    await message.answer("Привет! Введите e-mail, который будет удален:")
    await state.set_state(DeleteState.WAITING_FOR_USER_INPUT)
    logger.info("Состояние установлено: WAITING_FOR_USER_INPUT")

@router.message(DeleteState.WAITING_FOR_USER_INPUT)
async def handle_user_input(message: Message, state: FSMContext):

    logger.info(f"Получен ввод: {message.text}")
    user_input = message.text.strip()

    if not is_valid_email(user_input):
        await message.answer("❌ Пожалуйста, введите корректный e-mail.")
        return

    try:
        user_data = delete_user(user_input)


        if user_data:
            response_text = (
                f"✅Пользователь удален"
            )
        else:
            response_text = "❌ Пользователь не найден."
    except Exception as e:
        logger.error(f"Ошибка при получении пользователя: {e}")
        await message.answer("⚠ Ошибка при удалении пользователя. Попробуйте позже.")

    await state.clear()