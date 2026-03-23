import { useState, useEffect } from 'react'
import Sidebar from '../components/Sidebar'
import StatsCard from '../components/dashboard/StatsCard'
import MonthlyChart from '../components/dashboard/MonthlyChart'
import CategoryChart from '../components/dashboard/CategoryChart'
import TransactionList from '../components/dashboard/TransactionList'
import { getTransactions, getCategories } from '../api/dashboard'

const DashboardPage = () => {
  const [transactions, setTransactions] = useState([])
  const [categories, setCategories] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const load = async () => {
      try {
        const [txs, cats] = await Promise.all([getTransactions(), getCategories()])
        setTransactions(txs)
        setCategories(cats)
      } catch {
        console.error('Error cargando datos del dashboard')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  const now = new Date()
  const currentMonth = now.getMonth()
  const currentYear = now.getFullYear()

  const monthTxs = transactions.filter(t => {
    const d = new Date(t.transaction_date)
    return d.getMonth() === currentMonth && d.getFullYear() === currentYear
  })

  const ingresos = monthTxs.filter(t => t.type === 'income').reduce((s, t) => s + parseFloat(t.amount), 0)
  const gastos = monthTxs.filter(t => t.type === 'expense').reduce((s, t) => s + parseFloat(t.amount), 0)
  const balance = ingresos - gastos

  return (
    <div className="layout">
      <Sidebar conversations={[]} currentConvId={null} onSelectConv={() => {}} />
      <div className="main-content">
        <div className="dashboard-content">
          <div className="dashboard-header">
            <h1>Panel de finanzas</h1>
            <p>Resumen del mes actual</p>
          </div>

          {loading ? (
            <div className="loading-state">Cargando datos...</div>
          ) : (
            <>
              <div className="stats-grid">
                <StatsCard label="Ingresos del mes" value={ingresos} icon="📈" type="income" />
                <StatsCard label="Gastos del mes" value={gastos} icon="📉" type="expense" />
                <StatsCard label="Balance" value={balance} icon="💰" type="balance" />
              </div>

              <div className="charts-grid">
                <MonthlyChart transactions={transactions} />
                <CategoryChart transactions={transactions} categories={categories} />
              </div>

              <TransactionList transactions={transactions} categories={categories} />
            </>
          )}
        </div>
      </div>
    </div>
  )
}

export default DashboardPage
