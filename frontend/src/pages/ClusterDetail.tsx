import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import {
  ArrowLeftIcon,
  ArrowPathIcon,
  CloudArrowUpIcon,
  ServerStackIcon,
  CpuChipIcon,
  CircleStackIcon,
} from '@heroicons/react/24/outline'
import { useDropzone } from 'react-dropzone'
import {
  useCluster,
  useClusterStatus,
  useRefreshClusterStatus,
  useUploadKubeconfig,
} from '../hooks/useClusters'
import { useCurrentClusterUser } from '../hooks/useReservations'
import { format } from 'date-fns'

export default function ClusterDetail() {
  const { id } = useParams<{ id: string }>()
  const [showUpload, setShowUpload] = useState(false)

  const { data: cluster, isLoading: clusterLoading } = useCluster(id!)
  const { data: status, isLoading: statusLoading } = useClusterStatus(id!)
  const { data: currentUser } = useCurrentClusterUser(id!)
  const refreshStatus = useRefreshClusterStatus()
  const uploadKubeconfig = useUploadKubeconfig()

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: { 'application/x-yaml': ['.yaml', '.yml'], 'text/plain': ['.kubeconfig'] },
    multiple: false,
    onDrop: async (files) => {
      if (files[0] && id) {
        await uploadKubeconfig.mutateAsync({ id, file: files[0] })
        setShowUpload(false)
      }
    },
  })

  if (clusterLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <ArrowPathIcon className="h-8 w-8 animate-spin text-gray-400" />
      </div>
    )
  }

  if (!cluster) {
    return (
      <div className="text-center py-12">
        <ServerStackIcon className="h-16 w-16 mx-auto text-gray-300" />
        <h3 className="mt-4 text-lg font-medium text-gray-900">Cluster not found</h3>
        <Link to="/clusters" className="mt-4 inline-block text-primary-600 hover:text-primary-700">
          ← Back to clusters
        </Link>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link
          to="/clusters"
          className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
        >
          <ArrowLeftIcon className="h-5 w-5 text-gray-500" />
        </Link>
        <div className="flex-1">
          <h1 className="text-2xl font-bold text-gray-900">{cluster.name}</h1>
          {cluster.description && (
            <p className="mt-1 text-sm text-gray-500">{cluster.description}</p>
          )}
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => setShowUpload(!showUpload)}
            className="btn-secondary"
          >
            <CloudArrowUpIcon className="h-4 w-4 mr-2" />
            Upload Kubeconfig
          </button>
          <button
            onClick={() => refreshStatus.mutate(id!)}
            disabled={refreshStatus.isPending}
            className="btn-primary"
          >
            <ArrowPathIcon
              className={`h-4 w-4 mr-2 ${refreshStatus.isPending ? 'animate-spin' : ''}`}
            />
            Refresh Status
          </button>
        </div>
      </div>

      {showUpload && (
        <div className="card p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Upload New Kubeconfig</h3>
          <div
            {...getRootProps()}
            className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors ${
              isDragActive
                ? 'border-primary-500 bg-primary-50'
                : 'border-gray-300 hover:border-gray-400'
            }`}
          >
            <input {...getInputProps()} />
            <CloudArrowUpIcon className="h-12 w-12 mx-auto text-gray-400" />
            <p className="mt-2 text-sm text-gray-600">
              Drop your kubeconfig file here, or click to browse
            </p>
            {uploadKubeconfig.isPending && (
              <p className="mt-2 text-sm text-primary-600">Uploading...</p>
            )}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="card p-6">
          <div className="flex items-center gap-3">
            <div
              className={`h-12 w-12 rounded-xl flex items-center justify-center ${
                cluster.status === 'healthy'
                  ? 'bg-green-100'
                  : cluster.status === 'error'
                  ? 'bg-red-100'
                  : 'bg-yellow-100'
              }`}
            >
              <ServerStackIcon
                className={`h-6 w-6 ${
                  cluster.status === 'healthy'
                    ? 'text-green-600'
                    : cluster.status === 'error'
                    ? 'text-red-600'
                    : 'text-yellow-600'
                }`}
              />
            </div>
            <div>
              <p className="text-sm text-gray-500">Status</p>
              <p className="text-xl font-semibold text-gray-900 capitalize">{cluster.status}</p>
            </div>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center gap-3">
            <div className="h-12 w-12 rounded-xl bg-blue-100 flex items-center justify-center">
              <CircleStackIcon className="h-6 w-6 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Nodes</p>
              <p className="text-xl font-semibold text-gray-900">{cluster.node_count || 'N/A'}</p>
            </div>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center gap-3">
            <div className="h-12 w-12 rounded-xl bg-purple-100 flex items-center justify-center">
              <CpuChipIcon className="h-6 w-6 text-purple-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">GPUs</p>
              <p className="text-xl font-semibold text-gray-900">{cluster.gpu_count || '0'}</p>
            </div>
          </div>
        </div>
      </div>

      {currentUser?.occupied && currentUser.current_user && (
        <div className="card p-6 border-l-4 border-l-orange-500">
          <h3 className="font-semibold text-gray-900">Currently Reserved</h3>
          <div className="mt-2 grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-gray-500">User</p>
              <p className="font-medium text-gray-900">{currentUser.current_user.user_name}</p>
            </div>
            <div>
              <p className="text-gray-500">Purpose</p>
              <p className="font-medium text-gray-900">{currentUser.current_user.title}</p>
            </div>
            <div>
              <p className="text-gray-500">Started</p>
              <p className="font-medium text-gray-900">
                {format(new Date(currentUser.current_user.start_time), 'MMM d, h:mm a')}
              </p>
            </div>
            <div>
              <p className="text-gray-500">Ends</p>
              <p className="font-medium text-gray-900">
                {format(new Date(currentUser.current_user.end_time), 'MMM d, h:mm a')}
              </p>
            </div>
          </div>
        </div>
      )}

      <div className="card">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Cluster Details</h2>
        </div>
        <div className="p-6">
          <dl className="grid grid-cols-1 gap-6 sm:grid-cols-2">
            <div>
              <dt className="text-sm text-gray-500">Cluster ID</dt>
              <dd className="mt-1 font-mono text-sm text-gray-900">{cluster.id}</dd>
            </div>
            <div>
              <dt className="text-sm text-gray-500">Version</dt>
              <dd className="mt-1 text-sm text-gray-900">{cluster.cluster_version || 'N/A'}</dd>
            </div>
            <div className="sm:col-span-2">
              <dt className="text-sm text-gray-500">API Server</dt>
              <dd className="mt-1 font-mono text-sm text-gray-900 break-all">
                {cluster.api_server_url || 'Not configured'}
              </dd>
            </div>
            <div>
              <dt className="text-sm text-gray-500">Last Health Check</dt>
              <dd className="mt-1 text-sm text-gray-900">
                {cluster.last_health_check
                  ? format(new Date(cluster.last_health_check), 'MMM d, yyyy h:mm:ss a')
                  : 'Never'}
              </dd>
            </div>
            <div>
              <dt className="text-sm text-gray-500">Created</dt>
              <dd className="mt-1 text-sm text-gray-900">
                {format(new Date(cluster.created_at), 'MMM d, yyyy h:mm a')}
              </dd>
            </div>
          </dl>
        </div>
      </div>

      {status?.nodes && status.nodes.length > 0 && (
        <div className="card">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">Nodes</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Roles
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    CPU
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Memory
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    GPU
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {status.nodes.map((node) => (
                  <tr key={node.name} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap font-mono text-sm text-gray-900">
                      {node.name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`badge ${
                          node.status === 'Ready' ? 'badge-success' : 'badge-error'
                        }`}
                      >
                        {node.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {node.roles.join(', ')}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {node.cpu}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {node.memory}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {node.gpu}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {status?.resource_usage && (
        <div className="card">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">Resource Summary</h2>
          </div>
          <div className="p-6 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-6">
            <div>
              <p className="text-sm text-gray-500">Total CPU Cores</p>
              <p className="text-2xl font-semibold text-gray-900">
                {status.resource_usage.total_cpu_cores}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Total Memory</p>
              <p className="text-2xl font-semibold text-gray-900">
                {status.resource_usage.total_memory_gb} GB
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Total GPUs</p>
              <p className="text-2xl font-semibold text-gray-900">
                {status.resource_usage.total_gpus}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Running Pods</p>
              <p className="text-2xl font-semibold text-gray-900">
                {status.resource_usage.running_pods}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Total Pods</p>
              <p className="text-2xl font-semibold text-gray-900">
                {status.resource_usage.total_pods}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Total Nodes</p>
              <p className="text-2xl font-semibold text-gray-900">
                {status.resource_usage.total_nodes}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
