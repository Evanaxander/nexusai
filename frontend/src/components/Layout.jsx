import Sidebar from './Sidebar'
import { Outlet } from 'react-router-dom'

export default function Layout() {
  return (
    <div style={{ display: 'flex', minHeight: '100vh',
      background: '#f5f7ff', fontFamily: 'Inter, sans-serif' }}>
      <Sidebar />
      <main style={{ flex: 1, padding: '32px',
        maxWidth: '900px' }}>
        <Outlet />
      </main>
    </div>
  )
}