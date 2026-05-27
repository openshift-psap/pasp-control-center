import { Fragment, useState, useCallback } from 'react'
import { Dialog, Transition } from '@headlessui/react'
import { FireIcon, CloudArrowUpIcon } from '@heroicons/react/24/outline'
import { useDropzone } from 'react-dropzone'
import { useConnectHearth } from '../hooks/useHearth'

interface HearthConnectModalProps {
  open: boolean
  onClose: () => void
}

export default function HearthConnectModal({ open, onClose }: HearthConnectModalProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const connectHearth = useConnectHearth()

  const onDrop = useCallback((accepted: File[]) => {
    if (accepted.length > 0) {
      setSelectedFile(accepted[0])
    }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/x-yaml': ['.yaml', '.yml'],
      'text/plain': ['.kubeconfig', '.conf'],
      'application/octet-stream': ['.kubeconfig'],
    },
    multiple: false,
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedFile) return

    try {
      await connectHearth.mutateAsync(selectedFile)
      setSelectedFile(null)
      onClose()
    } catch {
      // error toast handled by the mutation hook
    }
  }

  const handleClose = () => {
    setSelectedFile(null)
    onClose()
  }

  return (
    <Transition.Root show={open} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={handleClose}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-gray-500/75 transition-opacity" />
        </Transition.Child>

        <div className="fixed inset-0 z-10 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 translate-y-4 sm:scale-95"
              enterTo="opacity-100 translate-y-0 sm:scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 translate-y-0 sm:scale-100"
              leaveTo="opacity-0 translate-y-4 sm:scale-95"
            >
              <Dialog.Panel className="relative w-full max-w-md rounded-2xl bg-white p-6 shadow-xl">
                <div className="flex flex-col items-center mb-6">
                  <div className="h-12 w-12 rounded-full bg-orange-100 flex items-center justify-center mb-3">
                    <FireIcon className="h-6 w-6 text-orange-600" />
                  </div>
                  <Dialog.Title className="text-lg font-semibold text-gray-900">
                    Connect to Hearth
                  </Dialog.Title>
                  <p className="mt-1 text-sm text-gray-500 text-center">
                    Upload a kubeconfig for the management cluster where Hearth is running
                  </p>
                </div>

                <form onSubmit={handleSubmit} className="space-y-4">
                  <div
                    {...getRootProps()}
                    className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-colors ${
                      isDragActive
                        ? 'border-orange-500 bg-orange-50'
                        : selectedFile
                        ? 'border-green-400 bg-green-50'
                        : 'border-gray-300 hover:border-gray-400'
                    }`}
                  >
                    <input {...getInputProps()} />
                    <CloudArrowUpIcon className={`h-10 w-10 mx-auto ${
                      selectedFile ? 'text-green-500' : 'text-gray-400'
                    }`} />
                    {selectedFile ? (
                      <div className="mt-2">
                        <p className="text-sm font-medium text-green-700">{selectedFile.name}</p>
                        <p className="text-xs text-gray-500 mt-1">Click or drop to replace</p>
                      </div>
                    ) : (
                      <div className="mt-2">
                        <p className="text-sm text-gray-600">Drop your kubeconfig here, or click to browse</p>
                        <p className="text-xs text-gray-400 mt-1">
                          Needs read access to FournosCluster CRDs in the hearth namespace
                        </p>
                      </div>
                    )}
                  </div>

                  <div className="rounded-lg bg-gray-50 p-3 text-xs text-gray-500 space-y-1">
                    <p className="font-medium text-gray-700">What this does:</p>
                    <ul className="list-disc list-inside space-y-0.5">
                      <li>Connects to the psap-automation management cluster</li>
                      <li>Reads FournosCluster CRDs managed by the Hearth operator</li>
                      <li>Surfaces GPU hardware discovery, lock status, and Kueue quotas</li>
                    </ul>
                  </div>

                  <div className="flex gap-3">
                    <button
                      type="button"
                      onClick={handleClose}
                      className="flex-1 rounded-lg border border-gray-300 px-4 py-2.5 text-sm font-semibold text-gray-700 hover:bg-gray-50 transition-colors"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={!selectedFile || connectHearth.isPending}
                      className="flex-1 rounded-lg bg-orange-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-orange-500 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:ring-offset-2 disabled:opacity-50 transition-colors"
                    >
                      {connectHearth.isPending ? 'Connecting...' : 'Connect'}
                    </button>
                  </div>
                </form>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition.Root>
  )
}
