import { NavLink } from 'react-router-dom'

const Sidebar = ({ conversations, currentConvId, onSelectConv }) => {
  const formatDate = (dateStr) => {
    const d = new Date(dateStr)
    return d.toLocaleDateString('es-AR', { day: 'numeric', month: 'short' })
  }

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="logo-icon">💳</div>
        <span>Qash</span>
      </div>

      <nav className="sidebar-nav">
        <NavLink to="/dashboard" className={({ isActive }) => isActive ? 'active' : ''}>
          📊 Dashboard
        </NavLink>
        <NavLink to="/chat" className={({ isActive }) => isActive ? 'active' : ''}>
          💬 Chat
        </NavLink>
      </nav>

      <div className="sidebar-conversations">
        {conversations.length > 0 && (
          <h4>Conversaciones</h4>
        )}
        {conversations.map((conv) => (
          <div
            key={conv.id}
            className={`conv-item ${conv.id === currentConvId ? 'active' : ''}`}
            onClick={() => onSelectConv(conv.id)}
          >
            <span style={{ fontSize: 14 }}>💬</span>
            <div className="conv-item-text">
              <div className="conv-title">{conv.title}</div>
              <div className="conv-date">{formatDate(conv.createdAt)}</div>
            </div>
          </div>
        ))}
      </div>
    </aside>
  )
}

export default Sidebar
