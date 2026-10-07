const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export const MAX_UPLOAD_MB = 5

export const COMPLEXITIES = [
  { value: 'O(1)', label: 'O(1)' },
  { value: 'O(log n)', label: 'O(log n)' },
  { value: 'O(n)', label: 'O(n)' },
  { value: 'O(n log n)', label: 'O(n log n)' },
  { value: 'O(n**2)', label: 'O(n²)' },
  { value: 'O(n**3)', label: 'O(n³)' },
]

// Sends a request and returns the image Blob, or throws an Error with a readable message.
async function requestImage(path, options) {
  let response
  try {
    response = await fetch(`${API_URL}${path}`, { method: 'POST', ...options })
  } catch {
    throw new Error('Cannot reach the server. Is the API running?')
  }
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    const detail = body?.detail
    // FastAPI validation errors (422) come as a list of objects
    const message = Array.isArray(detail) ? detail.map((item) => item.msg).join(', ') : detail
    throw new Error(message || `Server error (${response.status})`)
  }
  return response.blob()
}

export function createFlowchart(file) {
  const form = new FormData()
  form.append('file', file)
  return requestImage('/create/flowchart', { body: form })
}

export function createChart(data) {
  return requestImage('/create/chart', {
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
}

// "[14, 2282, 65236]" (what print() shows), "10 100 1000" and "10, 100; 1000" all work
export function parseNumbers(text) {
  return (text.match(/-?\d+(?:\.\d+)?(?:e[+-]?\d+)?/gi) ?? []).map(Number)
}
