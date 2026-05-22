export interface Cluster {
  id: string
  name: string
  description?: string
  api_server_url?: string
  status: string
  last_health_check?: string
  node_count?: string
  gpu_count?: string
  cluster_version?: string
  metadata_info?: Record<string, unknown>
  tags?: string[]
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface ClusterStatus {
  status: string
  api_server_url?: string
  node_count?: string
  gpu_count?: string
  cluster_version?: string
  last_health_check?: string
  nodes?: NodeInfo[]
  namespaces?: string[]
  resource_usage?: ResourceUsage
}

export interface NodeInfo {
  name: string
  status: string
  roles: string[]
  cpu: string
  memory: string
  gpu: string
}

export interface ResourceUsage {
  total_cpu_cores: number
  total_memory_gb: number
  total_gpus: number
  running_pods: number
  total_pods: number
  total_nodes: number
}

export interface Reservation {
  id: string
  cluster_id: string
  cluster_name?: string
  title: string
  description?: string
  user_name: string
  user_email?: string
  team?: string
  start_time: string
  end_time: string
  purpose?: string
  notes?: string
  color: string
  status: 'scheduled' | 'active' | 'completed' | 'cancelled'
  created_at: string
  updated_at: string
}

export interface CalendarEvent {
  id: string
  title: string
  start: string
  end: string
  cluster_id: string
  cluster_name: string
  user_name: string
  team?: string
  status: string
  color: string
  description?: string
}

export interface ClusterListResponse {
  clusters: Cluster[]
  total: number
}

export interface ReservationListResponse {
  reservations: Reservation[]
  total: number
}
