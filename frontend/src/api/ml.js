import axios from 'axios'

const API = axios.create({ baseURL: 'http://localhost:8000' })

export const getForecast = async () => {
  const res = await API.get('/ml/forecast')
  return res.data
}

export const getAnomalies = async () => {
  const res = await API.get('/ml/anomalies')
  return res.data
}
