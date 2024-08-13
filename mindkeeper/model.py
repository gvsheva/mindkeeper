from typing import Annotated
from uuid import UUID, uuid4

import annotated_types as at
from pydantic import BaseModel, Field


class Note(BaseModel):
    id: UUID = Field(..., default_factory=uuid4)
    title: Annotated[str, at.Len(1, 100)]
    text: Annotated[str, at.Len(1, 1000)]
    tags: list[Annotated[str, at.Len(1, 100)]
               ] = Field(..., default_factory=list)
