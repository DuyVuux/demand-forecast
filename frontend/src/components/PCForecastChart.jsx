import React, { useEffect, useRef, useMemo } from 'react';
import { Line } from 'react-chartjs-2'
import {
  Chart as ChartJS,
  LineElement,
  CategoryScale,
  LinearScale,
  PointElement,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js'
import annotationPlugin from 'chartjs-plugin-annotation'

ChartJS.register(LineElement, CategoryScale, LinearScale, PointElement, Tooltip, Legend, Filler, annotationPlugin)

function buildSeries(record) {
  const history = Array.isArray(record?.history) ? record.history : [];
  const forecast = Array.isArray(record?.forecast) ? record.forecast : [];

  if (history.length === 0 && forecast.length === 0) {
    return { labels: [], datasets: [], transitionDate: null };
  }

  const labelsSet = new Set([...history.map(p => p.date), ...forecast.map(p => p.date)]);
  const labels = Array.from(labelsSet).sort();

  const historyMap = new Map(history.map(p => [p.date, p.actual]));
  const forecastMap = new Map(forecast.map(p => [p.date, { yhat: p.yhat, lower: p.yhat_lower_80, upper: p.yhat_upper_80 }]));

  const actualData = labels.map(label => historyMap.get(label) ?? null);
  const forecastData = labels.map(label => forecastMap.get(label)?.yhat ?? null);
  const ciUpperData = labels.map(label => forecastMap.get(label)?.upper ?? null);
  const ciLowerData = labels.map(label => forecastMap.get(label)?.lower ?? null);

  const lastHistoryPoint = history.length > 0 ? history[history.length - 1] : null;
  if (lastHistoryPoint) {
    const lastHistoryIndex = labels.indexOf(lastHistoryPoint.date);
    if (lastHistoryIndex !== -1) {
      // This is the key fix: create the anchor point for the forecast line
      forecastData[lastHistoryIndex] = lastHistoryPoint.actual;
    }
  }

  const actualColor = '#4CAF50';
  const forecastColor = '#FF9800';
  const ciColor = 'rgba(255, 152, 0, 0.2)';

  const datasets = [
    { label: 'Lịch sử', data: actualData, borderColor: actualColor, borderWidth: 2.2, pointRadius: 2.5, tension: 0.2 },
    { label: 'Dự báo', data: forecastData, borderColor: forecastColor, borderWidth: 2.2, pointRadius: 2.5, borderDash: [6, 4], tension: 0.2, spanGaps: true },
  ];

  const rawTransitionDate = record?.train_end_date || record?.transition_date || lastHistoryPoint?.date || null;
  let transitionDate = null;
  if (rawTransitionDate) {
    transitionDate = labels.find(d => d >= rawTransitionDate) || rawTransitionDate;
  }

  return { labels, datasets, transitionDate };
}

export default function PCForecastChart({ record }) {
  if (!record) return null

  // Key fix: Memoize the chart data to prevent re-computation on every render.
  // This was the missing piece causing the forecast line to disappear.
  const { labels, datasets, transitionDate } = useMemo(() => buildSeries(record), [record]);

  const data = { labels, datasets };
  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
        labels: {},

      },
      tooltip: {
        mode: 'index',
        intersect: false,
        callbacks: {
          title: items => items[0] ? `Ngày: ${items[0].label}` : '',
          label: ctx => {
            if (ctx.parsed.y === null) return null;
            const label = ctx.dataset.label || '';
            // Do not show tooltip for the CI datasets
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
  }

  return (
    <div style={{ height: 360 }}>
      <Line data={data} options={options} />
    </div>
  )
}
