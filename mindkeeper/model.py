from datetime import datetime
from enum import StrEnum, auto
from typing import Annotated
from uuid import UUID, uuid4

import annotated_types as at
from pydantic import BaseModel, EmailStr, Field

Tags = list[Annotated[str, at.Len(1, 100)]]


class Note(BaseModel):
    id: UUID = Field(..., default_factory=uuid4)
    title: Annotated[str, at.Len(1, 100)]
    text: Annotated[str, at.Len(0, 1000)]
    tags: Tags = Field(..., default_factory=list)


class PhoneType(StrEnum):
    MOBILE = auto()
    WORK = auto()
    HOME = auto()


class Phone(BaseModel):
    number: str = Field(..., pattern=r'^\+?\d{10,15}$')
    type: PhoneType = PhoneType.MOBILE


class Contact(BaseModel):
    id: UUID = Field(..., default_factory=uuid4)
    name: Annotated[str, at.Len(1, 100)]
    address: Annotated[str, at.Len(1, 250)] | None = None
    email: EmailStr | None = None
    phones: list[Phone] = Field(..., default_factory=list)
    birthday: datetime | None = None
    tags: Tags = Field(..., default_factory=list)
