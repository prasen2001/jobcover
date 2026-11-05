const API_ROOT = '/api'

export class ApiError extends Error {
  status: number
  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('jobcover_token')
  const headers = new Headers(options.headers)
  if (token) headers.set('Authorization', `Bearer ${token}`)
  if (options.body && !(options.body instanceof FormData)) headers.set('Content-Type', 'application/json')
  const response = await fetch(`${API_ROOT}${path}`, { ...options, headers })
  const data = response.status === 204 ? null : await response.json().catch(() => ({}))
  if (!response.ok) throw new ApiError(data?.error || 'Something went wrong.', response.status)
  return data as T
}

