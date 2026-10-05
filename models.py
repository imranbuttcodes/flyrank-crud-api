from sqlmodel import Field, SQLModel
from typing import Optional
from pydantic import BaseModel

class Task(SQLModel, table=True):
    __tablename__ = "tasks"
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    done: bool = False


class UserCredentials(BaseModel):
    email: str
    password: str
