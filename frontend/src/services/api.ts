import axios from 'axios'
import type { 
  Cluster, 
  ClusterStatus, 
  ClusterListResponse, 
  Reservation, 
  ReservationListResponse,
  CalendarEvent 
} from '../types'

const api = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Interceptor to extract error messages from API responses
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Extract the detail message from FastAPI error responses
    const detail = error.response?.data?.detail
    if (detail) {
      error.message = detail
    }
    return Promise.reject(error)
  }
)

export const clusterApi = {
  list: async (activeOnly = false): Promise<ClusterListResponse> => {
    const { data } = await api.get('/clusters', { params: { active_only: activeOnly } })
    return data
  },

  get: async (id: string): Promise<Cluster> => {
    const { data } = await api.get(`/clusters/${id}`)
    return data
  },

  create: async (cluster: { 
    name: string; 
    description?: string; 
    kubeconfig_content?: string; 
    api_server_url?: string;
    username?: string;
    password?: string;
    tags?: string[] 
  }): Promise<Cluster> => {
    const { data } = await api.post('/clusters', cluster)
    return data
  },

  update: async (id: string, cluster: Partial<Cluster>): Promise<Cluster> => {
    const { data } = await api.put(`/clusters/${id}`, cluster)
    return data
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/clusters/${id}`)
  },

  getStatus: async (id: string): Promise<ClusterStatus> => {
    const { data } = await api.get(`/clusters/${id}/status`)
    return data
  },

  refreshStatus: async (id: string): Promise<ClusterStatus> => {
    const { data } = await api.post(`/clusters/${id}/refresh`)
    return data
  },

  uploadKubeconfig: async (id: string, file: File): Promise<Cluster> => {
    const formData = new FormData()
    formData.append('file', file)
    const { data } = await api.post(`/clusters/${id}/kubeconfig`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return data
  },

  validateKubeconfig: async (file: File): Promise<{ valid: boolean; contexts?: string[]; api_server?: string }> => {
    const formData = new FormData()
    formData.append('file', file)
    const { data } = await api.post('/clusters/validate-kubeconfig', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return data
  },

  loginWithCredentials: async (id: string, credentials: { api_server_url: string; username: string; password: string }): Promise<Cluster> => {
    const { data } = await api.post(`/clusters/${id}/login`, credentials)
    return data
  },

  testCredentials: async (credentials: { api_server_url: string; username: string; password: string }): Promise<{ valid: boolean; api_server: string; auth_type: string }> => {
    const { data } = await api.post('/clusters/test-credentials', credentials)
    return data
  },

  getTopology: async (id: string): Promise<ClusterTopology> => {
    const { data } = await api.get(`/clusters/${id}/topology`)
    return data
  },

  getOcpDetails: async (id: string): Promise<OcpDetails> => {
    const { data } = await api.get(`/clusters/${id}/ocp-details`)
    return data
  },

  getOperators: async (id: string): Promise<{ operators: Operator[]; total: number }> => {
    const { data } = await api.get(`/clusters/${id}/operators`)
    return data
  },

  getWorkloads: async (id: string, namespace?: string): Promise<WorkloadsResponse> => {
    const { data } = await api.get(`/clusters/${id}/workloads`, { params: { namespace } })
    return data
  },
}

export const reservationApi = {
  list: async (params?: {
    cluster_id?: string
    user_name?: string
    start_date?: string
    end_date?: string
    status?: string
  }): Promise<ReservationListResponse> => {
    const { data } = await api.get('/reservations', { params })
    return data
  },

  get: async (id: string): Promise<Reservation> => {
    const { data } = await api.get(`/reservations/${id}`)
    return data
  },

  create: async (reservation: Omit<Reservation, 'id' | 'status' | 'created_at' | 'updated_at'>): Promise<Reservation> => {
    const { data } = await api.post('/reservations', reservation)
    return data
  },

  update: async (id: string, reservation: Partial<Reservation>): Promise<Reservation> => {
    const { data } = await api.put(`/reservations/${id}`, reservation)
    return data
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/reservations/${id}`)
  },

  cancel: async (id: string): Promise<Reservation> => {
    const { data } = await api.post(`/reservations/${id}/cancel`)
    return data
  },

  getCalendarEvents: async (startDate: string, endDate: string, clusterId?: string): Promise<CalendarEvent[]> => {
    const { data } = await api.get('/reservations/calendar', {
      params: { start_date: startDate, end_date: endDate, cluster_id: clusterId },
    })
    return data
  },

  getCurrentUser: async (clusterId: string): Promise<{ occupied: boolean; current_user?: { user_name: string; team?: string; title: string; start_time: string; end_time: string } }> => {
    const { data } = await api.get(`/reservations/cluster/${clusterId}/current`)
    return data
  },
}

export default api
