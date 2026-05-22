from sqlalchemy import Column, String, DateTime, Boolean, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base


class Cluster(Base):
    __tablename__ = "clusters"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    api_server_url = Column(String(512), nullable=True)
    kubeconfig_path = Column(String(512), nullable=False)
    
    status = Column(String(50), default="unknown")
    last_health_check = Column(DateTime, nullable=True)
    
    node_count = Column(String(20), nullable=True)
    gpu_count = Column(String(20), nullable=True)
    cluster_version = Column(String(50), nullable=True)
    
    metadata_info = Column(JSON, nullable=True)
    tags = Column(JSON, nullable=True)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    reservations = relationship("Reservation", back_populates="cluster", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Cluster(name={self.name}, status={self.status})>"
