import React, { useMemo } from 'react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  LineElement,
  CategoryScale,
  LinearScale,
  PointElement,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';
import annotationPlugin from 'chartjs-plugin-annotation';

ChartJS.register(LineElement, CategoryScale, LinearScale, PointElement, Tooltip, Legend, Filler, annotationPlugin);

function buildSeries(record) {
  const history = Array.isArray(record?.history) ? record.history : [];
  const forecast = Array.isArray(record?.forecast) ? record.forecast : [];
  const ci = record?.confidence_interval;

  if (history.length === 0 && forecast.length === 0) {
    return { labels: [], datasets: [], transitionDate: null };
  }

  const labelsSet = new Set([...history.map(p => p.date), ...forecast.map(p => p.date)]);
  const labels = Array.from(labelsSet).sort();

  const historyMap = new Map(history.map(p => [p.date, p.actual]));
  // API SKU trả về forecast là một object { date, forecast }, khác với PC là { date, yhat }
  const forecastMap = new Map(forecast.map(p => [p.date, { 
    yhat: p.forecast, 
    lower: ci?.lower?.[p.date], // Giả định CI là một map date -> value
    upper: ci?.upper?.[p.date],
  }]));

  const actualData = labels.map(label => historyMap.get(label) ?? null);
  const forecastData = labels.map(label => forecastMap.get(label)?.yhat ?? null);
  const ciUpperData = labels.map(label => forecastMap.get(label)?.upper ?? null);
  const ciLowerData = labels.map(label => forecastMap.get(label)?.lower ?? null);

  const lastHistoryPoint = history.length > 0 ? history[history.length - 1] : null;
  if (lastHistoryPoint) {
    const lastHistoryIndex = labels.indexOf(lastHistoryPoint.date);
    if (lastHistoryIndex !== -1) {
      forecastData[lastHistoryIndex] = lastHistoryPoint.actual;
      if (ciUpperData[lastHistoryIndex] === null) ciUpperData[lastHistoryIndex] = lastHistoryPoint.actual;
      if (ciLowerData[lastHistoryIndex] === null) ciLowerData[lastHistoryIndex] = lastHistoryPoint.actual;
    }
  }

  const actualColor = '#4CAF50';
  const forecastColor = '#FF9800';
  const ciColor = 'rgba(255, 152, 0, 0.2)';

  const datasets = [
    { label: 'Lịch sử', data: actualData, borderColor: actualColor, borderWidth: 2, pointRadius: 2.5, tension: 0.2 },
    { label: 'Dự báo', data: forecastData, borderColor: forecastColor, borderWidth: 2, pointRadius: 2.5, borderDash: [6, 4], tension: 0.2, spanGaps: true },
  ];

  // // Chỉ thêm dataset cho CI nếu có dữ liệu
  // if (ciUpperData.some(d => d !== null) && ciLowerData.some(d => d !== null)) {
  //   datasets.push(
  //     { label: 'Khoảng tin cậy', data: ciUpperData, fill: '+1', backgroundColor: ciColor, borderColor: 'transparent', pointRadius: 0, spanGaps: true },
  //     { label: 'CI Lower', data: ciLowerData, fill: false, borderColor: 'transparent', pointRadius: 0, spanGaps: false, hidden: true }
  //   );
  // }

  const rawTransitionDate = record?.train_end_date || lastHistoryPoint?.date || null;
  let transitionDate = null;
  if (rawTransitionDate) {
    transitionDate = labels.find(d => d >= rawTransitionDate) || rawTransitionDate;
  }

  return { labels, datasets, transitionDate };
}

export default function SkuForecastChart({ record }) {
  if (!record) return null;

  const { labels, datasets, transitionDate } = useMemo(() => buildSeries(record), [record]);

  const data = { labels, datasets };
  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
        labels: {
          filter: item => item.text && !item.text.includes('CI Lower'),
        },
      },
      tooltip: {
        mode: 'index',
        intersect: false,
        callbacks: {
          title: items => items[0] ? `Ngày: ${items[0].label}` : '',
          label: ctx => {
            if (ctx.parsed.y === null) return null;
            const label = ctx.dataset.label || '';
            if (label.includes('CI')) return null;
            return `${label}: ${ctx.parsed.y.toFixed(2)}`;
          },
        },
      },
      annotation: transitionDate
        ? {
            annotations: {
              transition: {
                type: 'line',
                xMin: transitionDate,
                xMax: transitionDate,
                borderColor: 'rgba(158,158,158,0.85)',
                borderWidth: 1.5,
                borderDash: [6, 6],
              },
            },
          }
        : {},
    },
    interaction: { mode: 'nearest', axis: 'x', intersect: false },
    scales: {
      y: { beginAtZero: true },
    },
  };

  return (
    <div style={{ height: 360 }}>
      <Line data={data} options={options} />
    </div>
  );
}
