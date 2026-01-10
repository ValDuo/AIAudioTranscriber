import SQLAlchemy as SQLAlchemy
from sqlalchemy.dialects.postgresql import JSON, ENUM
from datetime import datetime
import enum

db = SQLAlchemy()


# Создаем enum для статуса задач (аналог TaskStatus из Pydantic)
class TaskStatusEnum(str, enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


# Модель для базы данных
class TaskResponseModel(db.Model):
    __tablename__ = 'task_responses'

    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.String(255), unique=True, nullable=False, index=True)
    status = db.Column(ENUM(TaskStatusEnum, name='task_status'), nullable=False)

    results = db.Column(JSON, nullable=True)

    error = db.Column(db.Text, nullable=True)
    def __repr__(self):
        return f'<TaskResponse {self.task_id} - {self.status}>'

    # Метод для конвертации в Pydantic модель
    def to_pydantic(self):
        from pydantic_models import TaskResponse, TaskStatus, TranscriptionResult

        # Конвертируем статус
        status_enum = TaskStatus(self.status.value)

        # Создаем Pydantic объект
        return TaskResponse(
            task_id=self.task_id,
            status=status_enum,
            results=TranscriptionResult(**self.results) if self.results else None,
            error=self.error
        )