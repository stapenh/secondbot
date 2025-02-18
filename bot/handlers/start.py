# bot/handlers/start.py
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from bot.services.nocodb_client import NocodbClient
from config import NOCODB_BASE_URL, NOCODB_API_TOKEN

router = Router()

# Определяем состояния
class ProjectState(StatesGroup):
    WAITING_FOR_PROJECT_INPUT = State()

def extract_project_id(user_input: str) -> str:
    """
    Извлекает ID проекта из ввода пользователя.
    """
    if user_input.startswith("http"):
        # Если это URL, извлекаем ID
        parts = user_input.split("/")
        return parts[-1]  # ID находится перед последним элементом
    else:
        # Если это ID, возвращаем его как есть
        return user_input

@router.message(Command("start"))
async def start_command(message: Message, state: FSMContext):
    # Запрашиваем ввод (ID или URL)
    await message.answer("Привет! Введите ID проекта или URL:")
    # Устанавливаем состояние ожидания ввода
    await state.set_state(ProjectState.WAITING_FOR_PROJECT_INPUT)

@router.message(ProjectState.WAITING_FOR_PROJECT_INPUT)
async def handle_project_input(message: Message, state: FSMContext):
    user_input = message.text

    # Извлекаем ID проекта из ввода
    try:
        project_id = extract_project_id(user_input)
    except IndexError:
        await message.answer("Некорректный ввод. Убедитесь, что вы ввели ID или URL.")
        return

    # Создаем клиент NocoDB
    client = NocodbClient(NOCODB_BASE_URL, NOCODB_API_TOKEN)

    # Получаем информацию о пользователях проекта
    users = client.get_project_users(project_id)

    if users:
        # Проверяем структуру ответа
        if "users" in users and "list" in users["users"]:
            user_list = users["users"]["list"]
            response = "Пользователи с доступом к проекту:\n"
            for user in user_list:
                response += f"- {user['email']} ({user.get('main_roles', 'нет роли')})\n"
            await message.answer(response)
        else:
            await message.answer("Некорректный формат ответа от NocoDB.")
    else:
        await message.answer("Не удалось получить информацию о пользователях.")

    # Сбрасываем состояние
    await state.clear()