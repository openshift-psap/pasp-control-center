from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from app.models.reservation import Reservation, ReservationStatus
from app.models.cluster import Cluster
from app.schemas.reservation import (
    ReservationCreate,
    ReservationUpdate,
    ReservationResponse,
    CalendarEvent
)

logger = logging.getLogger(__name__)


class ReservationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_reservation(
        self,
        reservation_data: ReservationCreate
    ) -> Reservation:
        cluster_result = await self.db.execute(
            select(Cluster).where(Cluster.id == reservation_data.cluster_id)
        )
        cluster = cluster_result.scalar_one_or_none()
        if not cluster:
            raise ValueError("Cluster not found")
        
        conflicts = await self.check_conflicts(
            reservation_data.cluster_id,
            reservation_data.start_time,
            reservation_data.end_time
        )
        if conflicts:
            raise ValueError(f"Time slot conflicts with existing reservation: {conflicts[0].title}")
        
        reservation = Reservation(
            cluster_id=reservation_data.cluster_id,
            cluster_name=cluster.name,  # Store cluster name for historical records
            title=reservation_data.title,
            description=reservation_data.description,
            user_name=reservation_data.user_name,
            user_email=reservation_data.user_email,
            team=reservation_data.team,
            start_time=reservation_data.start_time,
            end_time=reservation_data.end_time,
            purpose=reservation_data.purpose,
            notes=reservation_data.notes,
            color=reservation_data.color,
            status=ReservationStatus.SCHEDULED
        )
        
        self.db.add(reservation)
        await self.db.commit()
        await self.db.refresh(reservation)
        
        return reservation

    async def get_reservation(self, reservation_id: str) -> Optional[Reservation]:
        result = await self.db.execute(
            select(Reservation)
            .options(selectinload(Reservation.cluster))
            .where(Reservation.id == reservation_id)
        )
        return result.scalar_one_or_none()

    async def get_reservations(
        self,
        skip: int = 0,
        limit: int = 100,
        cluster_id: Optional[str] = None,
        user_name: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: Optional[ReservationStatus] = None
    ) -> tuple[List[Reservation], int]:
        query = select(Reservation).options(selectinload(Reservation.cluster))
        
        conditions = []
        if cluster_id:
            conditions.append(Reservation.cluster_id == cluster_id)
        if user_name:
            conditions.append(Reservation.user_name == user_name)
        if start_date:
            conditions.append(Reservation.end_time >= start_date)
        if end_date:
            conditions.append(Reservation.start_time <= end_date)
        if status:
            conditions.append(Reservation.status == status)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(Reservation.start_time).offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        reservations = result.scalars().all()
        
        count_query = select(Reservation)
        if conditions:
            count_query = count_query.where(and_(*conditions))
        count_result = await self.db.execute(count_query)
        total = len(count_result.scalars().all())
        
        return list(reservations), total

    async def update_reservation(
        self,
        reservation_id: str,
        reservation_data: ReservationUpdate
    ) -> Optional[Reservation]:
        reservation = await self.get_reservation(reservation_id)
        if not reservation:
            return None
        
        update_data = reservation_data.model_dump(exclude_unset=True)
        
        if 'start_time' in update_data or 'end_time' in update_data:
            new_start = update_data.get('start_time', reservation.start_time)
            new_end = update_data.get('end_time', reservation.end_time)
            
            conflicts = await self.check_conflicts(
                reservation.cluster_id,
                new_start,
                new_end,
                exclude_id=reservation_id
            )
            if conflicts:
                raise ValueError(f"Time slot conflicts with existing reservation: {conflicts[0].title}")
        
        for key, value in update_data.items():
            setattr(reservation, key, value)
        
        reservation.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(reservation)
        
        return reservation

    async def delete_reservation(self, reservation_id: str) -> bool:
        reservation = await self.get_reservation(reservation_id)
        if not reservation:
            return False
        
        await self.db.delete(reservation)
        await self.db.commit()
        
        return True

    async def cancel_reservation(self, reservation_id: str) -> Optional[Reservation]:
        reservation = await self.get_reservation(reservation_id)
        if not reservation:
            return None
        
        reservation.status = ReservationStatus.CANCELLED
        reservation.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(reservation)
        
        return reservation

    async def check_conflicts(
        self,
        cluster_id: str,
        start_time: datetime,
        end_time: datetime,
        exclude_id: Optional[str] = None
    ) -> List[Reservation]:
        query = select(Reservation).where(
            and_(
                Reservation.cluster_id == cluster_id,
                Reservation.status.in_([ReservationStatus.SCHEDULED, ReservationStatus.ACTIVE]),
                or_(
                    and_(
                        Reservation.start_time <= start_time,
                        Reservation.end_time > start_time
                    ),
                    and_(
                        Reservation.start_time < end_time,
                        Reservation.end_time >= end_time
                    ),
                    and_(
                        Reservation.start_time >= start_time,
                        Reservation.end_time <= end_time
                    )
                )
            )
        )
        
        if exclude_id:
            query = query.where(Reservation.id != exclude_id)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_calendar_events(
        self,
        start_date: datetime,
        end_date: datetime,
        cluster_id: Optional[str] = None
    ) -> List[CalendarEvent]:
        query = select(Reservation).options(
            selectinload(Reservation.cluster)
        ).where(
            and_(
                Reservation.start_time <= end_date,
                Reservation.end_time >= start_date,
                Reservation.status.in_([
                    ReservationStatus.SCHEDULED,
                    ReservationStatus.ACTIVE
                ])
            )
        )
        
        if cluster_id:
            query = query.where(Reservation.cluster_id == cluster_id)
        
        query = query.order_by(Reservation.start_time)
        
        result = await self.db.execute(query)
        reservations = result.scalars().all()
        
        events = []
        for r in reservations:
            # Use stored cluster_name, or get from relationship, or mark as removed
            cluster_name = r.cluster_name or (r.cluster.name if r.cluster else "[Cluster Removed]")
            events.append(CalendarEvent(
                id=r.id,
                title=r.title,
                start=r.start_time,
                end=r.end_time,
                cluster_id=r.cluster_id,
                cluster_name=cluster_name,
                user_name=r.user_name,
                team=r.team,
                status=r.status,
                color=r.color,
                description=r.description
            ))
        
        return events

    async def get_current_user(self, cluster_id: str) -> Optional[Reservation]:
        now = datetime.utcnow()
        result = await self.db.execute(
            select(Reservation).where(
                and_(
                    Reservation.cluster_id == cluster_id,
                    Reservation.start_time <= now,
                    Reservation.end_time > now,
                    Reservation.status.in_([
                        ReservationStatus.SCHEDULED,
                        ReservationStatus.ACTIVE
                    ])
                )
            )
        )
        return result.scalar_one_or_none()

    async def update_reservation_statuses(self):
        now = datetime.utcnow()
        
        await self.db.execute(
            select(Reservation).where(
                and_(
                    Reservation.status == ReservationStatus.SCHEDULED,
                    Reservation.start_time <= now,
                    Reservation.end_time > now
                )
            )
        )
        scheduled_to_active = await self.db.execute(
            select(Reservation).where(
                and_(
                    Reservation.status == ReservationStatus.SCHEDULED,
                    Reservation.start_time <= now,
                    Reservation.end_time > now
                )
            )
        )
        for reservation in scheduled_to_active.scalars():
            reservation.status = ReservationStatus.ACTIVE
        
        active_to_complete = await self.db.execute(
            select(Reservation).where(
                and_(
                    Reservation.status.in_([
                        ReservationStatus.SCHEDULED,
                        ReservationStatus.ACTIVE
                    ]),
                    Reservation.end_time <= now
                )
            )
        )
        for reservation in active_to_complete.scalars():
            reservation.status = ReservationStatus.COMPLETED
        
        await self.db.commit()
