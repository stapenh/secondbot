from __future__ import annotations
import psycopg2
from logger_config import logger
from bot.handlers.find_user import get_connection


def extract_project_id(user_input: str) -> str:
    """Извлекает ID проекта из URL или возвращает введенный текст как есть."""
    if user_input.startswith("http"):
        parts = user_input.split("/")
        if len(parts) >= 2:
            return parts[-1]  # Извлекаем ID из URL
        else:
            raise ValueError("Некорректный URL: невозможно извлечь ID.")
    else:
        return user_input  # Если это не URL, возвращаем как есть


def get_base_id_by_all(base_input: str) -> str | None:
    try:
        # Если это URL, вынимаем ID
        base_id_or_title = extract_project_id(base_input)
        logger.info(f"Обрабатываем ввод: '{base_input}' -> Извлечено: '{base_id_or_title}'")

        conn = get_connection()
        if not conn:
            logger.error("Ошибка подключения к базе данных")
            return None

        try:
            with conn.cursor() as cursor:
                # 1. Сначала пытаемся найти базу как ID
                cursor.execute("SELECT id FROM nc_bases_v2 WHERE id = %s", (base_id_or_title,))
                row = cursor.fetchone()
                if row:
                    logger.info(f"База найдена по ID: {row[0]}")
                    return row[0]

                # 2. Если не нашли по ID, ищем по названию
                cursor.execute("SELECT id FROM nc_bases_v2 WHERE title = %s", (base_id_or_title,))
                row = cursor.fetchone()
                if row:
                    logger.info(f"База найдена по названию: {row[0]}")
                    return row[0]

                # 3. Ничего не нашли
                logger.warning(f"База не найдена ни по ID, ни по названию: '{base_id_or_title}'")
                return None
        finally:
            conn.close()
            logger.info("Соединение с базой данных закрыто.")
    except ValueError as e:
        logger.error(f"Ошибка при обработке ввода: {e}")
        return None
