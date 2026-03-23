import axios from 'axios'

const API = axios.create({ baseURL: 'http://localhost:8000' })

export const getTransactions = async () => {
  const res = await API.get('/transactions')
  return res.data
}

export const getCategories = async () => {
  const res = await API.get('/categories')
  return res.data
}
