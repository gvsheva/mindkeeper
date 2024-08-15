from datetime import datetime
from enum import Enum, StrEnum, auto
from typing import Annotated, Literal

import annotated_types as at
from pydantic import BaseModel, EmailStr, Field

Tags = list[Annotated[str, at.Len(1, 100)]]


class _GENERATE_TYPE(Enum):
    GENERATE = auto()


GENERATE = _GENERATE_TYPE.GENERATE


class Note(BaseModel):
    id: int | Literal[_GENERATE_TYPE.GENERATE] = GENERATE
    title: Annotated[str, at.Len(1, 100)]
    text: str
    tags: Tags = Field(..., default_factory=list)
    created_at: datetime = Field(..., default_factory=datetime.now)
    updated_at: datetime = Field(..., default_factory=datetime.now)


class PhoneType(StrEnum):
    MOBILE = auto()
    WORK = auto()
    HOME = auto()


class Phone(BaseModel):
    number: str = Field(..., pattern=r'^\+?\d{10,15}$')
    type: PhoneType = PhoneType.MOBILE


class Contact(BaseModel):
    id: int | Literal[_GENERATE_TYPE.GENERATE] = GENERATE
    name: Annotated[str, at.Len(1, 100)]
    address: Annotated[str, at.Len(1, 250)] | None = None
    email: EmailStr | None = None
    phones: list[Phone] = Field(..., default_factory=list)
    birthday: datetime | None = None
    tags: Tags = Field(..., default_factory=list)
