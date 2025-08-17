import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import api from '../api';
import { Bar } from 'react-chartjs-2';
import { Chart as ChartJS, LineElement, BarElement, CategoryScale, LinearScale, PointElement, Tooltip, Legend, TimeScale } from 'chart.js';
import {
  Container, Typography, Button, Box, Paper, Grid, CircularProgress, Alert, Card, CardContent, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Checkbox, Tooltip as MuiTooltip, FormControl, Select, MenuItem, Chip
} from '@mui/material';
import { UploadFile as UploadFileIcon, CloudUpload as CloudUploadIcon, Download as DownloadIcon } from '@mui/icons-material';

ChartJS.register(LineElement, BarElement, CategoryScale, LinearScale, PointElement, Tooltip, Legend, TimeScale);

const POLLING_INTERVAL = 5000;
const MemoizedBar = React.memo(Bar);

// --- Child Components for DataAnalysis Page ---

const UploadSection = ({ onUpload, onFileChange, file, status, dragging, dragHandlers }) => (
  <Paper
    variant="outlined"
    {...dragHandlers}
    sx={{
      p: 4, 
      textAlign: 'center', 
      borderStyle: 'dashed',
      borderColor: dragging ? 'primary.main' : 'divider',
      backgroundColor: dragging ? 'action.hover' : 'background.paper',
      transition: 'all 0.2s ease-in-out',
      mb: 2
    }}
  >
    <input type="file" id="file-upload" onChange={onFileChange} accept=".csv,.xlsx" style={{ display: 'none' }} />
    <CloudUploadIcon sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
    <Typography variant="h6" gutterBottom>
      Kéo và thả tệp vào đây, hoặc
    </Typography>
    <Button variant="contained" component="label" htmlFor="file-upload" sx={{ mb: 2 }}>
      Chọn một tệp
    </Button>
    {file && <Typography variant="body2" color="text.secondary">Tệp đã chọn: {file.name}</Typography>}
    <Box sx={{ mt: 2 }}>
      <Button 
        onClick={onUpload} 
        disabled={!file || status === 'uploading' || status === 'processing'}
        variant="contained"
        size="large"
        startIcon={status === 'uploading' ? <CircularProgress size={20} color="inherit" /> : <UploadFileIcon />}
      >
        {status === 'uploading' ? 'Đang tải lên...' : 'Tải lên & Phân tích'}
      </Button>
    </Box>
  </Paper>
);

const JobStatus = ({ status, error }) => {
  if (error) {
    return <Alert severity="error" sx={{ mb: 2 }}>Lỗi: {error}</Alert>;
  }
  if (status && status !== 'finished' && status !== 'failed' && status !== 'uploading' && status !== 'submitted') {
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
        <Chip label={`Trạng thái: ${status}`} color="info" />
        {status === 'processing' && <CircularProgress size={24} />}
      </Box>
    );
  }
  return null;
};

const SummaryCard = ({ overview, filters, onFilterChange }) => {
  if (!overview || !filters) {
    return null;
  }

  return (
    <Card>
      <CardContent>
        <Typography variant="h5" component="h2" gutterBottom>Tổng quan Dữ liệu</Typography>
        <Typography variant="body1" color="text.secondary" paragraph>{overview.summary}</Typography>
        <TableContainer component={Paper} variant="outlined" sx={{ mb: 2, maxHeight: 500 }}>
          <Table stickyHeader size="small">
            <TableHead>
              <TableRow>
                <TableCell>Tên Cột</TableCell>
                <TableCell>Kiểu dữ liệu</TableCell>
                <TableCell>Số lượng duy nhất</TableCell>
                <TableCell>Số lượng null</TableCell>
                <TableCell>Min</TableCell>
                <TableCell>Max</TableCell>
                <TableCell>Mean</TableCell>
                <TableCell>Median</TableCell>
                
              </TableRow>
            </TableHead>
            <TableBody>
              {overview.columns.map(col => {
                const exclusionReason = filters?.auto_excluded?.[col.name];
                const isIncluded = !(col.name in (filters?.auto_excluded || {})) && !filters?.user_excluded?.includes(col.name);

                return (
                  <TableRow key={col.name}>
                    <TableCell>
                      <MuiTooltip title={exclusionReason ? `Tự động loại trừ: ${exclusionReason}` : 'Bao gồm trong phân tích'}>
                        <span>{col.name}</span>
                      </MuiTooltip>
                    </TableCell>
                    <TableCell>{col.dtype}</TableCell>
                    <TableCell>{col.unique_count}</TableCell>
                    <TableCell>{col.missing_count ?? 0}</TableCell>
                    <TableCell>{col.name === 'Quantity' ? col.min ?? 'N/A' : '-'}</TableCell>
                    <TableCell>{col.name === 'Quantity' ? col.max ?? 'N/A' : '-'}</TableCell>
                    <TableCell>{col.name === 'Quantity' ? col.mean ?? 'N/A' : '-'}</TableCell>
                    <TableCell>{col.name === 'Quantity' ? col.median ?? 'N/A' : '-'}</TableCell>
                    
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </TableContainer>
      </CardContent>
    </Card>
  );
};

const ColumnDetailCard = ({ overview, colName, setColName, colDetail, histChart, barChart, jobId }) => (
  <Card>
    <CardContent>
      <Typography variant="h5" component="h2" gutterBottom>Chi tiết Cột</Typography>
      <FormControl fullWidth sx={{ mb: 2 }}>
        <Select value={colName} onChange={e => setColName(e.target.value)} size="small">
          {overview.columns.map(c => <MenuItem key={c.name} value={c.name}>{c.name}</MenuItem>)}
        </Select>
      </FormControl>
      {colDetail ? (
        <Box>
          <Typography variant="h6">{colDetail.name} ({colDetail.type})</Typography>
          {colDetail.warning && <Alert severity="warning" sx={{ my: 1 }}>{colDetail.warning}</Alert>}
          {colDetail.stats && (
            <Grid container spacing={1} sx={{ my: 2 }}>
              {Object.entries(colDetail.stats).map(([key, value]) => (
                <Grid item xs={6} sm={4} key={key}>
                  <Paper variant="outlined" sx={{ p: 1 }}>
                    <Typography variant="caption" color="text.secondary">{key}</Typography>
                    <Typography variant="body2" fontWeight="bold">{typeof value === 'number' ? value.toFixed(2) : value}</Typography>
                  </Paper>
                </Grid>
              ))}
            </Grid>
          )}
          {colDetail.is_high_cardinality ? (
            <Box sx={{ mt: 2, p: 2, border: '1px dashed grey', borderRadius: 1, textAlign: 'center' }}>
              <Typography variant="body1" sx={{ mb: 2 }}>
                {colDetail.warning}
              </Typography>
              <Button 
                variant="contained"
                startIcon={<DownloadIcon />}
                onClick={async () => {
                  try {
                    const res = await fetch(`/api/analysis/columns/${colName}/export?job_id=${jobId}`);
                    if (!res.ok) throw new Error(`Server error: ${res.status}`);
                    const blob = await res.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.style.display = 'none';
                    a.href = url;
                    const disposition = res.headers.get('content-disposition');
                    let filename = `details_${colName}.csv`;
                    if (disposition && disposition.indexOf('attachment') !== -1) {
                        const filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
                        const matches = filenameRegex.exec(disposition);
                        if (matches != null && matches[1]) { 
                            filename = matches[1].replace(/['"]/g, '');
                        }
                    }
                    a.setAttribute('download', filename);
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(a);
                  } catch (err) {
                    console.error("Download failed", err);
                    // You might want to show an error to the user here
                  }
                }}
              >
                Tải về CSV
              </Button>
            </Box>
          ) : (
            <>
              {histChart && <Box sx={{ height: 250, mb: 2 }}><MemoizedBar data={histChart} options={{ responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } }} /></Box>}
              {barChart && <Box sx={{ height: 250 }}><MemoizedBar data={barChart} options={{ responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } }} /></Box>}
              {colDetail && colDetail.value_counts && Object.keys(colDetail.value_counts).length > 0 && (
                <Box sx={{ maxWidth: 400, mt: 2 }}>
                  <TableContainer component={Paper} variant="outlined" sx={{ maxHeight: 300 }}>
                    <Table stickyHeader size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell sx={{ fontWeight: 'bold' }}>Thành phần</TableCell>
                          <TableCell align="right" sx={{ fontWeight: 'bold' }}>Số lượng</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {Object.entries(colDetail.value_counts)
                          .sort(([, a], [, b]) => b - a)
                          .slice(0, 50) // Giới hạn chỉ hiển thị 50 giá trị đầu
                          .map(([value, count]) => (
                            <TableRow key={value} hover>
                              <TableCell>{value}</TableCell>
                              <TableCell align="right">{count.toLocaleString()}</TableCell>
                            </TableRow>
                          ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </Box>
              )}
            </>
          )}
        </Box>
      ) : <CircularProgress />}
    </CardContent>
  </Card>
);

// --- Main DataAnalysis Component ---

export default function DataAnalysis() {
    const [file, setFile] = useState(null);
    const [jobId, setJobId] = useState(null);
    const [status, setStatus] = useState('');
    const [overview, setOverview] = useState(null);
    const [colName, setColName] = useState('');
    const [colDetail, setColDetail] = useState(null);
    const [error, setError] = useState('');
    const [dragging, setDragging] = useState(false);
    const dragCounter = useRef(0);
    const [filters, setFilters] = useState({ included_columns: [], excluded_by_pattern: {} });

    useEffect(() => {
        if (jobId && (status === 'submitted' || status === 'processing')) {
            const interval = setInterval(async () => {
                try {
                    const response = await api.get(`/analysis/status/${jobId}`);
                    const newStatus = response.data.status;
                    setStatus(newStatus);
                    if (newStatus === 'finished') {
                        clearInterval(interval);
                        const overviewRes = await api.get(`/analysis/summary?job_id=${jobId}`);
                        setOverview(overviewRes.data);
                        if (overviewRes.data && overviewRes.data.columns.length > 0) {
                            setColName(overviewRes.data.columns[0].name);
                        }
                        await fetchConfig(jobId);
                    } else if (newStatus === 'failed') {
                        clearInterval(interval);
                        setError(response.data.error || 'Phân tích thất bại.');
                    }
                } catch (err) {
                    clearInterval(interval);
                    setError('Lỗi khi lấy trạng thái công việc.');
                    console.error(err);
                }
            }, POLLING_INTERVAL);
            return () => clearInterval(interval);
        }
    }, [jobId, status]);

    useEffect(() => {
        if (colName && jobId) {
            const fetchDetails = async () => {
                try {
                    setColDetail(null);
                    const response = await api.get(`/analysis/columns/${colName}?job_id=${jobId}`);
                    setColDetail(response.data);
                } catch (err) {
                    console.error('Lỗi khi lấy chi tiết cột:', err);
                    setError(`Không thể tải chi tiết cho cột ${colName}.`);
                }
            };
            fetchDetails();
        }
    }, [colName, jobId]);

    const fetchConfig = async (id) => {
        try {
            const res = await api.get(`/analysis/config?job_id=${id}`);
            if (res.data && res.data.filters) {
                setFilters(res.data.filters);
            } else {
                // Fallback to a safe default if the structure is not as expected
                setFilters({ included_columns: [], excluded_by_pattern: {} });
            }
        } catch (error) {
            console.error("Failed to fetch filters", error);
            setFilters({ included_columns: [], excluded_by_pattern: {} }); // Also set safe default on error
        }
    };

    const handleFilterChange = async (columnName, isIncluded) => {
        const currentIncluded = filters.included_columns;
        const newIncluded = isIncluded
            ? [...currentIncluded, columnName]
            : currentIncluded.filter(c => c !== columnName);

        try {
            await api.post(`/analysis/config?job_id=${jobId}`, { included_columns: newIncluded });
            // Refetch the config to get the updated state including any server-side changes
            await fetchConfig(jobId);
            const overviewRes = await api.get(`/analysis/summary?job_id=${jobId}`);
            setOverview(overviewRes.data);
        } catch (error) {
            console.error("Failed to update filters", error);
            setError('Cập nhật bộ lọc thất bại.');
        }
    };

    const handleUpload = async () => {
        if (!file) return;
        const formData = new FormData();
        formData.append('file', file);
        setStatus('uploading');
        setError('');
        try {
            const response = await api.post('/analysis/upload', formData, { headers: { 'Content-Type': 'multipart/form-data' } });
            setJobId(response.data.job_id);
            setStatus('submitted');
        } catch (err) {
            setError(err.response?.data?.detail || 'Tải lên thất bại.');
            setStatus('failed');
            console.error(err);
        }
    };

    const handleFileChange = (e) => {
        setFile(e.target.files[0]);
        resetState();
    };

    const handleDrag = (e) => { e.preventDefault(); e.stopPropagation(); };
    const handleDragIn = (e) => {
        e.preventDefault();
        e.stopPropagation();
        dragCounter.current++;
        if (e.dataTransfer.items && e.dataTransfer.items.length > 0) {
            setDragging(true);
        }
    };
    const handleDragOut = (e) => {
        e.preventDefault();
        e.stopPropagation();
        dragCounter.current--;
        if (dragCounter.current === 0) {
            setDragging(false);
        }
    };
    const handleDrop = (e) => {
        e.preventDefault();
        e.stopPropagation();
        setDragging(false);
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            setFile(e.dataTransfer.files[0]);
            resetState();
            e.dataTransfer.clearData();
            dragCounter.current = 0;
        }
    };

    const resetState = () => {
        setJobId(null);
        setStatus('');
        setOverview(null);
        setColName('');
        setColDetail(null);
        setError('');
    };

    const chartData = useMemo(() => {
        if (!overview) return null;
        return {
            labels: overview.columns.map(c => c.name),
            datasets: [{
                label: '% Missing',
                data: overview.columns.map(c => c.missing_percentage),
                backgroundColor: 'rgba(255, 99, 132, 0.5)',
            }]
        };
    }, [overview]);

    const histChart = useMemo(() => {
        if (!colDetail?.histogram) return null;
        return {
            labels: colDetail.histogram.bins.map(b => b.toFixed(2)),
            datasets: [{
                label: 'Frequency',
                data: colDetail.histogram.counts,
                backgroundColor: 'rgba(75, 192, 192, 0.5)',
            }]
        };
    }, [colDetail]);

    const barChart = useMemo(() => {
        if (!colDetail?.value_counts || typeof colDetail.value_counts !== 'object') return null;

        let entries = Object.entries(colDetail.value_counts);
        if (entries.length === 0) return null;

        // Optimization: If there are too many unique values, sorting the whole array is slow and can crash the browser.
        // We'll take a large slice, sort that, and then take the top N.
        // This is a heuristic and might not get the true top 20 if the highest counts are outside the initial slice,
        // but it prevents the app from crashing.
        // A better long-term solution is to have the backend return only the top N value counts for high-cardinality columns.
        if (entries.length > 50000) {
            entries = entries.slice(0, 50000);
        }

        // Sort by count descending and take top 20 for display
        const sortedEntries = entries.sort(([, a], [, b]) => b - a).slice(0, 20);

        return {
            labels: sortedEntries.map(([value]) => String(value)), // Ensure labels are strings
            datasets: [{
                label: 'Count',
                data: sortedEntries.map(([, count]) => count),
                backgroundColor: 'rgba(153, 102, 255, 0.5)',
            }]
        };
    }, [colDetail]);

    return (
        <Container maxWidth="xl">
            <Typography variant="h4" component="h1" gutterBottom sx={{ mt: 2 }}>
                Phân tích Dữ liệu
            </Typography>
            <UploadSection 
                onUpload={handleUpload} 
                onFileChange={handleFileChange} 
                file={file} 
                status={status} 
                dragging={dragging}
                dragHandlers={{ onDragEnter: handleDragIn, onDragLeave: handleDragOut, onDragOver: handleDrag, onDrop: handleDrop }}
            />
            <JobStatus status={status} error={error} />
            {overview && (
                <Box>
                    <Box sx={{ mb: 3 }}>
                        <SummaryCard 
                            overview={overview} 
                            filters={filters}
                            onFilterChange={handleFilterChange}
                            chartData={chartData} 
                        />
                    </Box>
                    <Box>
                        <ColumnDetailCard 
                            overview={overview} 
                            colName={colName} 
                            setColName={setColName} 
                            colDetail={colDetail} 
                            histChart={histChart}
                            barChart={barChart}
                            jobId={jobId}
                        />
                    </Box>
                </Box>
            )}
        </Container>
    );
}
