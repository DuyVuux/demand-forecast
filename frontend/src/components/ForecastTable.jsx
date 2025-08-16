export default function ForecastTable({ data }) {
  const items = data?.forecast || []
  if (!items.length) return null

  const hasCustomer = items.some((r) => 'customer_id' in r)

  return (
    <div className="card">
      <h3>Kết quả dự báo (Bảng)</h3>
      <div className="meta">Model: <b>{data?.meta?.model}</b> | Horizon: <b>{data?.meta?.horizon}</b> ngày</div>
      <div className="table-wrapper">
        <table>
          <thead>
            <tr>
              <th>product_id</th>
              {hasCustomer && <th>customer_id</th>}
              <th>date</th>
              <th>forecast</th>
            </tr>
          </thead>
          <tbody>
            {items.map((r, idx) => (
              <tr key={idx}>
                <td>{r.product_id}</td>
                {hasCustomer && <td>{r.customer_id}</td>}
                <td>{r.date}</td>
                <td>{Number(r.forecast).toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
