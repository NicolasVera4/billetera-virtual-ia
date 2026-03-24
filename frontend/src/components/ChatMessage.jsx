const ChatMessage = ({ message }) => {
  const { role, content, tool } = message

  return (
    <>
      {tool && (
        <div className="tool-indicator">
          <div className="tool-dot" />
          <span>{tool}</span>
          <span>• Listo</span>
        </div>
      )}
      <div className={`message-row ${role}`}>
        {role === 'assistant' && (
          <div className="message-avatar">💳</div>
        )}
        <div className="message-bubble">
          {content === 'loading' ? (
            <div className="loading-dots">
              <span /><span /><span />
            </div>
          ) : (
            content.split('\n').map((line, i) => (
              <span key={i}>{line}{i < content.split('\n').length - 1 && <br />}</span>
            ))
          )}
        </div>
      </div>
    </>
  )
}

export default ChatMessage
