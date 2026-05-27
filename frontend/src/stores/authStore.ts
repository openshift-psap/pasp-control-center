import { createLogger } from '../utils/logger'

const logger = createLogger('AuthStore')

const STORAGE_KEY = 'psap_auth'

export interface AuthCredentials {
  username: string
  password: string
}

let credentials: AuthCredentials | null = null

function loadFromSession(): AuthCredentials | null {
  try {
    const stored = sessionStorage.getItem(STORAGE_KEY)
    if (stored) return JSON.parse(stored)
  } catch {
    // ignore parse errors
  }
  return null
}

credentials = loadFromSession()

export function getCredentials(): AuthCredentials | null {
  return credentials
}

export function isAuthenticated(): boolean {
  return credentials !== null
}

export function getBasicAuthHeader(): string | null {
  if (!credentials) return null
  return 'Basic ' + btoa(`${credentials.username}:${credentials.password}`)
}

export function setCredentials(creds: AuthCredentials): void {
  credentials = creds
  sessionStorage.setItem(STORAGE_KEY, JSON.stringify(creds))
  logger.info('User authenticated:', creds.username)
  window.dispatchEvent(new Event('auth-change'))
}

export function clearCredentials(): void {
  credentials = null
  sessionStorage.removeItem(STORAGE_KEY)
  logger.info('User logged out')
  window.dispatchEvent(new Event('auth-change'))
}
