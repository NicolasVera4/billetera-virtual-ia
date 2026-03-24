import { useState, useRef, useEffect } from 'react'
import { Paperclip, Mic, Square, Send, Loader2 } from 'lucide-react'
import { transcribeAudio } from '../api/agent'

const ChatInput = ({ onSend, onFileUpload, disabled }) => {
  const [value, setValue] = useState('')
  const [recording, setRecording] = useState(false)
  const [transcribing, setTranscribing] = useState(false)
  const fileRef = useRef()
  const mediaRef = useRef(null)
  const chunksRef = useRef([])
  const canvasRef = useRef()
  const animRef = useRef()
  const analyserRef = useRef()

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

  const drawWave = () => {
    const canvas = canvasRef.current
    const analyser = analyserRef.current
    if (!canvas || !analyser) return

    const dpr = window.devicePixelRatio || 1
    const rect = canvas.getBoundingClientRect()
    canvas.width = rect.width * dpr
    canvas.height = rect.height * dpr
    const ctx = canvas.getContext('2d')
    ctx.scale(dpr, dpr)

    analyser.fftSize = 2048
    const bufferLength = analyser.fftSize
    const dataArray = new Uint8Array(bufferLength)

    const w = rect.width
    const h = rect.height

    const draw = () => {
      animRef.current = requestAnimationFrame(draw)
      analyser.getByteTimeDomainData(dataArray)

      ctx.clearRect(0, 0, w, h)
      ctx.lineWidth = 2
      ctx.strokeStyle = '#ef4444'
      ctx.beginPath()

      const sliceWidth = w / bufferLength
      let x = 0
      for (let i = 0; i < bufferLength; i++) {
        const v = dataArray[i] / 128.0
        const y = (v * h) / 2
        if (i === 0) ctx.moveTo(x, y)
        else ctx.lineTo(x, y)
        x += sliceWidth
      }
      ctx.lineTo(w, h / 2)
      ctx.stroke()
    }
    draw()
  }

  const startRecording = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    chunksRef.current = []

    const audioCtx = new AudioContext()
    const source = audioCtx.createMediaStreamSource(stream)
    const analyser = audioCtx.createAnalyser()
    source.connect(analyser)
    analyserRef.current = analyser

    const recorder = new MediaRecorder(stream)
    mediaRef.current = recorder

    recorder.ondataavailable = (e) => chunksRef.current.push(e.data)
    recorder.onstop = async () => {
      cancelAnimationFrame(animRef.current)
      audioCtx.close()
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

  useEffect(() => {
    if (recording) drawWave()
  }, [recording])

  return (
    <div className="chat-input-wrapper">
      {recording && (
        <div style={{ padding: '0 16px 8px' }}>
          <canvas
            ref={canvasRef}
            width={400}
            height={32}
            style={{ width: '100%', height: 32, borderRadius: 6, background: '#fef2f2' }}
          />
        </div>
      )}
      <div className="chat-input-box">
        <button className="btn-attach" onClick={() => fileRef.current.click()} title="Subir archivo">
          <Paperclip size={18} />
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
          placeholder={transcribing ? 'Transcribiendo...' : 'Ej: Gasté 500 en el supermercado...'}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKey}
          disabled={disabled || transcribing}
        />
        <button
          className="btn-attach"
          onClick={recording ? stopRecording : startRecording}
          disabled={transcribing || disabled}
          title={recording ? 'Detener grabación' : 'Grabar audio'}
          style={recording ? { color: '#ef4444' } : {}}
        >
          {transcribing
            ? <Loader2 size={18} className="spin" />
            : recording
            ? <Square size={18} fill="#ef4444" />
            : <Mic size={18} />}
        </button>
        <button
          className="btn-send"
          onClick={handleSend}
          disabled={!value.trim() || disabled}
          title="Enviar"
        >
          <Send size={16} />
        </button>
      </div>
      <div className="input-hint">Registra gastos, ingresos o consulta tus finanzas</div>
    </div>
  )
}

export default ChatInput
