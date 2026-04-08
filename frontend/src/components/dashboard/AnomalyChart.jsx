import {
  ComposedChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, Cell, ResponsiveContainer, ReferenceLine
} from 'recharts'

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  const d = payload[0].payload
  return (
    <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 8, padding: '10px 14px', fontSize: 13 }}>
      <p style={{ fontWeight: 600, marginBottom: 4 }}>{label}</p>
      <p style={{ color: '#ef4444' }}>Gasto: ${d.expense.toLocaleString()}</p>
      <p style={{ color: '#22c55e' }}>Ingreso: ${d.income.toLocaleString()}</p>
      <p style={{ color: d.is_anomaly ? '#ef4444' : '#6b7280', fontWeight: d.is_anomaly ? 600 : 400 }}>
        {d.is_anomaly ? '⚠️ Mes anómalo' : '✅ Normal'}
      </p>
      <p style={{ color: '#6b7280', fontSize: 11 }}>Score: {d.anomaly_score?.toFixed(3)}</p>
    </div>
  )
}

const AnomalyChart = ({ data }) => {
  if (!data || data.error) {
    return (
      <div className="chart-card">
        <h3>🔍 Detección de meses anómalos</h3>
        <div className="loading-state">{data?.error || 'Sin datos'}</div>
      </div>
    )
  }

  const anomalies = data.months.filter(m => m.is_anomaly)

  return (
    <div className="chart-card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
        <div>
          <h3>🔍 Detección de meses anómalos</h3>
          <p style={{ fontSize: 12, color: 'var(--gray-500)', marginTop: 2 }}>
            Meses con gasto inusual detectados por IsolationForest
          </p>
        </div>
        <div style={{ fontSize: 12, background: anomalies.length > 0 ? '#fef2f2' : '#f0fdf4', color: anomalies.length > 0 ? '#ef4444' : '#16a34a', padding: '4px 10px', borderRadius: 20, fontWeight: 600 }}>
          {anomalies.length > 0 ? `⚠️ ${anomalies.length} mes${anomalies.length > 1 ? 'es' : ''} anómalo${anomalies.length > 1 ? 's' : ''}` : '✅ Sin anomalías'}
        </div>
      </div>

      <ResponsiveContainer width="100%" height={220}>
        <ComposedChart data={data.months}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis dataKey="month" tick={{ fontSize: 11 }} />
          <YAxis tick={{ fontSize: 11 }} width={55} />
          <Tooltip content={<CustomTooltip />} />
          <Bar dataKey="expense" name="Gasto" radius={[3, 3, 0, 0]}>
            {data.months.map((m, i) => (
              <Cell key={i} fill={m.is_anomaly ? '#ef4444' : '#94a3b8'} opacity={m.is_anomaly ? 1 : 0.6} />
            ))}
          </Bar>
        </ComposedChart>
      </ResponsiveContainer>

      {anomalies.length > 0 && (
        <div style={{ marginTop: 12, display: 'flex', flexWrap: 'wrap', gap: 8 }}>
          {anomalies.map(m => (
            <div key={m.month} style={{ background: '#fef2f2', border: '1px solid #fecaca', borderRadius: 8, padding: '6px 12px', fontSize: 12 }}>
              <span style={{ fontWeight: 600, color: '#ef4444' }}>⚠️ {m.month}</span>
              <span style={{ color: '#6b7280', marginLeft: 6 }}>${m.expense.toLocaleString()}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default AnomalyChart
