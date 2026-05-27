from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime

# Import the status enum from the model to ensure consistency
from app.models.reservation import (
    ReservationStatus as ReservationStatusEnum
)


class ReservationBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    cluster_id: str
    user_name: str = Field(..., min_length=1, max_length=255)
    user_email: Optional[str] = None
    team: Optional[str] = None
    start_time: datetime
    end_time: datetime
    purpose: Optional[str] = None
    notes: Optional[str] = None
    color: Optional[str] = Field(default="#3B82F6", pattern="^#[0-9A-Fa-f]{6}$")

    @field_validator('end_time')
    @classmethod
    def end_time_must_be_after_start(cls, v, info):
        if 'start_time' in info.data and v <= info.data['start_time']:
            raise ValueError('end_time must be after start_time')
        return v


class ReservationCreate(ReservationBase):
    pass


class ReservationUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    team: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    purpose: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[ReservationStatusEnum] = None
    color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")


class ReservationResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    cluster_id: Optional[str] = None  # Can be null if cluster was removed
    cluster_name: Optional[str] = None  # Preserved even after cluster removal
    user_name: str
    user_email: Optional[str] = None
    team: Optional[str] = None
    start_time: datetime
    end_time: datetime
    purpose: Optional[str] = None
    notes: Optional[str] = None
    color: Optional[str] = None
    status: ReservationStatusEnum
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ReservationListResponse(BaseModel):
    reservations: List[ReservationResponse]
    total: int


class CalendarEvent(BaseModel):
    id: str
    title: str
    start: datetime
    end: datetime
    cluster_id: Optional[str] = None  # Can be null if cluster was removed
    cluster_name: str  # Always preserved
    user_name: str
    team: Optional[str] = None
    status: ReservationStatusEnum
    color: str
    description: Optional[str] = None
