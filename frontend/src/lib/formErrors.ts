import { ApiError } from './api'

export type FieldErrors = Record<string, string[]>

export const NOT_ACCESSIBLE = '無法存取此行程（不存在或您不是行程參與者）。'
export const FORBIDDEN = '您沒有權限執行此操作。'

export interface AccessErrorOptions {
  preferServerDetail?: boolean
}

function serverDetail(err: ApiError): string | null {
  if (err.body && typeof err.body === 'object' && 'detail' in err.body) {
    const detail = (err.body as { detail?: unknown }).detail
    if (typeof detail === 'string' && detail.trim()) {
      return detail;
    }
  }
  return null
}

export function accessErrorMessage(
  err: unknown,
  fallback: string,
  opts: AccessErrorOptions = {},
): string {
  if (err instanceof ApiError) {
    if (err.status === 404) {
      return (opts.preferServerDetail ? serverDetail(err) : null) ?? NOT_ACCESSIBLE
    }
    if (err.status === 403) {
      return serverDetail(err) ?? FORBIDDEN
    }
  }
  return fallback
}

export function toFieldErrors(
  err: unknown,
  fallback: string,
  opts: AccessErrorOptions = {},
): FieldErrors {
  if (err instanceof ApiError && (err.status === 403 || err.status === 404)) {
    return { _root: [accessErrorMessage(err, fallback, opts)] }
  }
  if (err instanceof ApiError && err.body && typeof err.body === 'object') {
    const next: FieldErrors = {}
    for (const [key, value] of Object.entries(err.body as Record<string, unknown>)) {
      if (Array.isArray(value) && value.every((v) => typeof v === 'string')) {
        next[key === 'non_field_errors' ? '_root' : key] = value as string[]
      } else if (typeof value === 'string') {
        next[key === 'detail' ? '_root' : key] = [value]
      }
    }
    if (Object.keys(next).length > 0) {
      return next;
    }
  }
  return { _root: [fallback] }
}
