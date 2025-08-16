import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import api from '../api';
import { Bar, Line } from 'react-chartjs-2';
import { Chart as ChartJS, LineElement, BarElement, CategoryScale, LinearScale, PointElement, Tooltip, Legend, TimeScale } from 'chart.js';
import styles from './DataAnalysis.module.css';

ChartJS.register(LineElement, BarElement, CategoryScale, LinearScale, PointElement, Tooltip, Legend, TimeScale);

const POLLING_INTERVAL = 5000;

const MemoizedBar = React.memo(Bar);

// --- Child Components for DataAnalysis Page ---

const UploadSection = ({ onUpload, onFileChange, file, status, dragging, dragHandlers }) => (
  <div className={styles.uploadContainer} {...dragHandlers}>
    <input type="file" id="file-upload" className={styles.fileInput} onChange={onFileChange} accept=".csv,.xlsx" />
    <label htmlFor="file-upload" className={`${styles.dropzone} ${dragging ? styles.dragging : ''}`}>
      <div className={styles.uploadIcon}>📤</div>
      <p className={styles.uploadText}>
        Kéo và thả tệp vào đây, hoặc <span>chọn một tệp</span>
      </p>
    </label>
    {file && <p className={styles.filePreview}>Tệp đã chọn: {file.name}</p>}
    <button onClick={onUpload} disabled={!file || status === 'uploading' || status === 'processing'} className={styles.uploadButton}>
      {status === 'uploading' ? 'Đang tải lên...' : 'Tải lên & Phân tích'}
    </button>
  </div>
);

const JobStatus = ({ status, error }) => {
  if (error) {
    return <div className={styles.errorContainer}>Lỗi: {error}</div>;
  }
  if (status && status !== 'finished' && status !== 'failed') {
    return (
      <div className={styles.statusContainer}>
        Trạng thái: <strong>{status}</strong>
        {status === 'processing' && <span className={styles.spinner}></span>}
      </div>
    );
  }
  return null;
};

const SummaryCard = ({ overview, filters, onFilterChange, chartData }) => (
  <div className={styles.card}>
    <h2 className={styles.cardHeader}>Tổng quan Dữ liệu</h2>
    <p>{overview.summary}</p>
    <div className={styles.tableContainer}>
      <table className={styles.table}>
        <thead>
          <tr>
            <th>Tên cột</th>
            <th>Kiểu dữ liệu</th>
            <th>% Thiếu</th>
            <th>Bao gồm</th>
          </tr>
        </thead>
        <tbody>
          {overview.columns.map(col => (
            <tr key={col.name}>
              <td>{col.name}</td>
              <td>{col.type}</td>
              <td>{col.missing_percentage.toFixed(2)}%</td>
              <td title={filters?.excluded_by_pattern[col.name] || ''}>
                <input 
                  type="checkbox" 
                  checked={filters ? filters.included_columns.includes(col.name) : false}
                  onChange={(e) => onFilterChange(col.name, e.target.checked)}
                  disabled={!!filters?.excluded_by_pattern[col.name]}
                />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
    {chartData && <div className={styles.chartContainer}><MemoizedBar data={chartData} options={{ responsive: true, maintainAspectRatio: false }} /></div>}
  </div>
);

const ColumnDetailCard = ({ overview, colName, setColName, colDetail, histChart, barChart }) => (
  <div className={styles.card}>
    <h2 className={styles.cardHeader}>Chi tiết Cột</h2>
    <select className={styles.select} value={colName} onChange={e => setColName(e.target.value)}>
      {overview.columns.map(c => <option key={c.name} value={c.name}>{c.name}</option>)}
    </select>
    {colDetail ? (
      <div>
        <h4>{colDetail.name} ({colDetail.type})</h4>
        {colDetail.warning && <p className={styles.warning}>{colDetail.warning}</p>}
        {colDetail.stats && (
          <div className={styles.statsGrid}>
            {Object.entries(colDetail.stats).map(([key, value]) => (
              <div key={key}><strong>{key}:</strong> {typeof value === 'number' ? value.toFixed(2) : value}</div>
            ))}
          </div>
        )}
        {histChart && <div className={styles.chartContainer}><MemoizedBar data={histChart} options={{ responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } }} /></div>}
        {barChart && <div className={styles.chartContainer}><MemoizedBar data={barChart} options={{ responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } }} /></div>}
      </div>
    ) : <p>Đang tải...</p>}
  </div>
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
                    const response = await api.get(`/analysis/status?job_id=${jobId}`);
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
                    const response = await api.get(`/analysis/column_detail?job_id=${jobId}&column_name=${colName}`);
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
            setFilters(res.data);
        } catch (error) {
            console.error("Failed to fetch filters", error);
        }
    };

    const handleFilterChange = async (columnName, isIncluded) => {
        const currentIncluded = filters.included_columns;
        const newIncluded = isIncluded
            ? [...currentIncluded, columnName]
            : currentIncluded.filter(c => c !== columnName);

        try {
            await api.post(`/analysis/config?job_id=${jobId}`, { included_columns: newIncluded });
            setFilters(prev => ({ ...prev, included_columns: newIncluded }));
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
            setStatus('failed');
            setError(err.response?.data?.detail || 'Tải lên thất bại.');
            console.error(err);
        }
    };

    const handleFileChange = (e) => {
        if (e.target.files && e.target.files[0]) {
            setFile(e.target.files[0]);
        }
    };

    const handleDrag = (e) => { e.preventDefault(); e.stopPropagation(); };
    const handleDragIn = (e) => {
        e.preventDefault();
        e.stopPropagation();
        dragCounter.current++;
        if (e.dataTransfer.items && e.dataTransfer.items.length > 0) setDragging(true);
    };
    const handleDragOut = (e) => {
        e.preventDefault();
        e.stopPropagation();
        dragCounter.current--;
        if (dragCounter.current === 0) setDragging(false);
    };
    const handleDrop = (e) => {
        e.preventDefault();
        e.stopPropagation();
        setDragging(false);
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            setFile(e.dataTransfer.files[0]);
            e.dataTransfer.clearData();
            dragCounter.current = 0;
        }
    };

    const dragHandlers = { onDragEnter: handleDragIn, onDragLeave: handleDragOut, onDragOver: handleDrag, onDrop: handleDrop };

    const summaryChart = useMemo(() => {
        if (!overview) return null;
        return { labels: overview.columns.map(c => c.name), datasets: [{ label: '% giá trị thiếu', data: overview.columns.map(c => c.missing_percentage), backgroundColor: 'rgba(75, 192, 192, 0.6)' }] };
    }, [overview]);

    const histChart = useMemo(() => {
        if (!colDetail || !colDetail.histogram) return null;
        const { counts, bin_edges } = colDetail.histogram;
        if (!Array.isArray(bin_edges)) return null;
        const labels = bin_edges.slice(0, -1).map((edge, i) => `${edge.toFixed(1)}-${bin_edges[i+1].toFixed(1)}`);
        return { labels, datasets: [{ data: counts || [], backgroundColor: 'rgba(54, 162, 235, 0.6)' }] };
    }, [colDetail]);

    const barChart = useMemo(() => {
        if (!colDetail || !colDetail.value_counts) return null;
        const labels = Object.keys(colDetail.value_counts);
        const data = Object.values(colDetail.value_counts);
        return { labels, datasets: [{ data, backgroundColor: 'rgba(255, 159, 64, 0.6)' }] };
    }, [colDetail]);

    return (
        <div>
            <div className={styles.pageHeader}><h1>Phân tích Dữ liệu</h1></div>
            
            {!jobId && !overview && (
                <UploadSection 
                    onUpload={handleUpload} 
                    onFileChange={handleFileChange} 
                    file={file} 
                    status={status} 
                    dragging={dragging} 
                    dragHandlers={dragHandlers} 
                />
            )}

            <JobStatus status={status} error={error} />

            {overview && (
                <div className={styles.resultsGrid}>
                    <SummaryCard 
                        overview={overview} 
                        filters={filters} 
                        onFilterChange={handleFilterChange} 
                        chartData={summaryChart} 
                    />
                    <ColumnDetailCard 
                        overview={overview} 
                        colName={colName} 
                        setColName={setColName} 
                        colDetail={colDetail} 
                        histChart={histChart} 
                        barChart={barChart} 
                    />
                </div>
            )}
        </div>
    );
}
