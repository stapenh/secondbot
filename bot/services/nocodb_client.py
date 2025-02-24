# bot/services/nocodb_client.py
import httpx

from logger_config import logger



class NocodbClient:
    def __init__(self, base_url: str, api_token: str):
        """
        Инициализация клиента NocoDB.

        :param base_url: Базовый URL вашего NocoDB (например, "http://localhost:8080").
        :param api_token: API-токен для аутентификации.
        """
        self.base_url = base_url
        self.api_token = api_token
        self.headers = {
            "xc-token": self.api_token,
            "Content-Type": "application/json"
        }

    async def get_project_users(self, project_id: str):
        """
        Получает список пользователей, у которых есть доступ к проекту.

        :param project_id: ID проекта.
        :return: Список пользователей или None в случае ошибки.
        """
        url = f"{self.base_url}/api/v1/db/meta/projects/{project_id}/users"
        try:
            async with httpx.AsyncClient() as client:
                logger.info(f"Отправка запроса к URL: {url}")
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()  # Проверяем, что запрос успешен
                logger.info(f"Ответ от NocoDB: {response.json()}")
                return response.json()  # Возвращаем JSON-ответ
        except httpx.HTTPStatusError as e:
            logger.error(f"Ошибка при запросе к NocoDB: {e}")
            return None