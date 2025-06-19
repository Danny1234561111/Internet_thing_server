from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey, DateTime, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from pydantic import BaseModel, constr
from typing import List, Optional
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta

# --- Конфигурация ---
DATABASE_URL = "sqlite:///./test.db"
SECRET_KEY = "your-secret-key"  # Замените на свой секретный ключ
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# --- Инициализация БД ---
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- Ассоциация многие-ко-многим ---
user_device_association = Table(
    'user_device',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('device_id', Integer, ForeignKey('devices.id'), primary_key=True)
)

# --- Модели ---
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    devices = relationship("Device", secondary=user_device_association, back_populates="owners")

class Device(Base):
    __tablename__ = "devices"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    unique_key = Column(String, unique=True, index=True, nullable=False)
    pin_code = Column(String(4), nullable=False)
    active = Column(Boolean, default=True)
    owners = relationship("User", secondary=user_device_association, back_populates="devices")
    logs = relationship("DeviceLog", back_populates="device")

class DeviceLog(Base):
    __tablename__ = "device_logs"
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"))
    event_type = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    info = Column(String, nullable=True)
    device = relationship("Device", back_populates="logs")

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

class DeviceUpdate(BaseModel):
    unique_key: str

class DeviceOut(BaseModel):
    id: int
    name: str
    unique_key: str
    pin_code: str
    active: bool
    class Config:
        orm_mode = True

class PinCheckRequest(BaseModel):
    pin_code: constr(min_length=4, max_length=4)
    unique_key: str

class PinChangeRequest(BaseModel):
    unique_key: str
    old_pin: constr(min_length=4, max_length=4)
    new_pin: constr(min_length=4, max_length=4)

class ChangePasswordRequest(BaseModel):
    unique_key: str
    old_password: constr(min_length=4, max_length=4)
    new_password: constr(min_length=4, max_length=4)

class EventPost(BaseModel):
    unique_key: str
    event_type: str

class LogsRequest(BaseModel):
    unique_key: str

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
    if not user or not verify_password(password, user.hashed_password):
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

# --- Инициализация начальных устройств ---
def init_devices(db: Session):
    if db.query(Device).count() == 0:
        devices = [
            Device(name="Device device_key_123", unique_key="device_key_123", pin_code="0000"),
            Device(name="Device device_key_456", unique_key="device_key_456", pin_code="0000"),
        ]
        db.add_all(devices)
        db.commit()

# --- FastAPI приложение ---
app = FastAPI()

# --- Роуты ---

@app.post("/users/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(user_in: UserCreate, db: Session = Depends(get_db)):
    if get_user_by_username(db, user_in.username):
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = get_password_hash(user_in.password)
    user = User(username=user_in.username, hashed_password=hashed_password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@app.post("/token", response_model=Token)
def login_for_access_token(user_in: UserLogin, db: Session = Depends(get_db)):
    user = authenticate_user(db, user_in.username, user_in.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password",
                            headers={"WWW-Authenticate": "Bearer"})
    access_token = create_access_token(data={"sub": user.username},
                                       expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/devices/", response_model=DeviceOut)
def add_device(device_in: DeviceUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    existing_device = db.query(Device).filter(Device.unique_key == device_in.unique_key).first()

    if existing_device:
        if current_user not in existing_device.owners:
            existing_device.owners.append(current_user)
            db.commit()
            db.refresh(existing_device)
        return existing_device

    # Если устройство не найдено — выдаём ошибку
    raise HTTPException(status_code=400,
                        detail="Device with this unique_key does not exist. Cannot create a new device.")


@app.get("/devices/", response_model=List[DeviceOut])
def list_devices(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return current_user.devices


@app.post("/devices/check_pin")
def check_pin(req: PinCheckRequest, db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.unique_key == req.unique_key).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    correct = req.pin_code == device.pin_code
    current_time = datetime.utcnow()
    if (correct):
    # Логируем событие pin_check
        log = DeviceLog(device_id=device.id, event_type="pin_check", timestamp=current_time, info=f"PIN correct: {correct}")
    else:
        return {"info":f"PIN correct: {correct}"}
    db.add(log)
    db.commit()

    return {"pin_valid": correct}

@app.post("/devices/change_pin")
def change_pin(req: PinChangeRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.unique_key == req.unique_key, Device.owners.any(id=current_user.id)).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    if device.pin_code != req.old_pin:
        raise HTTPException(status_code=400, detail="Old PIN incorrect")
    device.pin_code = req.new_pin
    db.commit()
    log = DeviceLog(device_id=device.id, event_type="pin_change", info="PIN changed")
    db.add(log)
    db.commit()
    return {"status": "PIN changed successfully"}

@app.post("/devices/change_password")
def change_device_password(req: ChangePasswordRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.unique_key == req.unique_key, Device.owners.any(id=current_user.id)).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    if req.old_password != device.pin_code:
        raise HTTPException(status_code=400, detail="Old password is incorrect")
    device.pin_code = req.new_password
    db.commit()
    return {"status": "Password changed successfully"}
@app.get("/devices/{unique_key}/pin_checks/")
def get_pin_checks(key: LogsRequest, db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.unique_key == key.unique_key).first()
    pin_checks = db.query(DeviceLog).filter(
        DeviceLog.device_id ==device.id,
        DeviceLog.event_type.in_(['pin_check', 'danger'])
    ).all()

    if not pin_checks:
        return {"message": "Sorry, no pin_check events found for this device."}  # Возвращаем сообщение вместо ошибки

    return pin_checks
@app.post("/devices/disarm")
def disarm_device(key: LogsRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.unique_key == key.unique_key).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    current_time = datetime.utcnow()
    log = DeviceLog(device_id=device.id, event_type="pin_check", timestamp=current_time,
                        info=f"PIN correct: {True}")
    db.add(log)
    db.commit()
    db.commit()
    return {'pin_valid': True}
@app.post("/events/")
def post_event(event: EventPost, db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.unique_key == event.unique_key).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    current_time = datetime.utcnow()
    log = DeviceLog(device_id=device.id, event_type=event.event_type, timestamp=current_time)
    db.add(log)
    db.commit()

    # Проверяем, если событие 'move'
    if event.event_type == 'move':
        recent_danger = db.query(DeviceLog).filter(
            DeviceLog.device_id == device.id,
            DeviceLog.event_type == 'danger',
            DeviceLog.timestamp >= current_time - timedelta(minutes=5)
        ).first()

        recent_pin_check = db.query(DeviceLog).filter(
            DeviceLog.device_id == device.id,
            DeviceLog.event_type == 'pin_check',
            DeviceLog.timestamp >= current_time - timedelta(minutes=3)
        ).first()

        print("Recent Danger:", recent_danger)
        print("Recent Pin Check:", recent_pin_check)

        if not recent_danger and not recent_pin_check:
            recent_accel = db.query(DeviceLog).filter(
                DeviceLog.device_id == device.id,
                DeviceLog.event_type == 'accel',
                DeviceLog.timestamp >= current_time - timedelta(minutes=5)
            ).first()

            if recent_accel:
                danger_log = DeviceLog(device_id=device.id, event_type='danger', timestamp=current_time)
                db.add(danger_log)
                db.commit()
                print("Danger event added")

    return {"status": "event recorded"}


@app.get("/logs/")
def get_logs(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Получаем все устройства, принадлежащие текущему пользователю
    user_devices = current_user.devices

    if not user_devices:
        raise HTTPException(status_code=404, detail="No devices found for this user")

    # Получаем текущее время
    current_time = datetime.utcnow()

    # Получаем события 'danger' за последние 5 минут для всех устройств пользователя
    logs = db.query(DeviceLog).filter(
        DeviceLog.device_id.in_([device.id for device in user_devices]),
        DeviceLog.event_type == 'danger',
        DeviceLog.timestamp >= current_time - timedelta(minutes=5)
    ).all()

    return logs


@app.on_event("startup")
def on_startup():
    db = SessionLocal()
    init_devices(db)
    db.close()
