from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from app.models.cluster import Cluster, CLUSTER_COLORS
from app.schemas.cluster import ClusterCreate, ClusterUpdate, ClusterStatus
from app.services.kubernetes_service import KubernetesService
from app.core.config import settings

logger = logging.getLogger(__name__)


def get_next_color(existing_count: int) -> str:
    """Get the next color from the palette based on existing cluster count."""
    return CLUSTER_COLORS[existing_count % len(CLUSTER_COLORS)]


class ClusterService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_cluster(self, cluster_data: ClusterCreate) -> Cluster:
        kubeconfig_path = None
        api_server_url = None
        
        if cluster_data.kubeconfig_content:
            # Method 1: Kubeconfig file provided
            parsed = KubernetesService.parse_kubeconfig(cluster_data.kubeconfig_content)
            if not parsed.get("valid"):
                raise ValueError(f"Invalid kubeconfig: {parsed.get('error')}")
            
            kubeconfig_path = KubernetesService.save_kubeconfig(
                cluster_data.kubeconfig_content,
                settings.KUBECONFIG_STORAGE_PATH,
                cluster_data.name
            )
            api_server_url = parsed.get("api_server")
        
        elif cluster_data.api_server_url and cluster_data.username and cluster_data.password:
            # Method 2: Login with credentials (kubeadmin)
            login_result = await KubernetesService.login_with_credentials(
                api_server=cluster_data.api_server_url,
                username=cluster_data.username,
                password=cluster_data.password,
                storage_path=settings.KUBECONFIG_STORAGE_PATH,
                cluster_name=cluster_data.name
            )
            
            if not login_result.get("success"):
                raise ValueError(f"Login failed: {login_result.get('error')}")
            
            kubeconfig_path = login_result.get("kubeconfig_path")
            api_server_url = login_result.get("api_server")
        
        # Auto-assign color based on existing cluster count
        count_result = await self.db.execute(select(Cluster))
        existing_count = len(count_result.scalars().all())
        cluster_color = get_next_color(existing_count)
        
        cluster = Cluster(
            name=cluster_data.name,
            description=cluster_data.description,
            kubeconfig_path=kubeconfig_path or "",
            api_server_url=api_server_url,
            tags=cluster_data.tags,
            color=cluster_color,
            status="pending"
        )
        
        self.db.add(cluster)
        await self.db.commit()
        await self.db.refresh(cluster)
        
        if kubeconfig_path:
            await self.refresh_cluster_status(cluster.id)
            await self.db.refresh(cluster)
        
        return cluster

    async def get_cluster(self, cluster_id: str) -> Optional[Cluster]:
        result = await self.db.execute(
            select(Cluster).where(Cluster.id == cluster_id)
        )
        return result.scalar_one_or_none()

    async def get_cluster_by_name(self, name: str) -> Optional[Cluster]:
        result = await self.db.execute(
            select(Cluster).where(Cluster.name == name)
        )
        return result.scalar_one_or_none()

    async def get_clusters(
        self,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = False
    ) -> tuple[List[Cluster], int]:
        query = select(Cluster)
        
        if active_only:
            query = query.where(Cluster.is_active == True)
        
        query = query.order_by(Cluster.name).offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        clusters = result.scalars().all()
        
        count_query = select(Cluster)
        if active_only:
            count_query = count_query.where(Cluster.is_active == True)
        count_result = await self.db.execute(count_query)
        total = len(count_result.scalars().all())
        
        return list(clusters), total

    async def update_cluster(
        self,
        cluster_id: str,
        cluster_data: ClusterUpdate
    ) -> Optional[Cluster]:
        cluster = await self.get_cluster(cluster_id)
        if not cluster:
            return None
        
        update_data = cluster_data.model_dump(exclude_unset=True)
        
        for key, value in update_data.items():
            setattr(cluster, key, value)
        
        cluster.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(cluster)
        
        return cluster

    async def delete_cluster(self, cluster_id: str) -> bool:
        from app.models.reservation import Reservation, ReservationStatus
        
        cluster = await self.get_cluster(cluster_id)
        if not cluster:
            return False
        
        # Update all reservations: preserve cluster name and cancel active/scheduled ones
        result = await self.db.execute(
            select(Reservation).where(Reservation.cluster_id == cluster_id)
        )
        reservations = result.scalars().all()
        
        for reservation in reservations:
            # Preserve the cluster name for historical records
            reservation.cluster_name = cluster.name
            reservation.cluster_id = None
            
            # Cancel any scheduled or active reservations
            if reservation.status in [ReservationStatus.SCHEDULED, ReservationStatus.ACTIVE]:
                reservation.status = ReservationStatus.CANCELLED
                reservation.notes = (reservation.notes or "") + f"\n[Auto-cancelled: Cluster '{cluster.name}' was removed from Control Center]"
        
        await self.db.delete(cluster)
        await self.db.commit()
        
        return True

    async def refresh_cluster_status(self, cluster_id: str) -> Optional[ClusterStatus]:
        cluster = await self.get_cluster(cluster_id)
        if not cluster or not cluster.kubeconfig_path:
            return None
        
        try:
            k8s_service = KubernetesService(cluster.kubeconfig_path)
            cluster_info = k8s_service.get_cluster_info()
            
            cluster.status = cluster_info.get("status", "unknown")
            cluster.node_count = cluster_info.get("node_count")
            cluster.gpu_count = cluster_info.get("gpu_count")
            cluster.cluster_version = cluster_info.get("cluster_version")
            cluster.api_server_url = cluster_info.get("api_server") or cluster.api_server_url
            cluster.last_health_check = datetime.utcnow()
            
            await self.db.commit()
            await self.db.refresh(cluster)
            
            namespaces = k8s_service.get_namespaces()
            resource_usage = k8s_service.get_resource_usage()
            
            return ClusterStatus(
                status=cluster.status,
                api_server_url=cluster.api_server_url,
                node_count=cluster.node_count,
                gpu_count=cluster.gpu_count,
                cluster_version=cluster.cluster_version,
                last_health_check=cluster.last_health_check,
                nodes=cluster_info.get("nodes"),
                namespaces=namespaces,
                resource_usage=resource_usage
            )
        except Exception as e:
            logger.error(f"Error refreshing cluster status: {e}")
            cluster.status = "error"
            cluster.last_health_check = datetime.utcnow()
            await self.db.commit()
            
            return ClusterStatus(
                status="error",
                last_health_check=cluster.last_health_check
            )

    async def get_cluster_status(self, cluster_id: str) -> Optional[ClusterStatus]:
        cluster = await self.get_cluster(cluster_id)
        if not cluster:
            return None
        
        return ClusterStatus(
            status=cluster.status,
            api_server_url=cluster.api_server_url,
            node_count=cluster.node_count,
            gpu_count=cluster.gpu_count,
            cluster_version=cluster.cluster_version,
            last_health_check=cluster.last_health_check
        )

    async def upload_kubeconfig(
        self,
        cluster_id: str,
        kubeconfig_content: str
    ) -> Optional[Cluster]:
        cluster = await self.get_cluster(cluster_id)
        if not cluster:
            return None
        
        parsed = KubernetesService.parse_kubeconfig(kubeconfig_content)
        if not parsed.get("valid"):
            raise ValueError(f"Invalid kubeconfig: {parsed.get('error')}")
        
        kubeconfig_path = KubernetesService.save_kubeconfig(
            kubeconfig_content,
            settings.KUBECONFIG_STORAGE_PATH,
            cluster.name
        )
        
        cluster.kubeconfig_path = kubeconfig_path
        cluster.api_server_url = parsed.get("api_server")
        cluster.status = "pending"
        
        await self.db.commit()
        await self.db.refresh(cluster)
        
        await self.refresh_cluster_status(cluster_id)
        await self.db.refresh(cluster)
        
        return cluster
