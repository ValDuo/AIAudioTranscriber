from sqlalchemy import create_engine, Column, String, DateTime, Text, JSON, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import enum
from datetime import datetime
import json

# Настройка подключения к базе данных
DATABASE_URL = "postgresql://username:password@localhost:5432/transcription_db"

# Создаем движок SQLAlchemy
engine = create_engine(DATABASE_URL)

# Создаем фабрику сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс для моделей
Base = declarative_base()


# Enum для статусов задач (аналог вашего TaskStatus)
class TaskStatusEnum(enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


# Модель для хранения задач
class TaskDB(Base):
    __tablename__ = "tasks"

    task_id = Column(String, primary_key=True, index=True)
    status = Column(Enum(TaskStatusEnum), default=TaskStatusEnum.PENDING)
    file_path = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    results = Column(JSON, nullable=True)  # Здесь будем хранить TranscriptionResult в JSON
    error = Column(Text, nullable=True)


# Функция для получения сессии БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Создаем таблицы при старте
def init_db():
    Base.metadata.create_all(bind=engine)