# bot/handlers/start.py
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from bot.services.nocodb_client import NocodbClient
from config import NOCODB_BASE_URL, NOCODB_API_TOKEN
import logging

logger = logging.getLogger(__name__)

router = Router()

class ProjectState(StatesGroup):
    WAITING_FOR_PROJECT_INPUT = State()

def extract_project_id(user_input: str) -> str:
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
    await message.answer("Привет! Введите ID проекта или URL:")
    await state.set_state(ProjectState.WAITING_FOR_PROJECT_INPUT)
    logger.info("Состояние установлено: WAITING_FOR_PROJECT_INPUT")

@router.message(ProjectState.WAITING_FOR_PROJECT_INPUT)
async def handle_project_input(message: Message, state: FSMContext):
    logger.info(f"Получен ввод: {message.text}")
    user_input = message.text
    try:
        project_id = extract_project_id(user_input)
        logger.info(f"Извлеченный ID проекта: {project_id}")
    except IndexError:
        await message.answer("Некорректный ввод. Убедитесь, что вы ввели ID или URL.")
        return

    client = NocodbClient(NOCODB_BASE_URL, NOCODB_API_TOKEN)
    users = await client.get_project_users(project_id)

    if users:
        if "users" in users and "list" in users["users"]:
            user_list = users["users"]["list"]
            response = "Пользователи с доступом к проекту:\n"
            for user in user_list:
                response += f"- {user['email']} ({user.get('main_roles', 'нет роли')})\n"
            await message.answer(response)
        else:
            await message.answer("Некорректный формат ответа от NocoDB.")
            logger.error(f"Некорректный формат ответа: {users}")
    else:
        await message.answer("Не удалось получить информацию о пользователях.")

    await state.clear()