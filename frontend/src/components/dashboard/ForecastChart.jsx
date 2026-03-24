import {
  ComposedChart, Line, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ReferenceLine, ResponsiveContainer
} from 'recharts'

const ForecastChart = ({ data }) => {
  if (!data || data.error) {
    return (
      <div className="chart-card">
        <h3>📈 Predicción de gasto</h3>
        <div className="loading-state">{data?.error || 'Sin datos'}</div>
      </div>
    )
  }

  const { history, prediction, r2_score } = data

  // Combinar historial + predicción en una sola serie
  const chartData = history.map(h => ({
    month: h.month,
    gasto_real: Math.round(h.expense),
    ingreso_real: Math.round(h.income),
    prediccion: null
  }))

  // Agregar el punto de predicción
  chartData.push({
    month: prediction.month,
    gasto_real: null,
    ingreso_real: null,
    prediccion: Math.round(prediction.predicted_expense)
  })

  const quality = r2_score >= 0.7 ? '🟢 Alta' : r2_score >= 0.4 ? '🟡 Media' : r2_score >= 0 ? '🔴 Baja' : '⚠️ Datos irregulares'

  return (
    <div className="chart-card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
        <div>
          <h3>📈 Predicción de gasto</h3>
          <p style={{ fontSize: 12, color: 'var(--gray-500)', marginTop: 2 }}>
            Próximo mes estimado: <strong style={{ color: '#f59e0b' }}>${prediction.predicted_expense.toLocaleString()}</strong>
          </p>
        </div>
        <div style={{ fontSize: 11, color: 'var(--gray-500)', textAlign: 'right' }}>
          Precisión del modelo<br />
          <span style={{ fontWeight: 600 }}>{quality} (R²: {r2_score})</span>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={220}>
        <ComposedChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis dataKey="month" tick={{ fontSize: 11 }} />
          <YAxis tick={{ fontSize: 11 }} width={55} />
          <Tooltip formatter={(v) => v ? `$${v.toLocaleString()}` : '-'} />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Bar dataKey="gasto_real" name="Gasto real" fill="#ef4444" opacity={0.7} radius={[3, 3, 0, 0]} />
          <Bar dataKey="ingreso_real" name="Ingreso real" fill="#22c55e" opacity={0.7} radius={[3, 3, 0, 0]} />
          <Line
            dataKey="prediccion"
            name="Predicción"
            stroke="#f59e0b"
            strokeWidth={2}
            strokeDasharray="6 3"
            dot={{ fill: '#f59e0b', r: 6 }}
            connectNulls={false}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}

export default ForecastChart
