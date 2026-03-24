import { useState, useRef } from 'react'
import { transcribeAudio } from '../api/agent'

const ChatInput = ({ onSend, onFileUpload, disabled }) => {
  const [value, setValue] = useState('')
  const [recording, setRecording] = useState(false)
  const [transcribing, setTranscribing] = useState(false)
  const fileRef = useRef()
  const mediaRef = useRef(null)
  const chunksRef = useRef([])

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

  const startRecording = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    chunksRef.current = []
    const recorder = new MediaRecorder(stream)
    mediaRef.current = recorder

    recorder.ondataavailable = (e) => chunksRef.current.push(e.data)
    recorder.onstop = async () => {
      stream.getTracks().forEach(t => t.stop())
      const blob = new Blob(chunksRef.current, { type: 'audio/webm' })
      setTranscribing(true)
      try {
        const text = await transcribeAudio(blob)
        setValue(text)
      } finally {
        setTranscribing(false)
      }
    }

    recorder.start()
    setRecording(true)
  }

  const stopRecording = () => {
    mediaRef.current?.stop()
    setRecording(false)
  }

  const handleVoice = () => {
    if (recording) stopRecording()
    else startRecording()
  }

  const micLabel = transcribing ? '⏳' : recording ? '⏹️' : '🎙️'
  const micTitle = transcribing ? 'Transcribiendo...' : recording ? 'Detener grabación' : 'Grabar audio'

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
          className="btn-attach"
          onClick={handleVoice}
          disabled={transcribing || disabled}
          title={micTitle}
          style={recording ? { color: '#ef4444' } : {}}
        >
          {micLabel}
        </button>
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
