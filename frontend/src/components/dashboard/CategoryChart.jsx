import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts'

const COLORS = ['#22c55e', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#f97316', '#ec4899']

const CategoryChart = ({ transactions, categories }) => {
  const catMap = {}
  categories.forEach(c => { catMap[c.id] = c.name })

  const grouped = {}
  transactions
    .filter(t => t.type === 'expense')
    .forEach(t => {
      const name = catMap[t.category_id] || 'Sin categoría'
      grouped[name] = (grouped[name] || 0) + parseFloat(t.amount)
    })

  const data = Object.entries(grouped)
    .map(([name, value]) => ({ name, value: Math.round(value) }))
    .sort((a, b) => b.value - a.value)
    .slice(0, 8)

  if (data.length === 0) {
    return (
      <div className="chart-card">
        <h3>Gastos por categoría</h3>
        <div className="loading-state">Sin datos</div>
      </div>
    )
  }

  return (
    <div className="chart-card">
      <h3>Gastos por categoría</h3>
      <ResponsiveContainer width="100%" height={200}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={50}
            outerRadius={80}
            dataKey="value"
          >
            {data.map((_, i) => (
              <Cell key={i} fill={COLORS[i % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip formatter={(v) => `$${v.toLocaleString()}`} />
          <Legend wrapperStyle={{ fontSize: 11 }} />
        </PieChart>
      </ResponsiveContainer>
    </div>
  )
}

export default CategoryChart
