from typing import Annotated
from uuid import UUID, uuid4

import annotated_types as at
from pydantic import BaseModel, Field, EmailStr, field_validator

class Note(BaseModel):
    id: UUID = Field(..., default_factory=uuid4)
    title: Annotated[str, at.Len(1, 100)]
    text: Annotated[str, at.Len(1, 1000)]
    tags: list[Annotated[str, at.Len(1, 100)]
               ] = Field(..., default_factory=list)
    
class PhoneNumber(BaseModel):
    number: str = Field(...)

    @field_validator('number')
    def validate_phone_number(cls, value):
        import re
        pattern = re.compile(r'^\+?\d{10,15}$')
        if not pattern.match(value):
            raise ValueError('Invalid phone number format')
        return value
    
class Contact(BaseModel):
    id: UUID = Field(..., default_factory=uuid4)
    name: Annotated[str, at.Len(1, 100)]
    address: Annotated[str, at.Len(1, 250)]
    phone_number: PhoneNumber
    email: EmailStr
    birthday: Annotated[str, at.Len(10)]  # format YYYY-MM-DD
