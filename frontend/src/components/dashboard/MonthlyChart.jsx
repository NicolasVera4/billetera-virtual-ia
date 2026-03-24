import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

const MONTH_NAMES = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']

const MonthlyChart = ({ transactions }) => {
  const now = new Date()
  const data = []

  for (let i = 5; i >= 0; i--) {
    const d = new Date(now.getFullYear(), now.getMonth() - i, 1)
    const m = d.getMonth()
    const y = d.getFullYear()

    const monthTxs = transactions.filter(t => {
      const td = new Date(t.transaction_date)
      return td.getMonth() === m && td.getFullYear() === y
    })

    const ingresos = monthTxs.filter(t => t.type === 'income').reduce((s, t) => s + parseFloat(t.amount), 0)
    const gastos = monthTxs.filter(t => t.type === 'expense').reduce((s, t) => s + parseFloat(t.amount), 0)

    data.push({ month: MONTH_NAMES[m], Ingresos: Math.round(ingresos), Gastos: Math.round(gastos) })
  }

  return (
    <div className="chart-card">
      <h3>Flujo mensual</h3>
      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis dataKey="month" tick={{ fontSize: 12 }} />
          <YAxis tick={{ fontSize: 12 }} width={50} />
          <Tooltip formatter={(v) => `$${v.toLocaleString()}`} />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Line type="monotone" dataKey="Ingresos" stroke="#22c55e" strokeWidth={2} dot={false} />
          <Line type="monotone" dataKey="Gastos" stroke="#ef4444" strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

export default MonthlyChart
