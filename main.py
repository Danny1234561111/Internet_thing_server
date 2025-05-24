from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base, Session
import secrets

DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False)
Base = declarative_base()

app = FastAPI()

# Модель БД
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    login = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    tv_name = Column(String, nullable=True)
    api_key = Column(String, unique=True, index=True, nullable=True)

Base.metadata.create_all(bind=engine)

# Pydantic модели
class RegisterRequest(BaseModel):
    login: str
    password: str
    tv_name: str = None

class RegisterResponse(BaseModel):
    api_key: str

class UserDataResponse(BaseModel):
    login: str
    tv_name: str = None

# Зависимость для сессии БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Новый маршрут для корня
@app.get("/")
def read_root():
    return {"message": "Welcome to the FastAPI server!"}

@app.post("/register", response_model=RegisterResponse)
def register_user(data: RegisterRequest, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.login == data.login).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Login already registered")
    api_key = secrets.token_hex(16)
    user = User(login=data.login, password=data.password, tv_name=data.tv_name, api_key=api_key)
    db.add(user)
    db.commit()
    db.refresh(user)
    return RegisterResponse(api_key=api_key)

# Получение данных пользователя по api_key в заголовке
@app.get("/user", response_model=User DataResponse)  # Исправлено здесь
def get_user_data(x_api_key: str = Header(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.api_key == x_api_key).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return UserDataResponse(login=user.login, tv_name=user.tv_name)
