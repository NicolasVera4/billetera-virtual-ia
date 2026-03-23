const ICONS = {
  income: '📈',
  expense: '📉',
}

const TransactionList = ({ transactions, categories }) => {
  const catMap = {}
  categories.forEach(c => { catMap[c.id] = c.name })

  const recent = [...transactions]
    .sort((a, b) => new Date(b.transaction_date) - new Date(a.transaction_date))
    .slice(0, 8)

  if (recent.length === 0) {
    return (
      <div className="transactions-card">
        <h3>Últimas transacciones</h3>
        <div className="loading-state">Sin transacciones</div>
      </div>
    )
  }

  return (
    <div className="transactions-card">
      <h3>Últimas transacciones</h3>
      {recent.map((t) => (
        <div key={t.id} className="transaction-item">
          <div className="transaction-left">
            <div className="transaction-icon">{ICONS[t.type]}</div>
            <div>
              <div className="transaction-desc">{t.description}</div>
              <div className="transaction-date">
                {catMap[t.category_id] || 'Sin categoría'} · {t.transaction_date}
              </div>
            </div>
          </div>
          <div className={`transaction-amount ${t.type}`}>
            {t.type === 'expense' ? '-' : '+'}${parseFloat(t.amount).toLocaleString('es-AR', { minimumFractionDigits: 2 })}
          </div>
        </div>
      ))}
    </div>
  )
}

export default TransactionList
