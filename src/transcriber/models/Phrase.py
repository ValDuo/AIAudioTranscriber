from pydantic import BaseModel


class Phrase(BaseModel):
    start: float
    end: float
    text: str

