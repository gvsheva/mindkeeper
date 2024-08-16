from datetime import datetime
from enum import Enum, StrEnum, auto
from typing import Annotated, Literal

import annotated_types as at
import phonenumbers
from pydantic import AfterValidator, BaseModel, EmailStr, Field

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


def _validate_phone_number(value: str) -> str:
    try:
        number = phonenumbers.parse(value, region="UA")
    except phonenumbers.phonenumberutil.NumberParseException as e:
        raise ValueError(str(e))
    return f"+({number.country_code}) {number.national_number}"


PhoneNumber = Annotated[str, AfterValidator(_validate_phone_number)]


class PhoneType(StrEnum):
    MOBILE = auto()
    WORK = auto()
    HOME = auto()


class Phone(BaseModel):
    number: PhoneNumber
    type: PhoneType = PhoneType.MOBILE


class Contact(BaseModel):
    id: int | Literal[_GENERATE_TYPE.GENERATE] = GENERATE
    name: Annotated[str, at.Len(1, 100)]
    address: Annotated[str, at.Len(1, 250)] | None = None
    email: EmailStr | None = None
    phones: list[Phone] = Field(..., default_factory=list)
    birthday: datetime | None = None
    tags: Tags = Field(..., default_factory=list)
