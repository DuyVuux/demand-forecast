import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { login } from '../api.js'

export default function Login() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const onSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const res = await login(username, password)
      if (res?.access_token) {
        navigate('/data-analysis')
      } else {
        setError('Đăng nhập thất bại')
      }
    } catch (err) {
      console.error(err)
      setError('Sai username hoặc password')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container">
      <h2>Đăng nhập</h2>
      <form onSubmit={onSubmit} className="card">
        <div className="form-row">
          <label>Tên đăng nhập</label>
          <input value={username} onChange={(e) => setUsername(e.target.value)} placeholder="username" />
        </div>
        <div className="form-row">
          <label>Mật khẩu</label>
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="password" />
        </div>
        {error && <div className="error">{error}</div>}
        <button type="submit" disabled={loading}>{loading ? 'Đang đăng nhập...' : 'Đăng nhập'}</button>
      </form>
    </div>
  )
}
