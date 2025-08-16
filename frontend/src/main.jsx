import React from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import MainLayout from './layouts/MainLayout.jsx';
import Home from './pages/Home.jsx';
import DataAnalysis from './pages/DataAnalysis.jsx';
import Login from './pages/Login.jsx';
import PCForecastView from './pages/PCForecastView.jsx';
import SkuForecastPage from './pages/SkuForecastPage.jsx';
import './styles.css'
// One-time cleanup: remove legacy demo token from localStorage
try {
  if (!localStorage.getItem('token_migrated_v1')) {
    localStorage.removeItem('access_token')
    localStorage.setItem('token_migrated_v1', '1')
  }
} catch (e) {
  // ignore storage errors
}

createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route element={<MainLayout />}>
          <Route path="/" element={<Home />} />
          <Route path="/data-analysis" element={<DataAnalysis />} />
          <Route path="/pc-forecast" element={<PCForecastView />} />
          <Route path="/sku-forecast" element={<SkuForecastPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
)
