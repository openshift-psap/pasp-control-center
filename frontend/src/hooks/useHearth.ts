import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { hearthApi } from '../services/api'
import toast from 'react-hot-toast'

export function useHearthStatus() {
  return useQuery({
    queryKey: ['hearthStatus'],
    queryFn: hearthApi.getStatus,
    refetchInterval: 60000,
    retry: 1,
  })
}

export function useHearthClusters() {
  return useQuery({
    queryKey: ['hearthClusters'],
    queryFn: hearthApi.listClusters,
    refetchInterval: 30000,
    retry: 1,
  })
}

export function useHearthCluster(name: string) {
  return useQuery({
    queryKey: ['hearthCluster', name],
    queryFn: () => hearthApi.getCluster(name),
    enabled: !!name,
    refetchInterval: 30000,
    retry: 1,
  })
}

export function useConnectHearth() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (file: File) => hearthApi.connect(file),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['hearthStatus'] })
      queryClient.invalidateQueries({ queryKey: ['hearthClusters'] })
      toast.success(data.message)
    },
    onError: (error: Error) => {
      toast.error(`Failed to connect: ${error.message}`)
    },
  })
}

export function useDisconnectHearth() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => hearthApi.disconnect(),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['hearthStatus'] })
      queryClient.invalidateQueries({ queryKey: ['hearthClusters'] })
      toast.success(data.message)
    },
    onError: (error: Error) => {
      toast.error(`Failed to disconnect: ${error.message}`)
    },
  })
}
