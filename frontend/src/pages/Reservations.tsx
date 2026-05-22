import { useState, Fragment } from 'react'
import { Link } from 'react-router-dom'
import { Dialog, Transition, Listbox } from '@headlessui/react'
import {
  PlusIcon,
  CalendarDaysIcon,
  XMarkIcon,
  ChevronUpDownIcon,
  CheckIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
} from '@heroicons/react/24/outline'
import { 
  format, 
  startOfWeek, 
  addDays, 
  isToday,
} from 'date-fns'
import {
  useReservations,
  useCreateReservation,
  useDeleteReservation,
  useCancelReservation,
} from '../hooks/useReservations'
import { useClusters } from '../hooks/useClusters'
import toast from 'react-hot-toast'
import clsx from 'clsx'

const COLORS = [
  { name: 'Blue', value: '#3B82F6' },
  { name: 'Green', value: '#10B981' },
  { name: 'Purple', value: '#8B5CF6' },
  { name: 'Red', value: '#EF4444' },
  { name: 'Orange', value: '#F97316' },
  { name: 'Teal', value: '#14B8A6' },
  { name: 'Pink', value: '#EC4899' },
]

const initialFormState = {
  cluster_id: '',
  title: '',
  description: '',
  user_name: '',
  user_email: '',
  team: '',
  start_time: '',
  end_time: '',
  purpose: '',
  color: '#3B82F6',
}

function WeekCalendar({ reservations }: { reservations: Array<{ start_time: string; end_time: string; color: string; title: string; status: string; user_name: string; cluster_name?: string }> }) {
  const [currentWeekStart, setCurrentWeekStart] = useState(startOfWeek(new Date()))
  
  // Get all days in the week
  const days: Date[] = []
  for (let i = 0; i < 7; i++) {
    days.push(addDays(currentWeekStart, i))
  }
  
  // Get reservations for a specific day
  const getReservationsForDay = (date: Date) => {
    return reservations.filter((r) => {
      if (r.status === 'cancelled') return false
      const start = new Date(r.start_time)
      const end = new Date(r.end_time)
      const dayStart = new Date(date.getFullYear(), date.getMonth(), date.getDate())
      const dayEnd = new Date(date.getFullYear(), date.getMonth(), date.getDate(), 23, 59, 59)
      return start <= dayEnd && end >= dayStart
    })
  }
  
  const prevWeek = () => setCurrentWeekStart(addDays(currentWeekStart, -7))
  const nextWeek = () => setCurrentWeekStart(addDays(currentWeekStart, 7))
  const goToToday = () => setCurrentWeekStart(startOfWeek(new Date()))
  
  return (
    <div className="card p-4">
      <div className="flex items-center justify-between mb-4">
        <button 
          onClick={prevWeek}
          className="p-1.5 hover:bg-gray-100 rounded-lg transition-colors"
        >
          <ChevronLeftIcon className="h-5 w-5 text-gray-600" />
        </button>
        <div className="text-center">
          <h3 className="font-semibold text-gray-900">
            {format(currentWeekStart, 'MMM d')} - {format(addDays(currentWeekStart, 6), 'MMM d, yyyy')}
          </h3>
          <button 
            onClick={goToToday}
            className="text-xs text-primary-600 hover:text-primary-700"
          >
            Go to today
          </button>
        </div>
        <button 
          onClick={nextWeek}
          className="p-1.5 hover:bg-gray-100 rounded-lg transition-colors"
        >
          <ChevronRightIcon className="h-5 w-5 text-gray-600" />
        </button>
      </div>
      
      <div className="grid grid-cols-7 gap-2">
        {days.map((date, idx) => {
          const dayReservations = getReservationsForDay(date)
          const isCurrentDay = isToday(date)
          
          return (
            <div
              key={idx}
              className={clsx(
                'flex flex-col rounded-lg border p-2 min-h-[100px]',
                isCurrentDay ? 'border-primary-300 bg-primary-50' : 'border-gray-200'
              )}
            >
              <div className="text-center mb-2">
                <div className="text-xs text-gray-500 uppercase">
                  {format(date, 'EEE')}
                </div>
                <div className={clsx(
                  'text-lg font-semibold',
                  isCurrentDay ? 'text-primary-700' : 'text-gray-900'
                )}>
                  {format(date, 'd')}
                </div>
              </div>
              <div className="flex-1 space-y-1 overflow-hidden">
                {dayReservations.slice(0, 3).map((r, i) => (
                  <div 
                    key={i}
                    className="text-xs p-1 rounded truncate"
                    style={{ backgroundColor: `${r.color}20`, borderLeft: `2px solid ${r.color}` }}
                    title={`${r.title} - ${r.user_name}`}
                  >
                    {r.title}
                  </div>
                ))}
                {dayReservations.length > 3 && (
                  <div className="text-xs text-gray-500 text-center">
                    +{dayReservations.length - 3} more
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>
      
      <div className="mt-4 pt-4 border-t border-gray-100">
        <Link 
          to="/calendar" 
          className="text-sm text-primary-600 hover:text-primary-700 flex items-center justify-center gap-1"
        >
          <CalendarDaysIcon className="h-4 w-4" />
          Open Full Calendar
        </Link>
      </div>
    </div>
  )
}

export default function Reservations() {
  const [isOpen, setIsOpen] = useState(false)
  const [form, setForm] = useState(initialFormState)
  const [selectedCluster, setSelectedCluster] = useState<{ id: string; name: string } | null>(null)

  const { data: reservationsData, isLoading: reservationsLoading } = useReservations()
  const { data: clustersData } = useClusters()
  const createReservation = useCreateReservation()
  const deleteReservation = useDeleteReservation()
  const cancelReservation = useCancelReservation()

  const reservations = reservationsData?.reservations || []
  const clusters = clustersData?.clusters || []

  // Split reservations into categories
  const activeReservations = reservations
    .filter((r) => r.status === 'active')
    .sort((a, b) => new Date(a.end_time).getTime() - new Date(b.end_time).getTime())
  
  const upcomingReservations = reservations
    .filter((r) => r.status === 'scheduled')
    .sort((a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime())
  
  const pastReservations = reservations
    .filter((r) => r.status === 'completed' || r.status === 'cancelled')
    .sort((a, b) => new Date(b.end_time).getTime() - new Date(a.end_time).getTime())

  const handleSubmit = async () => {
    if (!form.cluster_id || !form.title || !form.user_name || !form.start_time || !form.end_time) {
      toast.error('Please fill in all required fields')
      return
    }

    await createReservation.mutateAsync({
      cluster_id: form.cluster_id,
      title: form.title,
      description: form.description || undefined,
      user_name: form.user_name,
      user_email: form.user_email || undefined,
      team: form.team || undefined,
      start_time: new Date(form.start_time).toISOString(),
      end_time: new Date(form.end_time).toISOString(),
      purpose: form.purpose || undefined,
      color: form.color,
    })

    setIsOpen(false)
    setForm(initialFormState)
    setSelectedCluster(null)
  }

  const handleDelete = async (id: string) => {
    if (window.confirm('Are you sure you want to delete this reservation?')) {
      await deleteReservation.mutateAsync(id)
    }
  }

  const handleCancel = async (id: string) => {
    if (window.confirm('Are you sure you want to cancel this reservation?')) {
      await cancelReservation.mutateAsync(id)
    }
  }

  return (
    <div className="space-y-6">
      {/* Week Calendar - Centered */}
      <div className="flex justify-center">
        <div className="w-full max-w-4xl">
          <WeekCalendar reservations={reservations} />
        </div>
      </div>

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Reservations</h1>
          <p className="mt-1 text-sm text-gray-500">
            Manage cluster reservations and time slots
          </p>
        </div>
        <button onClick={() => setIsOpen(true)} className="btn-primary">
          <PlusIcon className="h-4 w-4 mr-2" />
          New Reservation
        </button>
      </div>

      <div className="space-y-6">

          {reservationsLoading ? (
        <div className="card p-12 text-center text-gray-500">Loading reservations...</div>
      ) : reservations.length === 0 ? (
        <div className="card p-12 text-center">
          <CalendarDaysIcon className="h-16 w-16 mx-auto text-gray-300" />
          <h3 className="mt-4 text-lg font-medium text-gray-900">No reservations yet</h3>
          <p className="mt-2 text-gray-500">Create your first reservation to get started.</p>
          <button onClick={() => setIsOpen(true)} className="mt-6 btn-primary">
            <PlusIcon className="h-4 w-4 mr-2" />
            New Reservation
          </button>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Active Reservations */}
          {activeReservations.length > 0 && (
            <div className="card border-l-4 border-l-green-500 overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-200 bg-green-50">
                <div className="flex items-center gap-2">
                  <span className="relative flex h-3 w-3">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
                  </span>
                  <h2 className="text-lg font-semibold text-gray-900">Active Now ({activeReservations.length})</h2>
                </div>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Reservation</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Cluster</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">User / Team</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Ends</th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {activeReservations.map((reservation) => (
                      <tr key={reservation.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-3">
                            <div className="h-10 w-1 rounded-full" style={{ backgroundColor: reservation.color }} />
                            <div>
                              <p className="font-medium text-gray-900">{reservation.title}</p>
                              {reservation.description && (
                                <p className="text-sm text-gray-500 truncate max-w-xs">{reservation.description}</p>
                              )}
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{reservation.cluster_name || 'Unknown'}</td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <p className="text-sm text-gray-900">{reservation.user_name}</p>
                          {reservation.team && <p className="text-xs text-gray-500">{reservation.team}</p>}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          <p className="text-gray-900">
                            Started: {format(new Date(reservation.start_time), 'MMM d, h:mm a')}
                          </p>
                          <p className="text-gray-500">
                            Ends: {format(new Date(reservation.end_time), 'MMM d, yyyy h:mm a')}
                          </p>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                          <button onClick={() => handleDelete(reservation.id)} className="text-red-600 hover:text-red-700">Delete</button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Upcoming Reservations */}
          <div className="card overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">Upcoming ({upcomingReservations.length})</h2>
              <p className="text-sm text-gray-500 mt-1">Scheduled reservations</p>
            </div>
            {upcomingReservations.length === 0 ? (
              <div className="px-6 py-8 text-center text-gray-500">No upcoming reservations</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Reservation</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Cluster</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">User / Team</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Time</th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {upcomingReservations.map((reservation) => (
                      <tr key={reservation.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-3">
                            <div className="h-10 w-1 rounded-full" style={{ backgroundColor: reservation.color }} />
                            <div>
                              <p className="font-medium text-gray-900">{reservation.title}</p>
                              {reservation.description && (
                                <p className="text-sm text-gray-500 truncate max-w-xs">{reservation.description}</p>
                              )}
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{reservation.cluster_name || 'Unknown'}</td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <p className="text-sm text-gray-900">{reservation.user_name}</p>
                          {reservation.team && <p className="text-xs text-gray-500">{reservation.team}</p>}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          <p className="text-gray-900">
                            {format(new Date(reservation.start_time), 'MMM d, yyyy h:mm a')}
                          </p>
                          <p className="text-gray-500">
                            to {format(new Date(reservation.end_time), 'MMM d, yyyy h:mm a')}
                          </p>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                          <button onClick={() => handleCancel(reservation.id)} className="text-orange-600 hover:text-orange-700 mr-3">Cancel</button>
                          <button onClick={() => handleDelete(reservation.id)} className="text-red-600 hover:text-red-700">Delete</button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Past Reservations */}
          <div className="card overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">Past ({pastReservations.length})</h2>
              <p className="text-sm text-gray-500 mt-1">Completed and cancelled reservations</p>
            </div>
            {pastReservations.length === 0 ? (
              <div className="px-6 py-8 text-center text-gray-500">No past reservations</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Reservation</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Cluster</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">User / Team</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {pastReservations.map((reservation) => (
                      <tr key={reservation.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-3">
                            <div className="h-10 w-1 rounded-full opacity-50" style={{ backgroundColor: reservation.color }} />
                            <div>
                              <p className="font-medium text-gray-600">{reservation.title}</p>
                              {reservation.description && (
                                <p className="text-sm text-gray-400 truncate max-w-xs">{reservation.description}</p>
                              )}
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">{reservation.cluster_name || 'Unknown'}</td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <p className="text-sm text-gray-600">{reservation.user_name}</p>
                          {reservation.team && <p className="text-xs text-gray-400">{reservation.team}</p>}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          <p className="text-gray-600">
                            {format(new Date(reservation.start_time), 'MMM d, yyyy h:mm a')}
                          </p>
                          <p className="text-gray-400">
                            to {format(new Date(reservation.end_time), 'MMM d, yyyy h:mm a')}
                          </p>
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex flex-col gap-1">
                            <span className={`badge ${reservation.status === 'completed' ? 'badge-success' : 'badge-error'}`}>
                              {reservation.status}
                            </span>
                            {reservation.status === 'cancelled' && reservation.notes && (
                              <p className="text-[10px] text-gray-400 leading-tight" title={reservation.notes}>
                                {reservation.notes.includes('[') ? reservation.notes.match(/\[([^\]]+)\]/)?.[1] : ''}
                              </p>
                            )}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                          <button onClick={() => handleDelete(reservation.id)} className="text-red-600 hover:text-red-700">Delete</button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}
      </div>

      <Transition appear show={isOpen} as={Fragment}>
        <Dialog as="div" className="relative z-50" onClose={() => setIsOpen(false)}>
          <Transition.Child
            as={Fragment}
            enter="ease-out duration-300"
            enterFrom="opacity-0"
            enterTo="opacity-100"
            leave="ease-in duration-200"
            leaveFrom="opacity-100"
            leaveTo="opacity-0"
          >
            <div className="fixed inset-0 bg-black/30 backdrop-blur-sm" />
          </Transition.Child>

          <div className="fixed inset-0 overflow-y-auto">
            <div className="flex min-h-full items-center justify-center p-4">
              <Transition.Child
                as={Fragment}
                enter="ease-out duration-300"
                enterFrom="opacity-0 scale-95"
                enterTo="opacity-100 scale-100"
                leave="ease-in duration-200"
                leaveFrom="opacity-100 scale-100"
                leaveTo="opacity-0 scale-95"
              >
                <Dialog.Panel className="w-full max-w-lg transform overflow-hidden rounded-2xl bg-white p-6 shadow-xl transition-all">
                  <div className="flex items-center justify-between">
                    <Dialog.Title as="h3" className="text-lg font-semibold text-gray-900">
                      New Reservation
                    </Dialog.Title>
                    <button
                      onClick={() => setIsOpen(false)}
                      className="p-2 rounded-lg hover:bg-gray-100"
                    >
                      <XMarkIcon className="h-5 w-5 text-gray-500" />
                    </button>
                  </div>

                  <div className="mt-6 space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Cluster *</label>
                      <Listbox
                        value={selectedCluster}
                        onChange={(cluster) => {
                          setSelectedCluster(cluster)
                          setForm((prev) => ({ ...prev, cluster_id: cluster?.id || '' }))
                        }}
                      >
                        <div className="relative mt-1">
                          <Listbox.Button className="relative w-full cursor-pointer rounded-lg border border-gray-300 bg-white py-2 pl-3 pr-10 text-left shadow-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500">
                            <span className="block truncate">
                              {selectedCluster?.name || 'Select a cluster'}
                            </span>
                            <span className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2">
                              <ChevronUpDownIcon className="h-5 w-5 text-gray-400" />
                            </span>
                          </Listbox.Button>
                          <Transition
                            as={Fragment}
                            leave="transition ease-in duration-100"
                            leaveFrom="opacity-100"
                            leaveTo="opacity-0"
                          >
                            <Listbox.Options className="absolute z-10 mt-1 max-h-60 w-full overflow-auto rounded-md bg-white py-1 shadow-lg ring-1 ring-black/5 focus:outline-none">
                              {clusters.map((cluster) => (
                                <Listbox.Option
                                  key={cluster.id}
                                  value={{ id: cluster.id, name: cluster.name }}
                                  className={({ active }) =>
                                    `relative cursor-pointer select-none py-2 pl-10 pr-4 ${
                                      active ? 'bg-primary-100 text-primary-900' : 'text-gray-900'
                                    }`
                                  }
                                >
                                  {({ selected }) => (
                                    <>
                                      <span
                                        className={`block truncate ${
                                          selected ? 'font-medium' : 'font-normal'
                                        }`}
                                      >
                                        {cluster.name}
                                      </span>
                                      {selected && (
                                        <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-primary-600">
                                          <CheckIcon className="h-5 w-5" />
                                        </span>
                                      )}
                                    </>
                                  )}
                                </Listbox.Option>
                              ))}
                            </Listbox.Options>
                          </Transition>
                        </div>
                      </Listbox>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700">Title *</label>
                      <input
                        type="text"
                        value={form.title}
                        onChange={(e) => setForm((prev) => ({ ...prev, title: e.target.value }))}
                        className="mt-1 block w-full rounded-lg border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                        placeholder="e.g., GPU Benchmark Testing"
                      />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700">
                          Your Name *
                        </label>
                        <input
                          type="text"
                          value={form.user_name}
                          onChange={(e) =>
                            setForm((prev) => ({ ...prev, user_name: e.target.value }))
                          }
                          className="mt-1 block w-full rounded-lg border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700">Team</label>
                        <input
                          type="text"
                          value={form.team}
                          onChange={(e) => setForm((prev) => ({ ...prev, team: e.target.value }))}
                          className="mt-1 block w-full rounded-lg border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                          placeholder="e.g., PSAP"
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700">
                          Start Time *
                        </label>
                        <input
                          type="datetime-local"
                          value={form.start_time}
                          onChange={(e) =>
                            setForm((prev) => ({ ...prev, start_time: e.target.value }))
                          }
                          className="mt-1 block w-full rounded-lg border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700">End Time *</label>
                        <input
                          type="datetime-local"
                          value={form.end_time}
                          onChange={(e) =>
                            setForm((prev) => ({ ...prev, end_time: e.target.value }))
                          }
                          className="mt-1 block w-full rounded-lg border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                        />
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700">Purpose</label>
                      <textarea
                        value={form.purpose}
                        onChange={(e) => setForm((prev) => ({ ...prev, purpose: e.target.value }))}
                        rows={2}
                        className="mt-1 block w-full rounded-lg border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                        placeholder="What will you be using the cluster for?"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Color</label>
                      <div className="flex gap-2">
                        {COLORS.map((color) => (
                          <button
                            key={color.value}
                            onClick={() => setForm((prev) => ({ ...prev, color: color.value }))}
                            className={`h-8 w-8 rounded-full transition-transform ${
                              form.color === color.value
                                ? 'ring-2 ring-offset-2 ring-gray-400 scale-110'
                                : 'hover:scale-105'
                            }`}
                            style={{ backgroundColor: color.value }}
                            title={color.name}
                          />
                        ))}
                      </div>
                    </div>
                  </div>

                  <div className="mt-6 flex justify-end gap-3">
                    <button onClick={() => setIsOpen(false)} className="btn-secondary">
                      Cancel
                    </button>
                    <button
                      onClick={handleSubmit}
                      disabled={createReservation.isPending}
                      className="btn-primary"
                    >
                      {createReservation.isPending ? 'Creating...' : 'Create Reservation'}
                    </button>
                  </div>
                </Dialog.Panel>
              </Transition.Child>
            </div>
          </div>
        </Dialog>
      </Transition>
    </div>
  )
}
