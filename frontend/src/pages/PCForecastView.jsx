import { useEffect, useMemo, useState } from 'react';
import api from '../api';
import PCForecastChart from '../components/PCForecastChart.jsx';
import styles from './PCForecastView.module.css';

export default function PCForecastView() {
  // State for forecast selection
  const [customerCode, setCustomerCode] = useState('C0003413');
  const [productCode, setProductCode] = useState('20100054');
  const modelOptions = ['Random Forest', 'XGBoost', 'Croston', 'SARIMA'];
  const [model, setModel] = useState(modelOptions[0]);
  const [record, setRecord] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // State for safety stock calculation
  const [serviceLevel, setServiceLevel] = useState(0.95);
  const [leadTime, setLeadTime] = useState(7);
  const [leadTimeStd, setLeadTimeStd] = useState(1.5);
  const [isCalculating, setIsCalculating] = useState(false);
  const [safetyStockResult, setSafetyStockResult] = useState(null);

  async function handleForecast() {
    if (!customerCode?.trim() || !productCode?.trim()) {
      setError('Vui lòng nhập CustomerCode và ProductCode.');
      return;
    }
    setLoading(true);
    setError('');
    setRecord(null);
    setSafetyStockResult(null); // Reset safety stock on new forecast

    const params = {
      customer_code: customerCode.trim(),
      product_code: productCode.trim(),
      model: model,
    };

    try {
      const res = await api.get('/pc-forecast', { params });
      if (res.data?.data) {
        setRecord(res.data.data);
      } else {
        setRecord(null);
        setError('Không tìm thấy dữ liệu cho mã SP-KH và mô hình đã chọn.');
      }
    } catch (e) {
      setError(e?.response?.data?.detail || e?.message || 'Lỗi tải dữ liệu');
    } finally {
      setLoading(false);
    }
  }

  async function handleCalculateSafetyStock() {
    if (!record) {
      setError('Vui lòng chạy dự báo trước khi tính tồn kho an toàn.');
      return;
    }
    if (!(serviceLevel > 0 && serviceLevel < 1)) {
      setError('Service Level phải là một số trong khoảng (0, 1).');
      return;
    }
    if (leadTime <= 0) {
      setError('Lead Time phải lớn hơn 0.');
      return;
    }
    if (leadTimeStd < 0) {
      setError('Lead Time Std không được âm.');
      return;
    }

    setIsCalculating(true);
    setError('');

    const payload = {
      customerId: record.customer_code,
      productId: record.product_code,
      model: record.model,
      serviceLevel,
      leadTime,
      leadTimeStd,
    };

    try {
      const res = await api.post('/pc-forecast/safety-stock', payload);
      setSafetyStockResult(res.data);
    } catch (e) {
      setError(e?.response?.data?.detail || e?.message || 'Lỗi tính toán tồn kho an toàn');
      setSafetyStockResult(null);
    } finally {
      setIsCalculating(false);
    }
  }

  const chartRecord = useMemo(() => {
    if (safetyStockResult) {
      const history = safetyStockResult.chartData.filter(d => d.type === 'history').map(d => ({ date: d.date, actual: d.value }));
      const forecast = safetyStockResult.chartData.filter(d => d.type === 'forecast').map(d => ({ date: d.date, yhat: d.value }));
      return { ...record, history, forecast };
    }
    return record;
  }, [record, safetyStockResult]);

  return (
    <div className={styles.pageContainer}>
      <h1 className={styles.pageHeader}>Dự báo theo Nhóm sản phẩm (SP-KH)</h1>

      <div className={styles.formSection}>
        <div className={styles.formGrid}>
          <div className={styles.formGroup}>
            <label className={styles.label}>Mã khách hàng (CustomerCode)</label>
            <input className={styles.input} value={customerCode} onChange={(e) => setCustomerCode(e.target.value)} placeholder="Nhập mã khách hàng..." />
          </div>
          <div className={styles.formGroup}>
            <label className={styles.label}>Mã sản phẩm (ProductCode)</label>
            <input className={styles.input} value={productCode} onChange={(e) => setProductCode(e.target.value)} placeholder="Nhập mã sản phẩm..." />
          </div>
          <div className={styles.formGroup}>
            <label className={styles.label}>Mô hình dự báo</label>
            <select className={styles.select} value={model} onChange={(e) => setModel(e.target.value)}>
              {modelOptions.map((m) => (<option key={m} value={m}>{m}</option>))}
            </select>
          </div>
          <div className={styles.formGroup}>
             <button className={styles.button} onClick={handleForecast} disabled={loading}>
              {loading ? 'Đang xử lý...' : 'Dự báo'}
            </button>
          </div>
        </div>
      </div>

      {error && <div className={styles.error}>{error}</div>}

      {chartRecord && (
        <div className={styles.resultsSection}>
          <h3>Biểu đồ dự báo: {chartRecord.product_code} | {chartRecord.customer_code}</h3>
          <PCForecastChart record={chartRecord} />

          <div className={styles.safetyStockSection}>
            <h4>Tính toán Tồn kho An toàn (Safety Stock)</h4>
            <div className={styles.formGrid}>
              <div className={styles.formGroup}>
                <label className={styles.label}>Mức độ phục vụ (Service Level)</label>
                <input className={styles.input} type="number" step="0.01" min="0.01" max="0.99" value={serviceLevel} onChange={(e) => setServiceLevel(parseFloat(e.target.value))} />
              </div>
              <div className={styles.formGroup}>
                <label className={styles.label}>Thời gian chờ (Lead Time - ngày)</label>
                <input className={styles.input} type="number" min="1" value={leadTime} onChange={(e) => setLeadTime(parseInt(e.target.value, 10))} />
              </div>
              <div className={styles.formGroup}>
                <label className={styles.label}>Độ lệch chuẩn Lead Time (ngày)</label>
                <input className={styles.input} type="number" min="0" value={leadTimeStd} onChange={(e) => setLeadTimeStd(parseFloat(e.target.value))} />
              </div>
              <div className={styles.formGroup}>
                <button className={styles.button} onClick={handleCalculateSafetyStock} disabled={isCalculating || !record}>
                  {isCalculating ? 'Đang tính...' : 'Tính Tồn kho'}
                </button>
              </div>
            </div>
          </div>

          {safetyStockResult && (
            <div className={styles.resultsCard}>
              <h6>Kết quả tính toán</h6>
              <p><strong>Demand Mean (Lịch sử):</strong> {safetyStockResult.demandMean.toLocaleString()}</p>
              <p><strong>Demand Std Dev (Lịch sử):</strong> {safetyStockResult.demandStd.toLocaleString()}</p>
              <p className={styles.highlightResult}>
                <strong>Tồn kho an toàn (Safety Stock):</strong> {Math.round(safetyStockResult.safetyStock).toLocaleString()}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
