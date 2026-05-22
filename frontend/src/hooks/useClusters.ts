import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { clusterApi } from '../services/api'
import type { Cluster, ClusterStatus, ClusterTopology, OcpDetails, Operator, WorkloadsResponse } from '../types'
import toast from 'react-hot-toast'

export function useClusters(activeOnly = false) {
  return useQuery({
    queryKey: ['clusters', { activeOnly }],
    queryFn: () => clusterApi.list(activeOnly),
  })
}

export function useCluster(id: string) {
  return useQuery({
    queryKey: ['cluster', id],
    queryFn: () => clusterApi.get(id),
    enabled: !!id,
  })
}

export function useClusterStatus(id: string) {
  return useQuery({
    queryKey: ['clusterStatus', id],
    queryFn: () => clusterApi.getStatus(id),
    enabled: !!id,
    refetchInterval: 60000,
  })
}

export function useCreateCluster() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: clusterApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clusters'] })
      toast.success('Cluster created successfully')
    },
    onError: (error: Error) => {
      toast.error(`Failed to create cluster: ${error.message}`)
    },
  })
}

export function useUpdateCluster() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Cluster> }) =>
      clusterApi.update(id, data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['clusters'] })
      queryClient.invalidateQueries({ queryKey: ['cluster', data.id] })
      toast.success('Cluster updated successfully')
    },
    onError: (error: Error) => {
      toast.error(`Failed to update cluster: ${error.message}`)
    },
  })
}

export function useDeleteCluster() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: clusterApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clusters'] })
      toast.success('Cluster removed from Control Center')
    },
    onError: (error: Error) => {
      toast.error(`Failed to remove cluster: ${error.message}`)
    },
  })
}

export function useRefreshClusterStatus() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: clusterApi.refreshStatus,
    onSuccess: (data, id) => {
      queryClient.invalidateQueries({ queryKey: ['clusterStatus', id] })
      queryClient.invalidateQueries({ queryKey: ['clusters'] })
      toast.success('Cluster status refreshed')
    },
    onError: (error: Error) => {
      toast.error(`Failed to refresh status: ${error.message}`)
    },
  })
}

export function useUploadKubeconfig() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, file }: { id: string; file: File }) =>
      clusterApi.uploadKubeconfig(id, file),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['clusters'] })
      queryClient.invalidateQueries({ queryKey: ['cluster', data.id] })
      toast.success('Kubeconfig uploaded successfully')
    },
    onError: (error: Error) => {
      toast.error(`Failed to upload kubeconfig: ${error.message}`)
    },
  })
}

export function useClusterTopology(id: string) {
  return useQuery({
    queryKey: ['clusterTopology', id],
    queryFn: () => clusterApi.getTopology(id),
    enabled: !!id,
    staleTime: 60000,
  })
}

export function useOcpDetails(id: string) {
  return useQuery({
    queryKey: ['ocpDetails', id],
    queryFn: () => clusterApi.getOcpDetails(id),
    enabled: !!id,
    staleTime: 60000,
  })
}

export function useClusterOperators(id: string) {
  return useQuery({
    queryKey: ['clusterOperators', id],
    queryFn: () => clusterApi.getOperators(id),
    enabled: !!id,
    staleTime: 60000,
  })
}

export function useClusterWorkloads(id: string, namespace?: string) {
  return useQuery({
    queryKey: ['clusterWorkloads', id, namespace],
    queryFn: () => clusterApi.getWorkloads(id, namespace),
    enabled: !!id,
    staleTime: 30000,
  })
}
