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

export interface TopologyNode {
  name: string
  status: string
  roles: string[]
  cpu: string
  memory: string
  memory_gb: number
  gpu: string
  instance_type: string
  zone: string
  region: string
  pod_count: number
  os_image: string
  kernel_version: string
  container_runtime: string
  kubelet_version: string
  architecture: string
  internal_ip?: string
  external_ip?: string
}

export interface ClusterTopology {
  nodes: TopologyNode[]
  control_plane: TopologyNode[]
  workers: TopologyNode[]
  infra: TopologyNode[]
  total_nodes: number
  zones: string[]
}

export interface OcpDetails {
  cluster_version?: string
  cluster_id?: string
  platform?: string
  infrastructure?: string
  network_type?: string
  ingress_domain?: string
  update_available?: boolean
  available_updates?: string[]
  api_server_url?: string
  api_server_internal?: string
  cluster_network?: Array<{ cidr: string; hostPrefix: number }>
  service_network?: string[]
  conditions?: Array<{ type: string; status: string; message: string }>
}

export interface Operator {
  name: string
  namespace: string
  version?: string
  phase?: string
  display_name?: string
  description?: string
  provider?: string
}

export interface PodInfo {
  name: string
  namespace: string
  node?: string
  phase: string
  ip?: string
  containers: string[]
  restarts: number
  created?: string
}

export interface DeploymentInfo {
  name: string
  namespace: string
  replicas: number
  ready_replicas: number
  available_replicas: number
}

export interface WorkloadsResponse {
  pods: PodInfo[]
  deployments: DeploymentInfo[]
  pods_by_node: Record<string, PodInfo[]>
  total_pods: number
  total_deployments: number
}
