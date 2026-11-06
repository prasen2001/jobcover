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

type StreamEvent = { type: 'token'; content: string } | { type: 'done' } | { type: 'error'; message: string }

export async function streamApi(path: string, body: unknown, onToken: (content: string) => void): Promise<void> {
  const token = localStorage.getItem('jobcover_token')
  const response = await fetch(`${API_ROOT}${path}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(body),
  })
  if (!response.ok) {
    const data = await response.json().catch(() => ({}))
    throw new ApiError(data?.error || 'Generation failed.', response.status)
  }
  if (!response.body) throw new ApiError('This browser cannot read streamed responses.', 500)

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  const processFrame = (frame: string) => {
    const data = frame.split('\n').find((line) => line.startsWith('data: '))
    if (!data) return
    const event = JSON.parse(data.slice(6)) as StreamEvent
    if (event.type === 'token') onToken(event.content)
    if (event.type === 'error') throw new ApiError(event.message, 502)
  }

  while (true) {
    const { value, done } = await reader.read()
    buffer += decoder.decode(value, { stream: !done })
    let boundary = buffer.indexOf('\n\n')
    while (boundary !== -1) {
      processFrame(buffer.slice(0, boundary))
      buffer = buffer.slice(boundary + 2)
      boundary = buffer.indexOf('\n\n')
    }
    if (done) break
  }
  if (buffer.trim()) processFrame(buffer)
}

