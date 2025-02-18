# bot/services/nocodb_client.py
import requests

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
            "xc-auth": self.api_token,
            "Content-Type": "application/json"
        }

    def get_project_users(self, project_id: str):
        """
        Получает список пользователей, у которых есть доступ к проекту.

        :param project_id: ID проекта.
        :return: Список пользователей или None в случае ошибки.
        """
        url = f"{self.base_url}/api/v1/db/meta/projects/{project_id}/users"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()  # Проверяем, что запрос успешен
            return response.json()  # Возвращаем JSON-ответ
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при запросе к NocoDB: {e}")
            return None