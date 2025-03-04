import psycopg2
from aiogram.fsm.context import FSMContext
from aiogram import Router
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from logger_config import logger
from bot.handlers.find_user import get_connection, is_valid_email, get_user
from bot.services.find_base_id import get_base_id_by_all
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import bot.handlers.button

router = Router()

# Определяем состояния для FSM
class DeleteState(StatesGroup):
    WAITING_FOR_USER_INPUT_EMAIL = State()
    WAITING_FOR_USER_INPUT_BASE = State()


def delete_user(email: str, base_id: str) -> bool:
    """Удаляет пользователя по email и возвращает True, если удаление прошло успешно."""
    logger.info(f"🔄 Попытка удаления пользователя {email} из базы {base_id}...")

    user_data = get_user(email)
    if not user_data:
        logger.warning(f"⚠ Пользователь с email {email} не найден.")
        return False

    user_id = user_data.get('id')
    logger.info(f"✅ ID пользователя найден: {user_id}")

    conn = get_connection()
    if not conn:
        logger.error("❌ Ошибка подключения к базе данных")
        return False
    basic_id = get_base_id_by_all(base_id)
    try:
        with conn.cursor() as cursor:
            logger.info(f"🗑 Выполняем SQL-запрос на удаление пользователя {user_id} из базы {base_id}...")
            cursor.execute(
                "DELETE FROM nc_base_users_v2 WHERE fk_user_id = %s AND base_id = %s",
                (user_id, basic_id)
            )
        conn.commit()
        logger.info(f"✅ Пользователь {email} (ID: {user_id}) успешно удален из базы (ID: {basic_id})")
        return True
    except psycopg2.Error as e:
        logger.error(f"❌ Ошибка удаления из базы: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()
        logger.info("🔒 Соединение с базой данных закрыто.")


# Хендлер для обработки нажатия инлайн-кнопки
@router.callback_query(lambda c: c.data == "delete")
async def start_delete_process(callback: CallbackQuery, state: FSMContext):
    """Начинает процесс удаления пользователя по нажатию инлайн-кнопки."""
    logger.info(f"📌 Пользователь {callback.from_user.id} нажал кнопку 'Удалить пользователя'")
    await callback.message.answer("Введите e-mail пользователя, которого нужно удалить:")
    await state.set_state(DeleteState.WAITING_FOR_USER_INPUT_EMAIL)
    await callback.answer()  # Подтверждаем нажатие кнопки


# Хендлер для получения email пользователя
@router.message(DeleteState.WAITING_FOR_USER_INPUT_EMAIL)
async def process_email_input(message: Message, state: FSMContext):
    """Обрабатывает ввод email и запрашивает ID магазина."""
    email_input = message.text.strip()
    logger.info(f"📨 Получен email: '{email_input}' от пользователя {message.from_user.id}")

    if not is_valid_email(email_input):
        logger.warning(f"⚠ Некорректный email: {email_input}")
        await message.answer("Пожалуйста, введите корректный e-mail.")
        return

    user_data = get_user(email_input)
    if not user_data:
        logger.warning(f"⚠ Пользователь с email {email_input} не найден.")
        await message.answer(f"Пользователь с email {email_input} не найден.")
        await state.clear()
        return

    await state.update_data(email_input=email_input)
    logger.info(f"✅ Email пользователя {email_input} принят, запросим ID магазина")
    await message.answer("Введите ID магазина или его название:")
    await state.set_state(DeleteState.WAITING_FOR_USER_INPUT_BASE)


# Хендлер для получения ID магазина и выполнения удаления
@router.message(DeleteState.WAITING_FOR_USER_INPUT_BASE)
async def process_base_input(message: Message, state: FSMContext):
    """Обрабатывает ввод ID магазина и выполняет удаление."""
    base_input = message.text.strip()
    logger.info(f"🏢 Получен ID магазина: '{base_input}' от пользователя {message.from_user.id}")

    data = await state.get_data()
    email = data.get("email_input")
    logger.info(f"📨 Проверяем возможность удаления пользователя {email} из базы {base_input}...")

    try:
        success = delete_user(email, base_input)
        if success:
            logger.info(f"✅ Пользователь {email} успешно удален из магазина {base_input}.")
            await message.answer(f"Пользователь {email} успешно удален из магазина {base_input}.")
        else:
            logger.error(f"❌ Ошибка при удалении пользователя {email} из магазина {base_input}.")
            await message.answer(f"Ошибка при удалении пользователя {email}. Возможно, он не существует в базе.")
    except Exception as e:
        logger.error(f"⚠ Ошибка при удалении пользователя: {e}")
        await message.answer("Произошла ошибка при удалении пользователя. Попробуйте позже.")

    await state.clear()
    logger.info(f"♻ Состояние FSM очищено для пользователя {message.from_user.id}.")
