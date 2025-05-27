import requests

BASE_URL = "http://127.0.0.1:8000"

def register_user(username, password):
    url = f"{BASE_URL}/users/"
    data = {"username": username, "password": password}
    resp = requests.post(url, json=data)
    print("Register user:", resp.status_code, resp.json() if resp.status_code != 201 else "Created")
    return resp

def get_token(username, password):
    url = f"{BASE_URL}/token"
    data = {"username": username, "password": password}
    resp = requests.post(url, json=data)
    if resp.status_code == 200:
        token = resp.json()["access_token"]
        print("Got token:", token)
        return token
    else:
        print("Token error:", resp.status_code, resp.json())
        return None

def add_device(token, unique_key):
    url = f"{BASE_URL}/devices/"
    headers = {"Authorization": f"Bearer {token}"}
    data = {"unique_key": unique_key}
    resp = requests.post(url, json=data, headers=headers)
    print("Add device:", resp.status_code, resp.text)  # Изменено на resp.text для вывода текста ответа
    return resp


def list_devices(token):
    url = f"{BASE_URL}/devices/"
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(url, headers=headers)
    print("List devices:", resp.status_code, resp.json())
    return resp

def check_pin(unique_key, pin_code):
    url = f"{BASE_URL}/devices/check_pin"
    headers = {}
    params = {"unique_key": unique_key}
    data = {"pin_code": pin_code}
    resp = requests.post(url, json=data, params=params, headers=headers)
    print("Check PIN:", resp.status_code, resp.json())
    return resp

def change_pin(token, unique_key, old_pin, new_pin):
    url = f"{BASE_URL}/devices/change_pin"
    headers = {"Authorization": f"Bearer {token}"}
    data = {"unique_key": unique_key, "old_pin": old_pin, "new_pin": new_pin}
    resp = requests.post(url, json=data, headers=headers)
    print("Change PIN:", resp.status_code, resp.json())
    return resp
def disarm(token, unique_key):
    url = f"{BASE_URL}/devices/disarm"
    headers = {"Authorization": f"Bearer {token}"}
    data = {"unique_key": unique_key}
    resp = requests.post(url, json=data, headers=headers)
    print("Disarm Signalizetion:", resp.status_code, resp.json())
    return resp

def change_password(token, unique_key, old_password, new_password):
    url = f"{BASE_URL}/devices/change_password"
    headers = {"Authorization": f"Bearer {token}"}
    data = {"unique_key": unique_key, "old_password": old_password, "new_password": new_password}
    resp = requests.post(url, json=data, headers=headers)
    print("Change password:", resp.status_code, resp.json())
    return resp

def post_event(unique_key, event_type):
    url = f"{BASE_URL}/events/"
    data = {"unique_key": unique_key, "event_type": event_type}
    resp = requests.post(url, json=data)
    print("Post event:", resp.status_code, resp.json())
    return resp

def get_logs(unique_key):
    url = f"{BASE_URL}/logs/"
    headers = {}
    data = {"unique_key": unique_key}
    resp = requests.get(url, json=data, headers=headers)
    print("Get logs:", resp.status_code, resp.json())
    return resp

if __name__ == "__main__":
    # 1. Регистрация пользователя
    register_user("testuser2", "testpass2")

    # 2. Получение токена
    token = get_token("testuser2", "testpass2")
    if not token:
        exit(1)

    # 3. Добавление устройства
    add_device(token,"device_key_123")

    # 4. Получение списка устройств
    list_devices(token)

    # 5. Проверка PIN-кода
    check_pin("device_key_123", "4321")

    # 6. Изменение PIN-кода
    change_pin(token, "device_key_123", "4321", "4321")
    disarm(token, "device_key_123")

    # 8. Отправка события
    post_event("device_key_123", "accel")
    post_event("device_key_123", "move")

    # 9. Получение логов
    get_logs("device_key_123")
