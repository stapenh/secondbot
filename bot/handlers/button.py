from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

import config
from logger_config import logger
router = Router()

# Создаём клавиатуру
admin_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text='Пользователи, имеющие доступ', callback_data='start'),
        ],
        [
            InlineKeyboardButton(text='Узнать ID пользователя', callback_data='find'),
        ],
        [
            InlineKeyboardButton(text='Предоставить доступ пользователю', callback_data='add'),
        ],
        [
            InlineKeyboardButton(text='Удалить пользователя', callback_data='delete'),
        ],
        [
            InlineKeyboardButton(text='К каким магазинам есть доступ', callback_data='who'),
        ]
    ]
)
@router.message(Command("admin"))
async def admin_command(message: types.Message):
    """Отправляет админ-клавиатуру."""

    logger.info(f"Пользователь {message.from_user.id} вызвал команду /admin")
    if message.from_user.id in config.ADMIN_IDS:

        try:
            await message.answer("Добро пожаловать в Админ-панель!", reply_markup=admin_keyboard)
            logger.info("Сообщение с админ-кнопками успешно отправлено")
        except Exception as e:
            logger.error(f"Ошибка при отправке клавиатуры админа: {e}")
    else:
        await message.answer("У вас нет доступа")

