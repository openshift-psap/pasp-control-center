export enum LogLevel {
  ERROR = 0,
  WARN = 1,
  INFO = 2,
  DEBUG = 3,
}

const LOG_LEVEL_NAMES: Record<LogLevel, string> = {
  [LogLevel.ERROR]: 'ERROR',
  [LogLevel.WARN]: 'WARN',
  [LogLevel.INFO]: 'INFO',
  [LogLevel.DEBUG]: 'DEBUG',
}

let currentLogLevel: LogLevel = LogLevel.INFO

function formatDateTime(): string {
  const now = new Date()
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  const hours = String(now.getHours()).padStart(2, '0')
  const minutes = String(now.getMinutes()).padStart(2, '0')
  const seconds = String(now.getSeconds()).padStart(2, '0')
  const ms = String(now.getMilliseconds()).padStart(3, '0')
  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}.${ms}`
}

function formatArg(arg: unknown): string {
  if (arg instanceof Error) return arg.stack || arg.message
  if (typeof arg === 'object' && arg !== null) {
    try {
      return JSON.stringify(arg, null, 2)
    } catch {
      return String(arg)
    }
  }
  return String(arg)
}

function formatMessage(context: string, level: LogLevel, message: string, args: unknown[]): string {
  const datetime = formatDateTime()
  const levelName = LOG_LEVEL_NAMES[level]
  const formattedMessage = args.length > 0
    ? `${message} ${args.map(formatArg).join(' ')}`
    : message
  return `${datetime} ${context}: ${levelName} - ${formattedMessage}`
}

class Logger {
  constructor(private context: string) {}

  error(message: string, ...args: unknown[]): void {
    if (currentLogLevel >= LogLevel.ERROR)
      console.error(formatMessage(this.context, LogLevel.ERROR, message, args))
  }

  warn(message: string, ...args: unknown[]): void {
    if (currentLogLevel >= LogLevel.WARN)
      console.warn(formatMessage(this.context, LogLevel.WARN, message, args))
  }

  info(message: string, ...args: unknown[]): void {
    if (currentLogLevel >= LogLevel.INFO)
      console.log(formatMessage(this.context, LogLevel.INFO, message, args))
  }

  debug(message: string, ...args: unknown[]): void {
    if (currentLogLevel >= LogLevel.DEBUG)
      console.log(formatMessage(this.context, LogLevel.DEBUG, message, args))
  }
}

export function createLogger(context: string): Logger {
  return new Logger(context)
}

export function setLogLevel(level: LogLevel): void {
  currentLogLevel = level
}

export function setLogLevelFromEnv(): void {
  const envLevel = import.meta.env.VITE_LOG_LEVEL?.toUpperCase()
  const levelMap: Record<string, LogLevel> = {
    ERROR: LogLevel.ERROR,
    WARN: LogLevel.WARN,
    INFO: LogLevel.INFO,
    DEBUG: LogLevel.DEBUG,
  }
  if (envLevel && envLevel in levelMap) {
    currentLogLevel = levelMap[envLevel]
  }
}
