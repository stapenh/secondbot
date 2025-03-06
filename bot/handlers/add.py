from __future__ import annotations

import psycopg2
from aiogram.fsm.context import FSMContext
from aiogram import Router
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from logger_config import logger
from bot.handlers.find_user import get_connection, get_user, is_valid_email
from aiogram.filters import Command
from bot.services.find_base_id import get_base_id_by_all

router = Router()

# Определяем состояния для FSM
class AddUserState(StatesGroup):
    waiting_for_base = State()
    waiting_for_user_id = State()

# Функция для добавления пользователя в базу
def assign_user_to_base(base_id: str, email: str) -> bool:
    """Добавляет пользователя в базу и возвращает True, если операция успешна."""
    logger.info(f"Попытка добавить пользователя {email} в базу {base_id}")

    conn = get_connection()
    if not conn:
        logger.error("Ошибка подключения к базе данных")
        return False

    # Получаем ID пользователя по email
    user_data = get_user(email)
    if not user_data:
        logger.warning(f"Пользователь с email {email} не найден.")
        return False

    user_id = user_data.get("id")
    if not user_id:
        logger.error(f"Ошибка: у пользователя {email} отсутствует ID.")
        return False

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM nc_base_users_v2 WHERE base_id = %s AND fk_user_id = %s",
                (base_id, user_id)
            )
            exists = cursor.fetchone()
            if exists:
                logger.warning(f"Пользователь {email} уже имеет доступ к базе {base_id}.")
                return False  # Уже есть доступ, не добавляем повторно

            # Добавляем пользователя в базу
            cursor.execute(
                "INSERT INTO nc_base_users_v2 (base_id, fk_user_id, roles) VALUES (%s, %s, 'editor')",
                (base_id, user_id)
            )
        conn.commit()
        logger.info(f"✅ Пользователь {email} добавлен в базу (ID: {base_id})")
        return True
    except psycopg2.Error as e:
        logger.error(f"Ошибка при добавлении пользователя: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()
        logger.info("Соединение с базой данных закрыто.")

# Хендлер callback-кнопки "add"
@router.callback_query(lambda c: c.data == "add")
async def cmd_add(callback: CallbackQuery, state: FSMContext):
    """Начинает процесс добавления пользователя в базу."""
    logger.info(f"Пользователь {callback.from_user.id} начал процесс добавления.")
    if callback.message:

        await callback.message.answer("Введите название магазина:")
        await state.set_state(AddUserState.waiting_for_base)
        return
    await callback.answer("caput.", show_alert=True)
    return

# Хендлер получения названия базы
@router.message(AddUserState.waiting_for_base)
async def process_base_name(message: Message, state: FSMContext):
    """Проверяет, существует ли база, и запрашивает email пользователя."""
    if message.text:
        base_title = message.text.strip()
    else:
        await message.answer("pusto")
        return
    if message.from_user:
        logger.info(f"Получено название базы: '{base_title}' от пользователя {message.from_user.id}")
    else:
        logger.info(f"📨Получено название базы: '{base_title}' от неизвестного пользователя")

    try:
        base_id = get_base_id_by_all(base_title)
        if base_id:
            logger.info(f"База найдена: {base_id}")
            await message.answer("Магазин найден! Теперь введите e-mail пользователя:")
            await state.update_data(base_id=base_id)
            await state.set_state(AddUserState.waiting_for_user_id)
        else:
            await message.answer("База данных не найдена.")
            await state.clear()
    except Exception as e:
        logger.error(f"Ошибка при поиске базы: {e}")
        await message.answer("Произошла ошибка. Попробуйте позже.")
        await state.clear()

# Хендлер получения email пользователя и добавления в базу
@router.message(AddUserState.waiting_for_user_id)
async def process_user_id(message: Message, state: FSMContext):
    """Добавляет пользователя в найденную базу."""
    if message.text:
        email = message.text.strip()
    else:
        await message.answer("pusto")
        return
    if message.from_user:
        logger.info(f"Получен e-mail пользователя: '{email}' от {message.from_user.id}")
    else:
        logger.info(f"Получен e-mail пользователя: '{email}' от unknown user")

    if not is_valid_email(email):
        await message.answer("Введите корректный e-mail.")
        return

    # Получаем сохранённые данные (ID базы)
    data = await state.get_data()
    base_id = data.get("base_id")

    if not base_id:
        if message.from_user:

            logger.error(f"Ошибка: base_id не найден в state для пользователя {message.from_user.id}")
        else:
            logger.error(f"Ошибка: base_id не найден в state для unknown")

        await message.answer("Ошибка! Попробуйте снова.")
        await state.clear()
        return

    logger.info(f"Добавление пользователя {email} в базу с ID {base_id}")


    # Выполняем SQL-зап
    success = assign_user_to_base(base_id, email)

    if success:
        logger.info(f"✅ Пользователь {email} успешно добавлен в базу {base_id}.")
        await message.answer(f"Пользователь {email} успешно добавлен в базу!")
    else:
        logger.error(f"❌ Ошибка при добавлении пользователя {email} в базу {base_id}.")
        await message.answer(
            f"Ошибка при добавлении пользователя {email}. Возможно, у него уже есть доступ или произошла внутренняя ошибка.")

    # Очищаем состояние FSM
    await state.clear()
    if message.from_user:
        logger.info(f"Состояние FSM очищено для пользователя {message.from_user.id}.")