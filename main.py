from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from pydantic import BaseModel, constr
from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import sessionmaker, relationship, declarative_base, Session
from typing import List, Optional
from datetime import datetime
import threading
from passlib.context import CryptContext
import logging
# Настройки базы данных
DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Настройка хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# --- Модели БД ---
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    devices = relationship("Device", back_populates="owner")


class Device(Base):
    __tablename__ = "devices"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    unique_key = Column(String, unique=True, index=True, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"))
    pin_code = Column(String(4), nullable=False)
    pin_change_key = Column(String, nullable=False)
    active = Column(Boolean, default=True)
    alarm_enabled = Column(Boolean, default=True)
    last_accel_event = Column(DateTime, nullable=True)
    last_sound_event = Column(DateTime, nullable=True)

    owner = relationship("User", back_populates="devices")
    logs = relationship("DeviceLog", back_populates="device")


class DeviceLog(Base):
    __tablename__ = "device_logs"
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"))
    event_type = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    info = Column(String, nullable=True)

    device = relationship("Device", back_populates="logs")


Base.metadata.create_all(bind=engine)


# --- Схемы Pydantic ---
class UserCreate(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str

    class Config:
        orm_mode = True


class DeviceCreate(BaseModel):
    name: str
    unique_key: str
    pin_code: constr(min_length=4, max_length=4)
    pin_change_key: str


class DeviceOut(BaseModel):
    id: int
    name: str
    unique_key: str
    active: bool
    alarm_enabled: bool

    class Config:
        orm_mode = True


class PinCheckRequest(BaseModel):
    pin_code: constr(min_length=4, max_length=4)


class PinChangeRequest(BaseModel):
    unique_key: str
    old_pin: constr(min_length=4, max_length=4)
    new_pin: constr(min_length=4, max_length=4)
    pin_change_key: str


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


# --- Зависимости ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Хеширование паролей ---
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# --- Регистрация пользователя ---
logger = logging.getLogger(__name__)
@app.post("/register", response_model=UserOut)
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == user.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")

    hashed_password = hash_password(user.password)
    new_user = User(username=user.username, password=hashed_password)

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except Exception as e:
        db.rollback()
        logger.error(f"Error during user registration: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    return new_user


# --- Аутентификация ---
@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = f"token-{user.username}"  # Здесь должен быть более безопасный подход к созданию токенов
    return {"access_token": token, "token_type": "bearer"}


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    username = token.split('-')[1]  # Извлечение имени пользователя из токена
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="User  not found")
    return user


# --- Логика устройства и сигнализации ---
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
        owner_id=current_user.id,
        active=True,
        alarm_enabled=True,
    )
    db.add(new_device)
    db.commit()
    db.refresh(new_device)
    return new_device


@app.get("/devices/", response_model=List[DeviceOut])
def list_devices(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Device).filter(Device.owner_id == current_user.id).all()


@app.post("/devices/{device_id}/check_pin")
def check_pin(device_id: int, req: PinCheckRequest, current_user: User = Depends(get_current_user),
              db: Session = Depends(get_db)):
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


# --- Обработка событий с устройств ---
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


# --- Получение логов входов и выходов ---
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


# --- Отключение и автоматическое включение сигнализации ---
def reenable_alarm_later(device_id: int, delay_sec=300):
    def task():
        db = SessionLocal()
        device = db.query(Device).filter(Device.id == device_id).first()
        if device:
            device.alarm_enabled = True
            db.commit()
            db.close()

    threading.Timer(delay_sec, task).start()


@app.post("/devices/toggle_alarm")
def toggle_alarm(req: AlarmToggleRequest, current_user: User = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.unique_key == req.unique_key, Device.owner_id == current_user.id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    if not device.active:
        raise HTTPException(status_code=400, detail="Device inactive")

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

# --- Запуск приложения ---
# uvicorn main:app --reload
