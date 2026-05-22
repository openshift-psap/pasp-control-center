from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.core.database import Base


class ReservationStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Reservation(Base):
    __tablename__ = "reservations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    cluster_id = Column(String(36), ForeignKey("clusters.id"), nullable=False, index=True)
    
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    user_name = Column(String(255), nullable=False, index=True)
    user_email = Column(String(255), nullable=True)
    team = Column(String(255), nullable=True)
    
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=False, index=True)
    
    status = Column(
        Enum(ReservationStatus),
        default=ReservationStatus.SCHEDULED,
        nullable=False
    )
    
    purpose = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    
    color = Column(String(7), default="#3B82F6")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    cluster = relationship("Cluster", back_populates="reservations")

    def __repr__(self):
        return f"<Reservation(title={self.title}, user={self.user_name}, cluster_id={self.cluster_id})>"
