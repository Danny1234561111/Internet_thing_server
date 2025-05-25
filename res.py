import requests

# URL вашего FastAPI сервера
url = "https://internet-thing-server-1-wtlb.onrender.com/register"

# Данные для регистрации нового пользователя
user_data = {
    "username": "new_user",
    "password": "secure_password"
}

# Выполнение POST-запроса для регистрации
response = requests.post(url, json=user_data)

# Проверка ответа от сервера
if response.status_code == 200:
    print("Пользователь успешно зарегистрирован:", response.json())
else:
    print("Ошибка при регистрации:", response.status_code, response.json())
