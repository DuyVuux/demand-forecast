import { useMemo, useState } from 'react';
import api from '../api';
import PCForecastChart from '../components/PCForecastChart.jsx';
import {
  Container, Typography, Paper, Grid, TextField, Button, Select, MenuItem, FormControl, InputLabel, CircularProgress, Alert, Card, CardContent, CardHeader, Box, Tooltip
} from '@mui/material';
import ScienceIcon from '@mui/icons-material/Science';
import SecurityIcon from '@mui/icons-material/Security';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';

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
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom sx={{ fontWeight: 'bold', color: 'primary.main' }}>
        Dự báo theo Nhóm sản phẩm (SP-KH)
      </Typography>

      <Paper elevation={3} sx={{ p: 3, mb: 4 }}>
        <Grid container spacing={3} alignItems="flex-end">
          <Grid item xs={12} sm={4}>
            <TextField
              fullWidth
              label="Mã khách hàng (CustomerCode)"
              value={customerCode}
              onChange={(e) => setCustomerCode(e.target.value)}
              variant="outlined"
            />
          </Grid>
          <Grid item xs={12} sm={4}>
            <TextField
              fullWidth
              label="Mã sản phẩm (ProductCode)"
              value={productCode}
              onChange={(e) => setProductCode(e.target.value)}
              variant="outlined"
            />
          </Grid>
          <Grid item xs={12} sm={2}>
            <FormControl fullWidth variant="outlined">
              <InputLabel>Mô hình dự báo</InputLabel>
              <Select value={model} onChange={(e) => setModel(e.target.value)} label="Mô hình dự báo">
                {modelOptions.map((m) => (<MenuItem key={m} value={m}>{m}</MenuItem>))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={2}>
            <Button
              fullWidth
              variant="contained"
              color="primary"
              size="large"
              onClick={handleForecast}
              disabled={loading}
              startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <ScienceIcon />}
            >
              {loading ? 'Đang xử lý...' : 'Dự báo'}
            </Button>
          </Grid>
        </Grid>
      </Paper>

      {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}

      {record && (
        <Box>
          {/* Chart Section */}
          <Card elevation={3} sx={{ mb: 3 }}>
            <CardHeader
              title={`Biểu đồ dự báo: ${record.product_code} | ${record.customer_code}`}
              subheader={`Mô hình: ${record.model}`}
            />
            <CardContent>
              <PCForecastChart record={chartRecord} />
            </CardContent>
          </Card>

          {/* Results and Safety Stock Section */}
          <Grid container spacing={3}>
            <Grid item xs={12} md={5} lg={4}>
              <Card elevation={3} sx={{ height: '100%' }}>
                <CardHeader title="Kết quả dự báo" />
                <CardContent>
                  <Typography variant="body1" gutterBottom><strong>MAE:</strong> {record.metrics?.MAE?.toLocaleString()}</Typography>
                  <Typography variant="body1" gutterBottom><strong>RMSE:</strong> {record.metrics?.RMSE?.toLocaleString()}</Typography>
                  <Typography variant="body1" gutterBottom><strong>MAPE:</strong> {record.metrics?.MAPE ? `${(record.metrics.MAPE * 100).toFixed(2)}%` : 'N/A'}</Typography>
                  <hr />
                  <Typography variant="h6" sx={{ mt: 2 }}><strong>Tổng lượng cần nhập:</strong></Typography>
                  <Typography variant="h5" color="primary">{record.total_qty?.toLocaleString()}</Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={7} lg={8}>
              <Card elevation={3} sx={{ height: '100%' }}>
                <CardHeader title="Tính toán Tồn kho An toàn (Safety Stock)" />
                <CardContent>
                  <Grid container spacing={2}>
                    <Grid item xs={12} sm={4}>
                      <Tooltip title="Tỷ lệ đáp ứng đơn hàng mong muốn, ví dụ: 0.95 tương đương 95%.">
                        <TextField fullWidth label="Mức độ phục vụ (Service Level)" type="number" value={serviceLevel} onChange={(e) => setServiceLevel(parseFloat(e.target.value))} InputProps={{ inputProps: { min: 0.01, max: 0.99, step: 0.01 } }} variant="outlined" />
                      </Tooltip>
                    </Grid>
                    <Grid item xs={12} sm={4}>
                      <Tooltip title="Thời gian trung bình (tính bằng ngày) kể từ khi đặt hàng cho đến khi nhận được hàng.">
                        <TextField fullWidth label="Thời gian chờ (Lead Time)" type="number" value={leadTime} onChange={(e) => setLeadTime(parseInt(e.target.value, 10))} InputProps={{ inputProps: { min: 1 } }} variant="outlined" />
                      </Tooltip>
                    </Grid>
                    <Grid item xs={12} sm={4}>
                      <Tooltip title="Độ lệch chuẩn của thời gian chờ, phản ánh sự biến động của chuỗi cung ứng.">
                        <TextField fullWidth label="Độ lệch chuẩn Lead Time" type="number" value={leadTimeStd} onChange={(e) => setLeadTimeStd(parseFloat(e.target.value))} InputProps={{ inputProps: { min: 0 } }} variant="outlined" />
                      </Tooltip>
                    </Grid>
                    <Grid item xs={12}>
                      <Button fullWidth variant="contained" color="secondary" size="large" onClick={handleCalculateSafetyStock} disabled={isCalculating || !record} startIcon={isCalculating ? <CircularProgress size={20} color="inherit" /> : <SecurityIcon />}>
                        {isCalculating ? 'Đang tính...' : 'Tính Tồn kho'}
                      </Button>
                    </Grid>
                  </Grid>
                  {safetyStockResult && (
                    <Box sx={{ mt: 3, p: 2.5, borderRadius: 2, textAlign: 'center', background: (theme) => theme.palette.primary.main, color: 'white' }}>
                      <Typography variant="h6" component="p" sx={{ fontWeight: 'medium' }}>
                        Tồn kho an toàn (Safety Stock)
                      </Typography>
                      <Typography variant="h4" component="p" sx={{ fontWeight: 'bold', mt: 1 }}>
                        {Math.round(safetyStockResult.safetyStock).toLocaleString()}
                      </Typography>
                    </Box>
                  )}
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Box>
      )}
    </Container>
  );
}
