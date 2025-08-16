import { useEffect, useMemo, useState } from 'react';
import api from '../api';
import SkuForecastChart from '../components/SkuForecastChart.jsx';
import styles from './SkuForecastPage.module.css';

export default function SkuForecastPage() {
  const [productCode, setProductCode] = useState('');
  const [model, setModel] = useState('');
  const [modelOptions, setModelOptions] = useState([]);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [forecastResult, setForecastResult] = useState(null);

  // State for Safety Stock calculation
  const [ssParams, setSsParams] = useState({ serviceLevel: 0.95, leadTime: 7, leadTimeStd: 1.5 });
  const [ssLoading, setSsLoading] = useState(false);
  const [ssError, setSsError] = useState('');
  const [safetyStock, setSafetyStock] = useState(null);

  useEffect(() => {
    async function fetchModels() {
      try {
        const res = await api.get('/forecast/sku/models');
        const models = res.data?.models || [];
        setModelOptions(models);
        if (models.length > 0) {
          setModel(models[0]);
        }
      } catch (e) {
        console.error('Failed to fetch SKU models:', e);
        setError('Không thể tải danh sách mô hình.');
      }
    }
    fetchModels();
  }, []);

  const canQuery = useMemo(() => {
    return Boolean(productCode?.trim()) && Boolean(model?.trim());
  }, [productCode, model]);

  const handleSsParamChange = (e) => {
    const { name, value } = e.target;
    setSsParams(prev => ({ ...prev, [name]: parseFloat(value) || 0 }));
  };

  async function handleCalculateSafetyStock() {
    if (!forecastResult) {
      setSsError('Vui lòng chạy dự báo chính trước khi tính tồn kho an toàn.');
      return;
    }

    setSsLoading(true);
    setSsError('');
    setSafetyStock(null);

    const payload = {
      product_code: forecastResult.product_code,
      model: forecastResult.model,
      service_level: ssParams.serviceLevel,
      lead_time: ssParams.leadTime,
      lead_time_std: ssParams.leadTimeStd,
    };

    try {
      const res = await api.post('/forecast/safety-stock', payload);
      setSafetyStock(res.data.safety_stock);
      if (res.data.chart_data) {
        setForecastResult(prev => ({ ...prev, chart_data: res.data.chart_data }));
      }
    } catch (e) {
      const errorMsg = e?.response?.data?.detail || e?.message || 'Lỗi tính toán tồn kho an toàn';
      setSsError(errorMsg);
    } finally {
      setSsLoading(false);
    }
  }

  async function handleForecast() {
    if (!canQuery) return;

    setLoading(true);
    setError('');
    setForecastResult(null);
    setSafetyStock(null);
    setSsError('');

    const params = {
      product_code: productCode.trim(),
      model: model.trim(),
    };

    try {
      const res = await api.get('/forecast/sku', { params });
      setForecastResult(res.data);
    } catch (e) {
      const errorMsg = e?.response?.data?.detail || e?.message || 'Lỗi tải dữ liệu';
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className={styles.pageContainer}>
      <h1 className={styles.pageHeader}>Dự báo theo từng sản phẩm (SKU)</h1>

      <div className={styles.formSection}>
        <div className={styles.formGrid}>
          <div className={styles.formGroup}>
            <label className={styles.label}>Mã sản phẩm (SKU)</label>
            <input
              className={styles.input}
              type="text"
              value={productCode}
              onChange={(e) => setProductCode(e.target.value)}
              placeholder="VD: 20100002"
            />
          </div>
          <div className={styles.formGroup}>
            <label className={styles.label}>Mô hình</label>
            <select className={styles.select} value={model} onChange={(e) => setModel(e.target.value)}>
              {modelOptions.map((m) => <option key={m} value={m}>{m}</option>)}
            </select>
          </div>
          <div className={styles.formGroup}>
            <button className={styles.button} onClick={handleForecast} disabled={!canQuery || loading}>
              {loading ? 'Đang tải...' : 'Dự báo'}
            </button>
          </div>
        </div>
        {error && <div className={styles.error}>{error}</div>}
      </div>

      {loading && <div className={styles.loadingMessage}>Đang tải kết quả...</div>}

      {forecastResult && (
        <div className={styles.resultsSection}>
          {/* Forecast Metrics */}
          <div className={`${styles.card} ${styles.metricsCard}`}>
            <h2>Kết quả dự báo</h2>
            <p><strong>Mô hình:</strong> {forecastResult.model || 'N/A'}</p>
            <p><strong>MAE:</strong> {forecastResult.metrics?.MAE?.toFixed(2) ?? 'N/A'}</p>
            <p><strong>RMSE:</strong> {forecastResult.metrics?.RMSE?.toFixed(2) ?? 'N/A'}</p>
            <p><strong>MAPE:</strong> {`${forecastResult.metrics?.MAPE?.toFixed(2) ?? 'N/A'}%`}</p>
            <p className={styles.highlightResult}>
              <strong>Tổng lượng hàng cần nhập:</strong> {forecastResult.forecast_quantity?.toLocaleString() ?? 'N/A'}
            </p>
          </div>

          {/* Safety Stock Calculation */}
          <div className={styles.card}>
            <h2>Tính Tồn kho An toàn (Safety Stock)</h2>
            <div className={styles.formGrid}>
              <div className={styles.formGroup}>
                <label className={styles.label}>Mức độ dịch vụ</label>
                <input className={styles.input} type="number" name="serviceLevel" value={ssParams.serviceLevel} onChange={handleSsParamChange} step="0.01" min="0.01" max="0.99" />
              </div>
              <div className={styles.formGroup}>
                <label className={styles.label}>Thời gian chờ (ngày)</label>
                <input className={styles.input} type="number" name="leadTime" value={ssParams.leadTime} onChange={handleSsParamChange} min="0" />
              </div>
              <div className={styles.formGroup}>
                <label className={styles.label}>Độ lệch chuẩn LT</label>
                <input className={styles.input} type="number" name="leadTimeStd" value={ssParams.leadTimeStd} onChange={handleSsParamChange} min="0" />
              </div>
              <div className={styles.formGroup}>
                <button className={styles.button} onClick={handleCalculateSafetyStock} disabled={ssLoading}>
                  {ssLoading ? 'Đang tính...' : 'Tính Safety Stock'}
                </button>
              </div>
            </div>
            {ssError && <div className={styles.error}>{ssError}</div>}
            {safetyStock !== null && (
              <div className={styles.safetyStockResultCard}>
                <p>Tồn kho an toàn (Safety Stock): {safetyStock.toLocaleString()}</p>
              </div>
            )}
          </div>

          {/* Chart */}
          {forecastResult.chart_data && (
            <div className={styles.card}>
              <h2>Biểu đồ dự báo</h2>
              <SkuForecastChart record={forecastResult.chart_data} />
            </div>
          )}
        </div>
      )}
    </div>
  );
}
