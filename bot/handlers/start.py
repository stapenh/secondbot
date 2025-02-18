# bot/handlers/start.py
import re
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from bot.services.nocodb_client import NocodbClient
from config import NOCODB_BASE_URL, NOCODB_API_TOKEN

# Создаем роутер
router = Router()

# Определяем состояния
class ProjectState(StatesGroup):
    WAITING_FOR_PROJECT_ID = State()

def extract_project_id(text: str) -> str:
    """
    Извлекает ID проекта из ссылки NocoDB или принимает уже переданный ID.

    :param text: Введенный пользователем текст (ID или ссылка).
    :return: ID проекта или None, если не удалось извлечь.
    """
    match = re.search(r"/projects/(\d+)", text)
    if match:
        return match.group(1)  # Возвращаем только цифры ID

    if text.isdigit():  # Если введено просто число
        return text

    return None  # Если ID не найден

@router.message(Command("start"))
async def start_command(message: Message, state: FSMContext):
    """Запрашиваем у пользователя ID проекта."""
    await message.answer("Привет! Введите ID проекта или ссылку:")
    await state.set_state(ProjectState.WAITING_FOR_PROJECT_ID)

@router.message(ProjectState.WAITING_FOR_PROJECT_ID)
async def handle_project_id(message: Message, state: FSMContext):
    """Обрабатываем введенный пользователем ID или ссылку."""
    user_input = message.text.strip()  # Убираем пробелы
    project_id = extract_project_id(user_input)

    if project_id is None:
        await message.answer("Ошибка: не удалось определить ID проекта. Введите корректную ссылку или ID.")
        return

    # Создаем клиент NocoDB
    client = NocodbClient(NOCODB_BASE_URL, NOCODB_API_TOKEN)

    # Получаем информацию о пользователях проекта
    users = client.get_project_users(project_id)

    if not users:
        await message.answer(f"⚠️ Не удалось получить данные о проекте {project_id}.")
        await state.clear()
        return

    # Проверяем структуру ответа
    user_list = users.get("users", {}).get("list", [])

    if not user_list:
        await message.answer(f"🔹 В проекте {project_id} нет пользователей с доступом.")
    else:
        response = f"✅ Пользователи с доступом к проекту {project_id}:\n"
        for user in user_list:
            email = user.get("email", "Неизвестный email")
            role = user.get("main_roles", "нет роли")
            response += f"- {email} ({role})\n"

        await message.answer(response)

    # Сбрасываем состояние
    await state.clear()
