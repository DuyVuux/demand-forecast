import { Line } from 'react-chartjs-2'
import {
  Chart as ChartJS,
  LineElement,
  CategoryScale,
  LinearScale,
  PointElement,
  Tooltip,
  Legend,
} from 'chart.js'

ChartJS.register(LineElement, CategoryScale, LinearScale, PointElement, Tooltip, Legend)

function groupKey(row) {
  return 'customer_id' in row ? `${row.product_id} | ${row.customer_id}` : `${row.product_id}`
}

function buildChartData(items) {
  if (!items?.length) return { labels: [], datasets: [] }
  const labels = Array.from(new Set(items.map((r) => r.date))).sort()

  const groups = {}
  for (const r of items) {
    const key = groupKey(r)
    if (!groups[key]) groups[key] = {}
    groups[key][r.date] = Number(r.forecast)
  }

  const palette = [
    '#3366CC', '#DC3912', '#FF9900', '#109618', '#990099',
    '#0099C6', '#DD4477', '#66AA00', '#B82E2E', '#316395',
    '#994499', '#22AA99', '#AAAA11', '#6633CC', '#E67300',
  ]
  let i = 0

  const datasets = Object.entries(groups).map(([name, values]) => {
    const data = labels.map((d) => (d in values ? values[d] : null))
    const color = palette[i++ % palette.length]
    return {
      label: name,
      data,
      borderColor: color,
      backgroundColor: color + '55',
      spanGaps: true,
      tension: 0.2,
      pointRadius: 2,
    }
  })

  return { labels, datasets }
}

export default function ForecastChart({ data }) {
  const items = data?.forecast || []
  if (!items.length) return null

  const chartData = buildChartData(items)
  const options = {
    responsive: true,
    plugins: {
      legend: { position: 'top' },
      tooltip: { mode: 'index', intersect: false },
    },
    interaction: { mode: 'nearest', axis: 'x', intersect: false },
    scales: {
      y: { beginAtZero: true },
    },
  }

  return (
    <div className="card">
      <h3>Kết quả dự báo (Biểu đồ)</h3>
      <Line data={chartData} options={options} />
    </div>
  )
}
