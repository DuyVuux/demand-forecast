import { useEffect, useMemo, useState } from 'react';
import api from '../api';
import SkuForecastChart from '../components/SkuForecastChart.jsx';
import {
  Container, Typography, Paper, Grid, TextField, Button, Select, MenuItem, FormControl, InputLabel, CircularProgress, Alert, Card, CardContent, CardHeader, Box, Tooltip, Table, TableBody, TableCell, TableContainer, TableHead, TableRow
} from '@mui/material';
import QueryStatsIcon from '@mui/icons-material/QueryStats';
import SecurityIcon from '@mui/icons-material/Security';

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
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom sx={{ fontWeight: 'bold', color: 'primary.main' }}>
        Dự báo theo từng sản phẩm (SKU)
      </Typography>

      <Paper elevation={3} sx={{ p: 3, mb: 4 }}>
        <Grid container spacing={3} alignItems="center">
          <Grid item xs={12} sm={5}>
            <TextField
              fullWidth
              label="Mã sản phẩm (SKU)"
              value={productCode}
              onChange={(e) => setProductCode(e.target.value)}
              placeholder="VD: 20100002"
              variant="outlined"
            />
          </Grid>
          <Grid item xs={12} sm={4}>
            <FormControl fullWidth variant="outlined">
              <InputLabel>Mô hình</InputLabel>
              <Select value={model} onChange={(e) => setModel(e.target.value)} label="Mô hình">
                {modelOptions.map((m) => <MenuItem key={m} value={m}>{m}</MenuItem>)}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={3}>
            <Button
              fullWidth
              variant="contained"
              color="primary"
              size="large"
              onClick={handleForecast}
              disabled={!canQuery || loading}
              startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <QueryStatsIcon />}
            >
              {loading ? 'Đang tải...' : 'Dự báo'}
            </Button>
          </Grid>
        </Grid>
        {error && <Alert severity="error" sx={{ mt: 3 }}>{error}</Alert>}
      </Paper>

      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
          <CircularProgress />
          <Typography variant="h6" sx={{ ml: 2 }}>Đang tải kết quả...</Typography>
        </Box>
      )}

      {forecastResult && (
        <Box>
          {/* Chart Section */}
          {forecastResult.chart_data && (
            <Card elevation={3} sx={{ mb: 4 }}>
              <CardHeader title="Biểu đồ dự báo" />
              <CardContent>
                <SkuForecastChart record={forecastResult.chart_data} />
              </CardContent>
            </Card>
          )}

          {/* Results and Safety Stock Section */}
          <Grid container spacing={3}>
            <Grid item xs={12} md={5} lg={4}>
              <Card elevation={3} sx={{ height: '100%' }}>
                <CardHeader
                  title="Kết quả dự báo"
                  avatar={<QueryStatsIcon />}
                />
                <CardContent>
                  <TableContainer>
                    <Table size="small">
                      <TableBody>
                        <TableRow><TableCell>MAE</TableCell><TableCell align="right">{forecastResult.metrics?.MAE?.toFixed(2) ?? 'N/A'}</TableCell></TableRow>
                        <TableRow><TableCell>RMSE</TableCell><TableCell align="right">{forecastResult.metrics?.RMSE?.toFixed(2) ?? 'N/A'}</TableCell></TableRow>
                        <TableRow><TableCell>MAPE</TableCell><TableCell align="right">{`${forecastResult.metrics?.MAPE?.toFixed(2) ?? 'N/A'}%`}</TableCell></TableRow>
                      </TableBody>
                    </Table>
                  </TableContainer>
                  <Box sx={{ mt: 3, p: 2, borderRadius: 2, textAlign: 'center', background: (theme) => theme.palette.primary.main, color: 'white' }}>
                    <Typography variant="subtitle1" sx={{ fontWeight: 'medium' }}>Tổng lượng hàng cần nhập</Typography>
                    <Typography variant="h5" sx={{ fontWeight: 'bold' }}>{forecastResult.forecast_quantity?.toLocaleString() ?? 'N/A'}</Typography>
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={7} lg={8}>
              <Card elevation={3} sx={{ height: '100%' }}>
                <CardHeader title="Tính Tồn kho An toàn (Safety Stock)" />
                <CardContent>
                  <Grid container spacing={2} alignItems="center">
                    <Grid item xs={12} sm={6} md={3}>
                      <Tooltip title="Xác suất đáp ứng nhu cầu khách hàng (0.01 - 0.99)">
                        <TextField fullWidth label="Mức độ dịch vụ" type="number" name="serviceLevel" value={ssParams.serviceLevel} onChange={handleSsParamChange} InputProps={{ inputProps: { step: 0.01, min: 0.01, max: 0.99 } }} />
                      </Tooltip>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                      <Tooltip title="Thời gian chờ hàng trung bình (ngày)">
                        <TextField fullWidth label="Lead Time (ngày)" type="number" name="leadTime" value={ssParams.leadTime} onChange={handleSsParamChange} InputProps={{ inputProps: { min: 0 } }} />
                      </Tooltip>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                      <Tooltip title="Độ lệch chuẩn của thời gian chờ">
                        <TextField fullWidth label="Độ lệch chuẩn LT" type="number" name="leadTimeStd" value={ssParams.leadTimeStd} onChange={handleSsParamChange} InputProps={{ inputProps: { min: 0 } }} />
                      </Tooltip>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                      <Button fullWidth variant="contained" color="secondary" onClick={handleCalculateSafetyStock} disabled={ssLoading} startIcon={ssLoading ? <CircularProgress size={20} /> : <SecurityIcon />}>
                        {ssLoading ? 'Đang tính...' : 'Tính'}
                      </Button>
                    </Grid>
                  </Grid>
                  {ssError && <Alert severity="error" sx={{ mt: 2 }}>{ssError}</Alert>}
                  {safetyStock !== null && (
                    <Alert severity="success" sx={{ mt: 2 }}>
                      <Typography sx={{ fontWeight: 'bold' }}>
                        Tồn kho an toàn (Safety Stock): {safetyStock.toLocaleString()}
                      </Typography>
                    </Alert>
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
