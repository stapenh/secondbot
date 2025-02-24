from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from bot.services.nocodb_client import NocodbClient
from config import NOCODB_BASE_URL, NOCODB_API_TOKEN
from logger_config import logger
from bot.handlers.find_user import is_valid_email

router = Router()

class ProjectState(StatesGroup):
    WAITING_FOR_PROJECT_INPUT = State()

def extract_project_id(user_input: str) -> str:
    """Извлекает ID проекта из URL или возвращает введенный текст как ID."""
    if user_input.startswith("http"):
        parts = user_input.split("/")
        if len(parts) >= 2:
            return parts[-2]
        else:
            raise IndexError("Некорректный URL")
    else:
        return user_input

@router.message(Command("start"))
async def start_command(message: Message, state: FSMContext):
    """Обрабатывает команду /start и запрашивает ID проекта."""
    await message.answer("Привет! Введите ID проекта или URL:")
    await state.set_state(ProjectState.WAITING_FOR_PROJECT_INPUT)
    logger.info("Состояние установлено: WAITING_FOR_PROJECT_INPUT")

@router.message(ProjectState.WAITING_FOR_PROJECT_INPUT)
async def handle_project_input(message: Message, state: FSMContext):
    """Обрабатывает ввод ID проекта и возвращает список пользователей."""
    logger.info(f"Получен ввод: {message.text}")
    user_input = message.text

    try:
        # Извлекаем ID проекта
        project_id = extract_project_id(user_input)
        logger.info(f"Извлеченный ID проекта: {project_id}")
    except IndexError:
        await message.answer("❌ Некорректный ввод. Убедитесь, что вы ввели ID или URL.")
        return
    except Exception as e:
        logger.error(f"Ошибка при извлечении ID проекта: {e}")
        await message.answer("⚠ Произошла ошибка при обработке вашего запроса. Попробуйте позже.")
        return

    try:
        # Запрашиваем данные о пользователях проекта
        client = NocodbClient(NOCODB_BASE_URL, NOCODB_API_TOKEN)
        users = await client.get_project_users(project_id)

        if users and "users" in users and "list" in users["users"]:
            user_list = users["users"]["list"]
            response = "👥 Пользователи с доступом к проекту:\n"
            for user in user_list:
                email = user.get("email", "не указан")
                roles = user.get("main_roles", "нет роли")
                response += f"- {email} (роль: {roles})\n"
            await message.answer(response)
        else:
            await message.answer("❌ Не удалось получить информацию о пользователях.")
            logger.error(f"Некорректный формат ответа: {users}")
    except Exception as e:
        logger.error(f"Ошибка при запросе к NocoDB: {e}")
        await message.answer("⚠ Произошла ошибка при запросе к серверу. Попробуйте позже.")

    await state.clear()