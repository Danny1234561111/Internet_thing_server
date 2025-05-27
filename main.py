from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from pydantic import BaseModel
from typing import List, Optional
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import threading

# --- Конфигурация ---
DATABASE_URL = "sqlite:///./test.db"
SECRET_KEY = "your-secret-key"  # Замените на свой секретный ключ
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# --- Инициализация БД ---
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})  # Для SQLite
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# --- Модели SQLAlchemy ---
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    devices = relationship("Device", back_populates="owner")


class Device(Base):
    __tablename__ = "devices"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    unique_key = Column(String, unique=True, index=True)
    pin_code = Column(String)
    pin_change_key = Column(String)
    active = Column(Boolean, default=True)
    alarm_enabled = Column(Boolean, default=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="devices")


# --- Создание таблиц ---
Base.metadata.create_all(bind=engine)


# --- Pydantic модели ---
class UserCreate(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class DeviceCreate(BaseModel):
    unique_key: str
    pin_change_key: str


class DeviceOut(BaseModel):
    id: int
    name: str
    unique_key: str
    pin_code: str
    pin_change_key: str
    active: bool
    alarm_enabled: bool
    owner_id: Optional[int]

    class Config:
        orm_mode = True


# --- Безопасность ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# --- Зависимости ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()


def authenticate_user(db: Session, username: str, password: str):
    user = get_user_by_username(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user_by_username(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


# --- Инициализация начальных данных ---
def init_devices(db: Session):
    existing = db.query(Device).count()
    if existing == 0:
        device1 = Device(
            name="Device device_key_123",
            unique_key="device_key_123",
            pin_code="0000",
            pin_change_key="change_key_abc",
            active=True,
            alarm_enabled=True,
            owner_id=None
        )
        device2 = Device(
            name="Device device_key_456",
            unique_key="device_key_456",
            pin_code="0000",
            pin_change_key="change_key_def",
            active=True,
            alarm_enabled=True,
            owner_id=None
        )
        db.add_all([device1, device2])
        db.commit()


# --- FastAPI приложение ---
app = FastAPI()


# --- Роуты ---
@app.post("/users/", response_model=UserOut, status_code = status.HTTP_201_CREATED)

def create_user(user_in: UserCreate, db: Session = Depends(get_db)):
    user = get_user_by_username(db, user_in.username)
    if user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = get_password_hash(user_in.password)
    new_user = User(username=user_in.username, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password",
                            headers={"WWW-Authenticate": "Bearer"})
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/devices/", response_model=DeviceOut)
def add_device(device: DeviceCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    existing = db.query(Device).filter(Device.unique_key == device.unique_key).first()
    if existing:
        raise HTTPException(status_code=400, detail="Device with this unique key already exists")
    new_device = Device(
        name=f"Device {device.unique_key}",
        unique_key=device.unique_key,
        pin_code="0000",
        pin_change_key=device.pin_change_key,
        active=True,
        alarm_enabled=True,
        owner_id=current_user.id
    )
    db.add(new_device)
    db.commit()
    db.refresh(new_device)
    return new_device


@app.get("/devices/", response_model=List[DeviceOut])
def list_devices(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    devices = db.query(Device).filter(Device.owner_id == current_user.id).all()
    return devices


# --- Инициализация при старте ---
@app.on_event("startup")
def on_startup():
    db = SessionLocal()
    init_devices(db)
    db.close()


# --- Логика для управления сигнализацией и событиями ---
@app.post("/devices/{device_id}/toggle_alarm")
def toggle_alarm(device_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.id == device_id, Device.owner_id == current_user.id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    device.alarm_enabled = not device.alarm_enabled
    db.commit()
    return {"alarm_enabled": device.alarm_enabled}


@app.post("/events/")
def post_event(event: dict, db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.unique_key == event["unique_key"]).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    # Логика обработки событий
    return {"status": "event recorded"}

# --- Запуск приложения ---
# Для запуска используйте команду: uvicorn main:app --reload
