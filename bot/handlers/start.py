from aiogram import Router, Bot
from aiogram.types import Message, CallbackQuery

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from bot.services.nocodb_client import NocodbClient
from config import NOCODB_BASE_URL, NOCODB_API_TOKEN
from logger_config import logger
from bot.services.find_base_id import extract_project_id


router = Router()

class ProjectState(StatesGroup):
    WAITING_FOR_PROJECT_INPUT = State()

@router.callback_query(lambda c: c.data == "start")
async def start_command(callback: CallbackQuery, state: FSMContext):
    """Обрабатывает команду /start и запрашивает ID проекта."""
    if callback.message:
        await callback.message.answer("Введите ID магазина или URL:")
        await state.set_state(ProjectState.WAITING_FOR_PROJECT_INPUT)
        logger.info("Состояние установлено: WAITING_FOR_PROJECT_INPUT")
        return


    await callback.answer("caput.", show_alert=True)
    return


@router.message(ProjectState.WAITING_FOR_PROJECT_INPUT)
async def handle_project_input(message: Message, state: FSMContext, bot:Bot):
    """Обрабатывает ввод ID проекта и возвращает список пользователей."""
    logger.info(f"Получен ввод: {message.text}")
    user_input = message.text

    try:
        if not user_input:
            await message.answer("Ошибка: сообщение пустое.")
            return

        project_id = extract_project_id(user_input)
        logger.info(f"Извлеченный ID проекта: {project_id}")
    except IndexError:
        await message.answer("Некорректный ввод. Убедитесь, что вы ввели ID или URL.")
        return
    except Exception as e:
        logger.error(f"Ошибка при извлечении ID проекта: {e}")
        await message.answer("Произошла ошибка при обработке вашего запроса. Попробуйте позже.")
        return

    try:
        # Запрашиваем данные о пользователях проекта
        client = NocodbClient(NOCODB_BASE_URL or "", NOCODB_API_TOKEN or "")

        users = await client.get_project_users(project_id)

        if users and "users" in users and "list" in users["users"]:
            user_list = users["users"]["list"]
            response = "Пользователи с доступом к проекту:\n"
            for user in user_list:
                email = user.get("email", "не указан")
                roles = user.get("roles", "нет роли")
                response += f"- {email} (роль: {roles})\n"
            await message.answer(response)
        else:
            await message.answer("Не удалось получить информацию о пользователях.")
            logger.error(f"Некорректный формат ответа: {users}")
    except Exception as e:
        logger.error(f"Ошибка при запросе к NocoDB: {e}")
        await message.answer("Произошла ошибка при запросе к серверу. Попробуйте позже.")

    await state.clear()