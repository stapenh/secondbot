import os

API_TOKEN = os.getenv("API_TOKEN")
NOCODB_BASE_URL = os.getenv("NOCODB_BASE_URL")
NOCODB_API_TOKEN = os.getenv("NOCODB_API_TOKEN")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
INVITE_URL = os.getenv("INVITE_URL")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(","))) if os.getenv("ADMIN_IDS") else []