from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ClusterBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    tags: Optional[List[str]] = None


class ClusterCreate(ClusterBase):
    kubeconfig_content: Optional[str] = None
    # Alternative: Login with credentials (kubeadmin)
    api_server_url: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None


class ClusterUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None


class ClusterStatus(BaseModel):
    status: str
    api_server_url: Optional[str] = None
    node_count: Optional[str] = None
    gpu_count: Optional[str] = None
    cluster_version: Optional[str] = None
    last_health_check: Optional[datetime] = None
    nodes: Optional[List[Dict[str, Any]]] = None
    namespaces: Optional[List[str]] = None
    resource_usage: Optional[Dict[str, Any]] = None


class ClusterResponse(ClusterBase):
    id: str
    api_server_url: Optional[str] = None
    status: str
    color: str = "#3B82F6"
    last_health_check: Optional[datetime] = None
    node_count: Optional[str] = None
    gpu_count: Optional[str] = None
    cluster_version: Optional[str] = None
    metadata_info: Optional[Dict[str, Any]] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ClusterListResponse(BaseModel):
    clusters: List[ClusterResponse]
    total: int
