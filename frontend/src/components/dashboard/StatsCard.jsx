const StatsCard = ({ label, value, icon, type }) => {
  const isNegative = parseFloat(value) < 0

  return (
    <div className="stat-card">
      <div className="stat-card-header">
        <span className="stat-label">{label}</span>
        <span className="stat-icon">{icon}</span>
      </div>
      <div className={`stat-value ${type} ${type === 'balance' ? (isNegative ? 'negative' : 'positive') : ''}`}>
        ${Math.abs(parseFloat(value || 0)).toLocaleString('es-AR', { minimumFractionDigits: 2 })}
        {type === 'balance' && isNegative && ' (negativo)'}
      </div>
    </div>
  )
}

export default StatsCard
