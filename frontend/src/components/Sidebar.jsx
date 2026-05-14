import { NavLink } from 'react-router-dom'
import {
  MessageSquare, FileText, File, BarChart2
} from 'lucide-react'

const links = [
  { to: '/',          icon: MessageSquare, label: 'Chat' },
  { to: '/invoices',  icon: FileText,      label: 'Invoices' },
  { to: '/documents', icon: File,          label: 'Documents' },
  { to: '/metrics',   icon: BarChart2,     label: 'Metrics' }
]

export default function Sidebar() {
  return (
    <div style={{
      width: '220px', minHeight: '100vh',
      background: '#1a1a2e', color: '#fff',
      padding: '24px 0', display: 'flex',
      flexDirection: 'column', gap: '4px'
    }}>
      <div style={{
        padding: '0 24px 24px',
        fontSize: '20px', fontWeight: 700,
        color: '#6c8fff', borderBottom: '1px solid #2a2a4a'
      }}>
        NexusAI
      </div>

      {links.map(({ to, icon: Icon, label }) => (
        <NavLink
          key={to} to={to}
          end={to === '/'}
          style={({ isActive }) => ({
            display: 'flex', alignItems: 'center',
            gap: '12px', padding: '12px 24px',
            color: isActive ? '#6c8fff' : '#aaa',
            background: isActive ? '#2a2a4a' : 'transparent',
            textDecoration: 'none', fontSize: '15px',
            borderLeft: isActive
              ? '3px solid #6c8fff' : '3px solid transparent'
          })}
        >
          <Icon size={18} />
          {label}
        </NavLink>
      ))}
    </div>
  )
}