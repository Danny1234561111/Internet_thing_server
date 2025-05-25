import requests
import json

# URL вашего FastAPI приложения
BASE_URL = "http://127.0.0.1:8000"

# Эндпоинты
REGISTER_ENDPOINT = "/register"
USER_ENDPOINT = "/user"

LOGIN = "device1"
PASSWORD = "eqokppkw"
TV_NAME = "TV1"

def register_and_get_user_data(login, password, tv_name=None):
    """
    Регистрирует пользователя, получает API key, а затем получает данные пользователя.
    """

    # 1. Регистрация пользователя
    register_data = {
        "login": login,
        "password": password,
        "tv_name": tv_name
    }
    try:
        response = requests.post(f"{BASE_URL}{REGISTER_ENDPOINT}", json=register_data)
        response.raise_for_status()  # Вызовет исключение для HTTP ошибок (4xx, 5xx)
        register_response = response.json()
        api_key = register_response["api_key"]
        print(f"Регистрация успешна. API Key: {api_key}")

    except requests.exceptions.RequestException as e:
        print(f"Ошибка регистрации: {e}")
        return None

    # 2. Получение данных пользователя
    headers = {"X-API-Key": api_key}
    try:
        response = requests.get(f"{BASE_URL}{USER_ENDPOINT}", headers=headers)
        response.raise_for_status()  # Вызовет исключение для HTTP ошибок (4xx, 5xx)
        user_data = response.json()
        print(f"Данные пользователя: {user_data}")
        return user_data

    except requests.exceptions.RequestException as e:
        print(f"Ошибка получения данных пользователя: {e}")
        return None

# Вызываем функцию с нашими данными
user_data = register_and_get_user_data(LOGIN, PASSWORD, TV_NAME)

if user_data:
    print("Тест пройден успешно!")
else:
    print("Тест завершился с ошибками.")
