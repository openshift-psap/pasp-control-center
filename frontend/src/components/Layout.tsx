import { Fragment, useState } from 'react'
import { Outlet, NavLink, useLocation } from 'react-router-dom'
import { Dialog, Transition } from '@headlessui/react'
import {
  Bars3Icon,
  XMarkIcon,
  HomeIcon,
  ServerStackIcon,
  CalendarDaysIcon,
  ClipboardDocumentListIcon,
  BeakerIcon,
  ChartBarIcon,
} from '@heroicons/react/24/outline'
import clsx from 'clsx'

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: HomeIcon },
  { name: 'Clusters', href: '/clusters', icon: ServerStackIcon },
  { name: 'Reservations', href: '/reservations', icon: ClipboardDocumentListIcon },
  { name: 'Calendar', href: '/calendar', icon: CalendarDaysIcon },
  { name: 'Testing', href: '/testing', icon: BeakerIcon, comingSoon: true },
  { name: 'Results', href: '/results', icon: ChartBarIcon, comingSoon: true },
]

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const location = useLocation()

  return (
    <div className="min-h-screen bg-gray-50">
      <Transition.Root show={sidebarOpen} as={Fragment}>
        <Dialog as="div" className="relative z-50 lg:hidden" onClose={setSidebarOpen}>
          <Transition.Child
            as={Fragment}
            enter="transition-opacity ease-linear duration-300"
            enterFrom="opacity-0"
            enterTo="opacity-100"
            leave="transition-opacity ease-linear duration-300"
            leaveFrom="opacity-100"
            leaveTo="opacity-0"
          >
            <div className="fixed inset-0 bg-gray-900/80" />
          </Transition.Child>

          <div className="fixed inset-0 flex">
            <Transition.Child
              as={Fragment}
              enter="transition ease-in-out duration-300 transform"
              enterFrom="-translate-x-full"
              enterTo="translate-x-0"
              leave="transition ease-in-out duration-300 transform"
              leaveFrom="translate-x-0"
              leaveTo="-translate-x-full"
            >
              <Dialog.Panel className="relative mr-16 flex w-full max-w-xs flex-1">
                <div className="flex grow flex-col gap-y-5 overflow-y-auto bg-white px-6 pb-4">
                  <div className="flex h-16 shrink-0 items-center">
                    <div className="flex items-center gap-2">
                      <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-primary-600 to-primary-700 flex items-center justify-center">
                        <span className="text-white font-bold text-sm">P</span>
                      </div>
                      <span className="text-xl font-bold text-gray-900">PASP Control Center</span>
                    </div>
                  </div>
                  <nav className="flex flex-1 flex-col">
                    <ul className="flex flex-1 flex-col gap-y-1">
                      {navigation.map((item) => (
                        <li key={item.name}>
                          <NavLink
                            to={item.href}
                            onClick={() => setSidebarOpen(false)}
                            className={({ isActive }) =>
                              clsx(
                                'group flex gap-x-3 rounded-lg p-3 text-sm font-medium transition-colors',
                                isActive
                                  ? 'bg-primary-50 text-primary-700'
                                  : 'text-gray-700 hover:bg-gray-50 hover:text-primary-600'
                              )
                            }
                          >
                            <item.icon className="h-5 w-5 shrink-0" />
                            {item.name}
                            {item.comingSoon && (
                              <span className="ml-auto text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full">
                                Soon
                              </span>
                            )}
                          </NavLink>
                        </li>
                      ))}
                    </ul>
                  </nav>
                </div>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </Dialog>
      </Transition.Root>

      <div className="hidden lg:fixed lg:inset-y-0 lg:z-50 lg:flex lg:w-72 lg:flex-col">
        <div className="flex grow flex-col gap-y-5 overflow-y-auto border-r border-gray-200 bg-white px-6 pb-4">
          <div className="flex h-16 shrink-0 items-center">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-primary-600 to-primary-700 flex items-center justify-center shadow-lg shadow-primary-500/20">
                <span className="text-white font-bold text-lg">P</span>
              </div>
              <div>
                <h1 className="text-lg font-bold text-gray-900">PASP Control Center</h1>
                <p className="text-xs text-gray-500">Cluster Management</p>
              </div>
            </div>
          </div>
          <nav className="flex flex-1 flex-col">
            <ul className="flex flex-1 flex-col gap-y-1">
              {navigation.map((item) => (
                <li key={item.name}>
                  <NavLink
                    to={item.href}
                    className={({ isActive }) =>
                      clsx(
                        'group flex gap-x-3 rounded-lg p-3 text-sm font-medium transition-all duration-200',
                        isActive
                          ? 'bg-primary-50 text-primary-700 shadow-sm'
                          : 'text-gray-700 hover:bg-gray-50 hover:text-primary-600'
                      )
                    }
                  >
                    <item.icon
                      className={clsx(
                        'h-5 w-5 shrink-0 transition-colors',
                        location.pathname === item.href ? 'text-primary-600' : 'text-gray-400 group-hover:text-primary-500'
                      )}
                    />
                    {item.name}
                    {item.comingSoon && (
                      <span className="ml-auto text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full">
                        Soon
                      </span>
                    )}
                  </NavLink>
                </li>
              ))}
            </ul>

            <div className="mt-auto pt-4 border-t border-gray-200">
              <div className="rounded-xl bg-gradient-to-br from-gray-50 to-gray-100 p-4">
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Organization</p>
                <p className="mt-1 text-sm font-semibold text-gray-900">OpenShift PSAP</p>
                <p className="text-xs text-gray-500">Performance & Scale for AI Platforms</p>
              </div>
            </div>
          </nav>
        </div>
      </div>

      <div className="lg:pl-72">
        <div className="sticky top-0 z-40 flex h-16 shrink-0 items-center gap-x-4 border-b border-gray-200 bg-white/80 backdrop-blur-sm px-4 shadow-sm sm:gap-x-6 sm:px-6 lg:px-8">
          <button
            type="button"
            className="-m-2.5 p-2.5 text-gray-700 lg:hidden"
            onClick={() => setSidebarOpen(true)}
          >
            <span className="sr-only">Open sidebar</span>
            <Bars3Icon className="h-6 w-6" />
          </button>

          <div className="flex flex-1 gap-x-4 self-stretch lg:gap-x-6">
            <div className="flex flex-1" />
            <div className="flex items-center gap-x-4 lg:gap-x-6">
              <div className="hidden lg:block lg:h-6 lg:w-px lg:bg-gray-200" />
              <div className="flex items-center gap-2">
                <div className="h-8 w-8 rounded-full bg-primary-100 flex items-center justify-center">
                  <span className="text-sm font-medium text-primary-700">AC</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <main className="py-6 px-4 sm:px-6 lg:px-8">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
