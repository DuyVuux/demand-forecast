import { useState } from 'react'
import ForecastForm from './components/ForecastForm.jsx'
import ForecastTable from './components/ForecastTable.jsx'
import ForecastChart from './components/ForecastChart.jsx'
import './styles.css'
import { Link } from 'react-router-dom'

export default function App() {
  const [mode, setMode] = useState('product')
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')

  const handleResult = (data) => {
    setResult(data)
    setError('')
  }

  return (
    <div className="container">
      <h1>Demand Forecasting  </h1>
      <div className="card" style={{ marginBottom: 12, display: 'flex', gap: 16 }}>
        <Link to="/data-analysis">→ Chuyển sang trang Data Analysis</Link>
        <span style={{ opacity: 0.6 }}>|</span>
        <Link to="/sku-forecast">Xem dự báo SKU (theo từng sản phẩm)</Link>
        <span style={{ opacity: 0.6 }}>|</span>
        <Link to="/pc-forecast">Xem dự báo SP-KH</Link>
        <span style={{ opacity: 0.6 }}>|</span>
        <Link to="/login">Đăng nhập</Link>
      </div>
      <div className="mode-switch">
        <button className={mode === 'product' ? 'active' : ''} onClick={() => { setMode('product'); setResult(null) }}>Dự báo theo từng sản phẩm</button>
        <button className={mode === 'product_customer' ? 'active' : ''} onClick={() => { setMode('product_customer'); setResult(null) }}>Dự báo theo từng khách hàng</button>
      </div>

      <ForecastForm mode={mode} onResult={handleResult} onLoading={() => {}} onError={setError} />

      {error && <div className="error">{error}</div>}

      {result && (
        <>
          <ForecastChart data={result} />
          <ForecastTable data={result} />
        </>
      )}

      <footer>
        <p>Backend: FastAPI (port 8010) | Frontend: React Vite (port 3004/3005)</p>
      </footer>
    </div>
  )
}
