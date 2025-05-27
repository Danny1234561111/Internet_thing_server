from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from pydantic import BaseModel, constr
from typing import List, Optional
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import threading
import logging

# --- Конфигурация ---
DATABASE_URL = "sqlite:///./test.db"
SECRET_KEY = "your-secret-key"  # Замените на свой секретный ключ
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# --- Инициализация БД ---
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})  # Для SQLite
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- Логгер ---
logger = logging.getLogger(__name__)

# --- Модели SQLAlchemy ---
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    devices = relationship("Device", back_populates="owner")

class Device(Base):
    __tablename__ = "devices"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    unique_key = Column(String, unique=True, index=True, nullable=False)
    pin_code = Column(String(4), nullable=False)
    pin_change_key = Column(String, nullable=False)
    active = Column(Boolean, default=True)
    alarm_enabled = Column(Boolean, default=True)
    last_accel_event = Column(DateTime, nullable=True)
    last_sound_event = Column(DateTime, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="devices")
    logs = relationship("DeviceLog", back_populates="device")

class DeviceLog(Base):
    __tablename__ = "device_logs"
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"))
    event_type = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    info = Column(String, nullable=True)
    device = relationship("Device", back_populates="logs")

# --- Создание таблиц ---
Base.metadata.create_all(bind=engine)

# --- Pydantic модели ---
class UserCreate(BaseModel):
    username: str
    password: str
class UserLogin(BaseModel):
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
    name: str
    unique_key: str
    pin_code: constr(min_length=4, max_length=4)
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

class PinCheckRequest(BaseModel):
    pin_code: constr(min_length=4, max_length=4)

class PinChangeRequest(BaseModel):
    unique_key: str
    old_pin: constr(min_length=4, max_length=4)
    new_pin: constr(min_length=4, max_length=4)
    pin_change_key: str

class ChangePasswordRequest(BaseModel):
    unique_key: str
    old_password: constr(min_length=4, max_length=4)
    new_password: constr(min_length=4, max_length=4)

class EventPost(BaseModel):
    unique_key: str
    event_type: str  # "accel", "sound"
    timestamp: Optional[datetime] = None

class AlarmToggleRequest(BaseModel):
    unique_key: str
    pin_code: Optional[constr(min_length=4, max_length=4)] = None
    pin_change_key: Optional[str] = None

class LogsRequest(BaseModel):
    unique_key: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

class LogsResponse(BaseModel):
    event_type: str
    timestamp: datetime
    info: Optional[str]

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

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
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

# Регистрация пользователя
@app.post("/users/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
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

# Аутентификация и получение токена
@app.post("/token", response_model=Token)
def login_for_access_token(user_in: UserLogin, db: Session = Depends(get_db)):
    user = authenticate_user(db, user_in.username, user_in.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Добавление устройства
@app.post("/devices/", response_model=DeviceOut)
def add_device(device: DeviceCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    existing = db.query(Device).filter(Device.unique_key == device.unique_key).first()
    if existing:
        raise HTTPException(status_code=400, detail="Device with this unique key already exists")
    new_device = Device(
        name=device.name,
        unique_key=device.unique_key,
        pin_code=device.pin_code,
        pin_change_key=device.pin_change_key,
        active=True,
        alarm_enabled=True,
        owner_id=current_user.id
    )
    db.add(new_device)
    db.commit()
    db.refresh(new_device)
    return new_device

# Получение списка устройств пользователя
@app.get("/devices/", response_model=List[DeviceOut])
def list_devices(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    devices = db.query(Device).filter(Device.owner_id == current_user.id).all()
    return devices

# Проверка PIN-кода устройства
@app.post("/devices/{device_id}/check_pin")
def check_pin(device_id: int, req: PinCheckRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.id == device_id, Device.owner_id == current_user.id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    if not device.active:
        raise HTTPException(status_code=400, detail="Device inactive, PIN check not allowed")
    correct = (req.pin_code == device.pin_code)
    log = DeviceLog(device_id=device.id, event_type="pin_check", info=f"PIN correct: {correct}")
    db.add(log)
    db.commit()
    return {"pin_valid": correct}

# Изменение PIN-кода устройства
@app.post("/devices/change_pin")
def change_pin(req: PinChangeRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.unique_key == req.unique_key, Device.owner_id == current_user.id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    if device.pin_code != req.old_pin:
        raise HTTPException(status_code=400, detail="Old PIN incorrect")
    if device.pin_change_key != req.pin_change_key:
        raise HTTPException(status_code=400, detail="Invalid pin_change_key")
    device.pin_code = req.new_pin
    db.commit()
    log = DeviceLog(device_id=device.id, event_type="pin_change", info="PIN changed")
    db.add(log)
    db.commit()
    return {"status": "PIN changed successfully"}

# Изменение пароля устройства (альтернативная функция)
@app.post("/devices/change_password")
def change_device_password(req: ChangePasswordRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.unique_key == req.unique_key, Device.owner_id == current_user.id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    if req.old_password != device.pin_code:
        raise HTTPException(status_code=400, detail="Old password is incorrect")
    device.pin_code = req.new_password
    db.commit()
    return {"status": "Password changed successfully"}

# Обработка событий с устройств
@app.post("/events/")
def post_event(event: EventPost, db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.unique_key == event.unique_key).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    if not device.active:
        raise HTTPException(status_code=400, detail="Device inactive")
    now = event.timestamp or datetime.utcnow()

    if event.event_type == "accel":
        device.last_accel_event = now
        db.add(DeviceLog(device_id=device.id, event_type="accel_open", timestamp=now))
        db.commit()
    elif event.event_type == "sound":
        device.last_sound_event = now
        db.add(DeviceLog(device_id=device.id, event_type="sound_enter", timestamp=now))
        db.commit()
        if device.alarm_enabled and device.last_accel_event:
            delta = (now - device.last_accel_event).total_seconds()
            if 0 <= delta <= 60:
                db.add(DeviceLog(device_id=device.id, event_type="intrusion_detected", timestamp=now,
                                 info="Motion detected after door opened"))
                db.commit()
    else:
        raise HTTPException(status_code=400, detail="Unknown event_type")
    db.commit()
    return {"status": "event recorded"}

# Получение логов устройства
@app.post("/logs/", response_model=List[LogsResponse])
def get_logs(req: LogsRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.unique_key == req.unique_key, Device.owner_id == current_user.id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    query = db.query(DeviceLog).filter(DeviceLog.device_id == device.id)
    if req.start_time:
        query = query.filter(DeviceLog.timestamp >= req.start_time)
    if req.end_time:
        query = query.filter(DeviceLog.timestamp <= req.end_time)
    logs = query.order_by(DeviceLog.timestamp.desc()).all()
    return logs

# Функция для автоматического повторного включения сигнализации
def reenable_alarm_later(device_id: int, delay_sec=300):
    def task():
        db = SessionLocal()
        try:
            device = db.query(Device).filter(Device.id == device_id).first()
            if device:
                device.alarm_enabled = True
                db.commit()
        finally:
            db.close()

    threading.Timer(delay_sec, task).start()

# Переключение состояния сигнализации устройства
@app.post("/devices/toggle_alarm")
def toggle_alarm(req: AlarmToggleRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.unique_key == req.unique_key, Device.owner_id == current_user.id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    if not device.active:
        raise HTTPException(status_code=400, detail="Device inactive")

    # Проверка PIN и pin_change_key
    if req.pin_code:
        if req.pin_code != device.pin_code:
            raise HTTPException(status_code=400, detail="Invalid PIN")
        if req.pin_change_key != device.pin_change_key:
            raise HTTPException(status_code=400, detail="Invalid pin_change_key")
    else:
        if req.pin_change_key != device.pin_change_key:
            raise HTTPException(status_code=400, detail="pin_change_key required to toggle alarm without PIN")

    device.alarm_enabled = not device.alarm_enabled
    db.add(DeviceLog(device_id=device.id,
                     event_type="alarm_on" if device.alarm_enabled else "alarm_off",
                     info=f"Alarm toggled by user {current_user.username}"))
    db.commit()

    if not device.alarm_enabled:
        reenable_alarm_later(device.id)

    return {"alarm_enabled": device.alarm_enabled}

# --- Инициализация при старте ---
@app.on_event("startup")
def on_startup():
    db = SessionLocal()
    init_devices(db)
    db.close()

# --- Запуск приложения ---
# Для запуска используйте команду: uvicorn main:app --reload
