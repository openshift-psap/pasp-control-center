from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from datetime import datetime, timedelta
import logging

from app.core.database import get_db
from app.services.reservation_service import ReservationService
from app.models.reservation import ReservationStatus
from app.schemas.reservation import (
    ReservationCreate,
    ReservationUpdate,
    ReservationResponse,
    ReservationListResponse,
    CalendarEvent
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("", response_model=ReservationListResponse)
async def list_reservations(
    skip: int = 0,
    limit: int = 100,
    cluster_id: Optional[str] = None,
    user_name: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    service = ReservationService(db)
    
    status_enum = None
    if status:
        try:
            status_enum = ReservationStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    
    reservations, total = await service.get_reservations(
        skip=skip,
        limit=limit,
        cluster_id=cluster_id,
        user_name=user_name,
        start_date=start_date,
        end_date=end_date,
        status=status_enum
    )
    
    response_items = []
    for r in reservations:
        item = ReservationResponse(
            id=r.id,
            title=r.title,
            description=r.description,
            cluster_id=r.cluster_id,
            user_name=r.user_name,
            user_email=r.user_email,
            team=r.team,
            start_time=r.start_time,
            end_time=r.end_time,
            purpose=r.purpose,
            notes=r.notes,
            color=r.color,
            status=r.status,
            created_at=r.created_at,
            updated_at=r.updated_at,
            cluster_name=r.cluster.name if r.cluster else None
        )
        response_items.append(item)
    
    return ReservationListResponse(reservations=response_items, total=total)


@router.post("", response_model=ReservationResponse, status_code=201)
async def create_reservation(
    reservation_data: ReservationCreate,
    db: AsyncSession = Depends(get_db)
):
    service = ReservationService(db)
    
    try:
        reservation = await service.create_reservation(reservation_data)
        return ReservationResponse(
            id=reservation.id,
            title=reservation.title,
            description=reservation.description,
            cluster_id=reservation.cluster_id,
            user_name=reservation.user_name,
            user_email=reservation.user_email,
            team=reservation.team,
            start_time=reservation.start_time,
            end_time=reservation.end_time,
            purpose=reservation.purpose,
            notes=reservation.notes,
            color=reservation.color,
            status=reservation.status,
            created_at=reservation.created_at,
            updated_at=reservation.updated_at
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/calendar", response_model=List[CalendarEvent])
async def get_calendar_events(
    start_date: datetime,
    end_date: datetime,
    cluster_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    service = ReservationService(db)
    events = await service.get_calendar_events(start_date, end_date, cluster_id)
    return events


@router.get("/cluster/{cluster_id}/current")
async def get_current_cluster_user(
    cluster_id: str,
    db: AsyncSession = Depends(get_db)
):
    service = ReservationService(db)
    reservation = await service.get_current_user(cluster_id)
    
    if not reservation:
        return {"occupied": False, "current_user": None}
    
    return {
        "occupied": True,
        "current_user": {
            "user_name": reservation.user_name,
            "team": reservation.team,
            "title": reservation.title,
            "start_time": reservation.start_time,
            "end_time": reservation.end_time
        }
    }


@router.get("/{reservation_id}", response_model=ReservationResponse)
async def get_reservation(
    reservation_id: str,
    db: AsyncSession = Depends(get_db)
):
    service = ReservationService(db)
    reservation = await service.get_reservation(reservation_id)
    
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")
    
    return ReservationResponse(
        id=reservation.id,
        title=reservation.title,
        description=reservation.description,
        cluster_id=reservation.cluster_id,
        user_name=reservation.user_name,
        user_email=reservation.user_email,
        team=reservation.team,
        start_time=reservation.start_time,
        end_time=reservation.end_time,
        purpose=reservation.purpose,
        notes=reservation.notes,
        color=reservation.color,
        status=reservation.status,
        created_at=reservation.created_at,
        updated_at=reservation.updated_at,
        cluster_name=reservation.cluster.name if reservation.cluster else None
    )


@router.put("/{reservation_id}", response_model=ReservationResponse)
async def update_reservation(
    reservation_id: str,
    reservation_data: ReservationUpdate,
    db: AsyncSession = Depends(get_db)
):
    service = ReservationService(db)
    
    try:
        reservation = await service.update_reservation(reservation_id, reservation_data)
        if not reservation:
            raise HTTPException(status_code=404, detail="Reservation not found")
        
        return ReservationResponse(
            id=reservation.id,
            title=reservation.title,
            description=reservation.description,
            cluster_id=reservation.cluster_id,
            user_name=reservation.user_name,
            user_email=reservation.user_email,
            team=reservation.team,
            start_time=reservation.start_time,
            end_time=reservation.end_time,
            purpose=reservation.purpose,
            notes=reservation.notes,
            color=reservation.color,
            status=reservation.status,
            created_at=reservation.created_at,
            updated_at=reservation.updated_at,
            cluster_name=reservation.cluster.name if reservation.cluster else None
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{reservation_id}", status_code=204)
async def delete_reservation(
    reservation_id: str,
    db: AsyncSession = Depends(get_db)
):
    service = ReservationService(db)
    deleted = await service.delete_reservation(reservation_id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Reservation not found")


@router.post("/{reservation_id}/cancel", response_model=ReservationResponse)
async def cancel_reservation(
    reservation_id: str,
    db: AsyncSession = Depends(get_db)
):
    service = ReservationService(db)
    reservation = await service.cancel_reservation(reservation_id)
    
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")
    
    return ReservationResponse(
        id=reservation.id,
        title=reservation.title,
        description=reservation.description,
        cluster_id=reservation.cluster_id,
        user_name=reservation.user_name,
        user_email=reservation.user_email,
        team=reservation.team,
        start_time=reservation.start_time,
        end_time=reservation.end_time,
        purpose=reservation.purpose,
        notes=reservation.notes,
        color=reservation.color,
        status=reservation.status,
        created_at=reservation.created_at,
        updated_at=reservation.updated_at,
        cluster_name=reservation.cluster.name if reservation.cluster else None
    )
