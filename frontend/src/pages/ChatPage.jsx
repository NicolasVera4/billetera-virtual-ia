import { useState, useEffect, useRef } from 'react'
import Sidebar from '../components/Sidebar'
import ChatMessage from '../components/ChatMessage'
import ChatInput from '../components/ChatInput'
import { askAgentStream, uploadFile } from '../api/agent'

const SUGGESTIONS = [
  { icon: '🛒', text: 'Gasté 1500 en el supermercado' },
  { icon: '📈', text: 'Me depositaron 50000 de sueldo' },
  { icon: '📊', text: '¿Cuáles fueron mis mayores gastos este mes?' },
]

const ChatPage = () => {
  const [conversations, setConversations] = useState(() => {
    try { return JSON.parse(localStorage.getItem('qash_convs') || '[]') }
    catch { return [] }
  })
  const [currentConvId, setCurrentConvId] = useState(null)
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef()
  const convIdRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    localStorage.setItem('qash_convs', JSON.stringify(conversations))
  }, [conversations])

  const newConversation = () => {
    setCurrentConvId(null)
    convIdRef.current = null
    setMessages([])
  }

  const selectConversation = (id) => {
    const conv = conversations.find(c => c.id === id)
    if (conv) {
      setCurrentConvId(id)
      convIdRef.current = id
      setMessages(conv.messages)
    }
  }

  const saveMessages = (convId, msgs, title) => {
    setConversations(prev => {
      const exists = prev.find(c => c.id === convId)
      if (exists) {
        return prev.map(c => c.id === convId ? { ...c, messages: msgs } : c)
      }
      return [{ id: convId, title, messages: msgs, createdAt: new Date().toISOString() }, ...prev]
    })
  }

  const sendMessage = async (text) => {
    const userMsg = { role: 'user', content: text }
    const assistantMsg = { role: 'assistant', content: '', tool: null }

    setMessages(prev => [...prev, userMsg, assistantMsg])
    setLoading(true)

    const convId = convIdRef.current || Date.now().toString()
    if (!convIdRef.current) {
      convIdRef.current = convId
      setCurrentConvId(convId)
    }

    try {
      await askAgentStream(
        text,
        // onTool: cuando el backend notifica qué tool usó
        (tool) => {
          setMessages(prev => {
            const updated = [...prev]
            updated[updated.length - 1] = { ...updated[updated.length - 1], tool }
            return updated
          })
        },
        // onChunk: cada fragmento de texto que llega
        (chunk) => {
          setMessages(prev => {
            const updated = [...prev]
            updated[updated.length - 1] = {
              ...updated[updated.length - 1],
              content: updated[updated.length - 1].content + chunk
            }
            return updated
          })
        },
        // onDone: cuando termina
        () => {
          setLoading(false)
          setMessages(prev => {
            const title = text.length > 35 ? text.slice(0, 35) + '...' : text
            saveMessages(convId, prev, title)
            return prev
          })
        }
      )
    } catch {
      setMessages(prev => {
        const updated = [...prev]
        updated[updated.length - 1] = {
          role: 'assistant',
          content: 'Error al conectar con el servidor. Verificá que el backend esté corriendo.'
        }
        return updated
      })
      setLoading(false)
    }
  }

  const handleFile = async (file) => {
    const userMsg = { role: 'user', content: `📎 Subiendo archivo: ${file.name}` }
    const loadingMsg = { role: 'assistant', content: 'loading' }
    setMessages(prev => [...prev, userMsg, loadingMsg])
    setLoading(true)

    try {
      const data = await uploadFile(file)
      const text = data.message || data.error || 'Archivo procesado'
      const detail = data.transaction
        ? `\n📅 Fecha: ${data.transaction.fecha} | 💰 Monto: $${data.transaction.monto} | 🏷️ ${data.transaction.categoria}`
        : data.inserted !== undefined
        ? `\n✅ Insertadas: ${data.inserted} | ⏭️ Duplicadas: ${data.skipped_duplicates}`
        : ''
      const assistantMsg = { role: 'assistant', content: text + detail }
      setMessages(prev => {
        const updated = [...prev.slice(0, -1), assistantMsg]
        const convId = convIdRef.current || Date.now().toString()
        if (!convIdRef.current) {
          convIdRef.current = convId
          setCurrentConvId(convId)
        }
        saveMessages(convId, updated, `Archivo: ${file.name}`)
        return updated
      })
    } catch {
      setMessages(prev => [...prev.slice(0, -1), { role: 'assistant', content: 'Error al procesar el archivo.' }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="layout">
      <Sidebar
        conversations={conversations}
        currentConvId={currentConvId}
        onSelectConv={selectConversation}
      />
      <div className="main-content">
        <div className="chat-header">
          <div className="chat-header-left">
            <div className="chat-header-icon">💳</div>
            <div>
              <div className="chat-header-title">Qash</div>
              <div className="chat-header-subtitle">Tu billetera inteligente</div>
            </div>
          </div>
          <button className="btn-new-chat" onClick={newConversation} title="Nueva conversación">+</button>
        </div>

        <div className="messages-area">
          {messages.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon">💳</div>
              <h2>Hola, soy Qash</h2>
              <p>Tu asistente financiero personal. Contame tus gastos e ingresos y te ayudo a mantener tus finanzas en orden.</p>
              <div className="suggestions">
                {SUGGESTIONS.map((s) => (
                  <button key={s.text} className="suggestion-chip" onClick={() => sendMessage(s.text)}>
                    <span className="chip-icon">{s.icon}</span>
                    {s.text}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((msg, i) => <ChatMessage key={i} message={msg} />)
          )}
          <div ref={bottomRef} />
        </div>

        <ChatInput onSend={sendMessage} onFileUpload={handleFile} disabled={loading} />
      </div>
    </div>
  )
}

export default ChatPage
