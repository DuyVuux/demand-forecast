import api from '../api'
import { useRef, useState } from 'react'

const MODE_LABELS = {
  product: 'Dự báo theo sản phẩm',
  product_customer: 'Dự báo theo sản phẩm & khách hàng',
}

export default function ForecastForm({ mode, onResult, onLoading, onError }) {
  const fileRef = useRef(null)
  const [horizon, setHorizon] = useState(7)
  const [model, setModel] = useState('arima')

  const handleSubmit = async (e) => {
    e.preventDefault()
    onError('')
    if (!fileRef.current?.files?.[0]) {
      onError('Vui lòng chọn file CSV.')
      return
    }
    const form = new FormData()
    form.append('file', fileRef.current.files[0])
    form.append('horizon', String(horizon))
    form.append('model', model)
    const path = mode === 'product' ? '/forecast/product' : '/forecast/product_customer'
    try {
      onLoading(true)
      const res = await api.post(path, form, { headers: { 'Content-Type': 'multipart/form-data' } })
      onResult(res.data)
    } catch (err) {
      const msg = err?.response?.data?.detail || err.message || 'Lỗi khi gọi API'
      onError(msg)
    } finally {
      onLoading(false)
    }
  }

  return (
    <form className="form" onSubmit={handleSubmit}>
      <h2>{MODE_LABELS[mode]}</h2>
      <div className="form-row">
        <label>File CSV</label>
        <input type="file" accept=".csv,text/csv" ref={fileRef} />
      </div>
      <div className="form-row">
        <label>Số ngày dự báo</label>
        <input type="number" min="1" max="90" value={horizon} onChange={(e) => setHorizon(parseInt(e.target.value || '1'))} />
      </div>
      <div className="form-row">
        <label>Model</label>
        <select value={model} onChange={(e) => setModel(e.target.value)}>
          <option value="arima">ARIMA</option>
          <option value="linreg">Linear Regression</option>
          <option value="rf">RandomForest</option>
        </select>
      </div>
      <div className="form-row">
        <button type="submit">Chạy dự báo</button>
      </div>
      <div className="hint">
        Định dạng CSV:
        {mode === 'product' ? ' product_id,date,quantity_sold' : ' product_id,customer_id,date,quantity_sold'}
      </div>
    </form>
  )
}
