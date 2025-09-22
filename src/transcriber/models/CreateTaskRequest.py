from pydantic import BaseModel


class CreateTaskRequest(BaseModel):
    file_path: str

