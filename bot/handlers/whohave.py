import psycopg2
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.state import State, StatesGroup
from logger_config import logger
from bot.handlers.find_user import get_connection, is_valid_email

router = Router()

def get_user_bases(email: str) -> list:
    """
    Получает список баз данных, к которым у пользователя есть доступ.

    :param email: Email пользователя.
    :return: Список словарей с ID и названиями баз данных.
    """
    conn = None
    try:
        # Устанавливаем соединение с базой данных
        conn = get_connection()  # Используем внешнюю функцию get_connection
        if not conn:
            logger.error("Не удалось подключиться к базе данных.")
            return []

        with conn.cursor() as cursor:
            # 1. Получаем ID пользователя по email
            logger.info(f"Поиск пользователя с email: {email}")
            cursor.execute("SELECT id FROM nc_users_v2 WHERE email = %s", (email,))
            user = cursor.fetchone()

            if not user:
                logger.warning(f"Пользователь с email {email} не найден.")
                return []  # Если пользователь не найден, возвращаем пустой список

            user_id = user[0]
            logger.info(f"Найден пользователь с ID: {user_id}")

            # 2. Получаем список ID баз, к которым у него есть доступ (не более 5)
            logger.info(f"Поиск баз данных для пользователя с ID: {user_id}")
            cursor.execute(
                "SELECT base_id FROM nc_base_users_v2 WHERE fk_user_id = %s LIMIT 5",
                (user_id,)
            )
            base_ids = [row[0] for row in cursor.fetchall()]

            if not base_ids:
                logger.warning(f"Для пользователя с ID {user_id} не найдено доступных баз.")
                return []  # Если нет доступных баз, возвращаем пустой список

            logger.info(f"Найдены ID баз данных: {base_ids}")

            # 3. Получаем названия этих баз
            logger.info(f"Поиск названий баз данных с ID: {base_ids}")
            cursor.execute(
                "SELECT id, title FROM nc_bases_v2 WHERE id IN %s",
                (tuple(base_ids),)  # Кортеж с одним элементом (списком base_ids)
            )
            bases = cursor.fetchall()

            logger.info(f"Найдены базы данных: {bases}")
            return [{"id": base[0], "title": base[1]} for base in bases]

    except psycopg2.Error as e:
        logger.error(f"Ошибка при выполнении запроса: {e}")
        return []
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {e}")
        return []
    finally:
        # Закрываем соединение с базой данных
        if conn:
            conn.close()
            logger.info("Соединение с базой данных закрыто.")

class WhoState(StatesGroup):
    WAITING_FOR_USER_INPUT = State()

@router.message(Command("who"))
async def find_command(message: Message, state: FSMContext):
    """Обрабатывает команду /who и запрашивает email пользователя."""
    await message.answer("Привет! Введите e-mail:")
    await state.set_state(WhoState.WAITING_FOR_USER_INPUT)
    logger.info("Состояние установлено: WAITING_FOR_USER_INPUT")

@router.message(WhoState.WAITING_FOR_USER_INPUT)
async def handle_user_input(message: Message, state: FSMContext):
    """Обрабатывает ввод email и возвращает список баз данных пользователя."""
    logger.info(f"Получен ввод: {message.text}")
    user_input = message.text.strip()

    # Проверяем корректность email
    if not is_valid_email(user_input):
        await message.answer("❌ Пожалуйста, введите корректный e-mail.")
        return

    try:
        # Получаем список баз данных пользователя
        bases = get_user_bases(user_input)

        if bases:
            # Формируем ответ с информацией о базах данных
            response = "📚 Базы данных, к которым у вас есть доступ:\n"
            for base in bases:
                response += f"- {base['title']} (ID: {base['id']})\n"
            await message.answer(response)
        else:
            await message.answer("❌ У вас нет доступа к базам данных или пользователь не найден.")

    except Exception as e:
        logger.error(f"Ошибка при получении баз данных: {e}")
        await message.answer("⚠ Произошла ошибка при обработке вашего запроса. Попробуйте позже.")

    # Сбрасываем состояние
    await state.clear()