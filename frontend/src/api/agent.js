import axios from 'axios'

const BASE = 'http://localhost:8000'
const API = axios.create({ baseURL: BASE })

export const askAgentStream = async (question, onTool, onChunk, onDone) => {
  const response = await fetch(`${BASE}/agent/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question })
  })

  const reader = response.body.getReader()
  const decoder = new TextDecoder()

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    const text = decoder.decode(value)
    const lines = text.split('\n').filter(l => l.startsWith('data: '))

    for (const line of lines) {
      try {
        const data = JSON.parse(line.slice(6))
        if (data.type === 'tool') onTool(data.tool)
        else if (data.type === 'chunk') onChunk(data.text)
        else if (data.type === 'done') onDone(data.tool || null)
      } catch { /* chunk parcial, ignorar */ }
    }
  }
}

export const uploadFile = async (file) => {
  const form = new FormData()
  form.append('file', file)
  const name = file.name.toLowerCase()
  const isReceipt = name.endsWith('.pdf') || name.endsWith('.png') ||
                    name.endsWith('.jpg') || name.endsWith('.jpeg')
  const endpoint = isReceipt ? '/upload_factura/' : '/upload_data/'
  const res = await API.post(endpoint, form, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
  return res.data
}
