import { useState, useRef } from 'react'

const ChatInput = ({ onSend, onFileUpload, disabled }) => {
  const [value, setValue] = useState('')
  const fileRef = useRef()

  const handleSend = () => {
    if (!value.trim() || disabled) return
    onSend(value.trim())
    setValue('')
  }

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleFile = (e) => {
    const file = e.target.files[0]
    if (file) onFileUpload(file)
    e.target.value = ''
  }

  return (
    <div className="chat-input-wrapper">
      <div className="chat-input-box">
        <button className="btn-attach" onClick={() => fileRef.current.click()} title="Subir archivo">
          📎
        </button>
        <input
          type="file"
          ref={fileRef}
          style={{ display: 'none' }}
          onChange={handleFile}
          accept=".csv,.xlsx,.pdf,.png,.jpg,.jpeg"
        />
        <input
          type="text"
          placeholder="Ej: Gasté 500 en el supermercado..."
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKey}
          disabled={disabled}
        />
        <button
          className="btn-send"
          onClick={handleSend}
          disabled={!value.trim() || disabled}
          title="Enviar"
        >
          ➤
        </button>
      </div>
      <div className="input-hint">Registra gastos, ingresos o consulta tus finanzas</div>
    </div>
  )
}

export default ChatInput
