from __future__ import annotations

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RoomCreateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(..., min_length=3, max_length=100)
    location: str = Field(..., min_length=5, max_length=150)
    capacity: int = Field(..., gt=0, le=500)
    description: Optional[str] = Field(default=None, max_length=1000)
    equipment: Optional[List[str]] = Field(default_factory=list)


class RoomUpdateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: Optional[str] = Field(default=None, min_length=3, max_length=100)
    location: Optional[str] = Field(default=None, min_length=5, max_length=150)
    capacity: Optional[int] = Field(default=None, gt=0, le=500)
    description: Optional[str] = Field(default=None, max_length=1000)
    equipment: Optional[List[str]] = None
    is_active: Optional[bool] = None


class RoomResponse(BaseModel):
    id: UUID
    name: str
    location: str
    capacity: int
    description: Optional[str] = None
    is_active: bool
    equipment: List[str] = []
    created_at: str
    updated_at: str
    created_by: UUID
    updated_by: UUID

    @classmethod
    def from_orm_obj(cls, obj: dict) -> "RoomResponse":
        return cls(
            id=obj["id"],
            name=obj["name"],
            location=obj["location"],
            capacity=obj["capacity"],
            description=obj.get("description"),
            is_active=obj["is_active"],
            equipment=obj.get("equipment", []),
            created_at=obj["created_at"],
            updated_at=obj["updated_at"],
            created_by=obj["created_by"],
            updated_by=obj["updated_by"],
        )


class RoomListResponse(BaseModel):
    items: List[RoomResponse]
    page: int
    page_size: int
    total: int


class RoomRecord(BaseModel):
    id: UUID
    name: str
    location: str
    capacity: int
    description: Optional[str]
    is_active: bool
    equipment: List[str]
    created_at: datetime
    updated_at: datetime
    created_by: UUID
    updated_by: UUID
