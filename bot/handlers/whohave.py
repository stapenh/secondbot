import psycopg2
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram import Router
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from logger_config import logger
from bot.handlers.find_user import get_connection, is_valid_email


router = Router()

class WhoState(StatesGroup):
    WAITING_FOR_USER_INPUT = State()

def get_user_bases(email: str) -> list:
    """Получает список баз данных, к которым у пользователя есть доступ."""
    conn = None
    try:
        conn = get_connection()
        if not conn:
            logger.error("❌ Не удалось подключиться к базе данных.")
            return []

        with conn.cursor() as cursor:
            logger.info(f"🔍 Поиск пользователя с email: {email}")
            cursor.execute("SELECT id FROM nc_users_v2 WHERE email = %s", (email,))
            user = cursor.fetchone()

            if not user:
                logger.warning(f"⚠ Пользователь {email} не найден.")
                return []

            user_id = user[0]
            logger.info(f"✅ Найден пользователь с ID: {user_id}")

            cursor.execute(
                "SELECT base_id FROM nc_base_users_v2 WHERE fk_user_id = %s AND roles = %s LIMIT 30",
                (user_id, "editor")
            )
            base_ids = [row[0] for row in cursor.fetchall()]

            if not base_ids:
                logger.warning(f"⚠ У пользователя {user_id} нет доступных баз.")
                return []

            logger.info(f"📌 Найдены базы: {base_ids}")

            query = f"SELECT id, title FROM nc_bases_v2 WHERE id IN ({','.join(['%s'] * len(base_ids))})"
            cursor.execute(query, tuple(base_ids))
            bases = cursor.fetchall()

            return [{"id": base[0], "title": base[1]} for base in bases]

    except psycopg2.Error as e:
        logger.error(f"🔥 Ошибка базы данных: {e}")
        return []
    except Exception as e:
        logger.error(f"🔥 Неожиданная ошибка: {e}")
        return []
    finally:
        if conn:
            conn.close()
            logger.info("🔌 Соединение с базой данных закрыто.")

@router.callback_query(lambda c: c.data == "who")
async def find_command(callback: CallbackQuery, state: FSMContext):
    """Обрабатывает команду /who и запрашивает email пользователя."""
    await callback.message.answer("Введите e-mail пользователя:")
    await state.set_state(WhoState.WAITING_FOR_USER_INPUT)
    logger.info("✅ Состояние установлено: WAITING_FOR_USER_INPUT")
    await callback.answer()

@router.message(WhoState.WAITING_FOR_USER_INPUT)
async def handle_user_input(message: Message, state: FSMContext):
    """Обрабатывает ввод email и возвращает список баз данных пользователя."""
    logger.info(f"📩 Получен email: {message.text}")
    user_input = message.text.strip()

    if not is_valid_email(user_input):
        await message.answer("Пожалуйста, введите корректный e-mail.")
        await state.clear()
        return

    try:
        bases = get_user_bases(user_input)

        if bases:
            response = "📚 Базы данных, к которым у пользователя есть доступ:\n"
            for base in bases:
                response += f"{base['title']} (ID: {base['id']})\n"
            await message.answer(response)
        else:
            await message.answer("⚠ У пользователя нет доступа к базам данных или он не найден.")

    except Exception as e:
        logger.error(f"🔥 Ошибка при получении баз данных: {e}")
        await message.answer("Произошла ошибка. Попробуйте позже.")

    await state.clear()
    logger.info(f"✅ Состояние FSM очищено для пользователя {message.from_user.id}.")
