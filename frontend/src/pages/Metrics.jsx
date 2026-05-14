import { useState, useEffect } from 'react'
import { metricsApi } from '../api/client'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip,
  ResponsiveContainer, Cell
} from 'recharts'
import { Activity, Clock, CheckCircle, AlertTriangle } from 'lucide-react'

export default function Metrics() {
  const [stats, setStats] = useState(null)
  const [health, setHealth] = useState(null)

  useEffect(() => {
    metricsApi.get().then(setStats).catch(console.error)
    metricsApi.healthScore().then(setHealth).catch(console.error)

    // Refresh every 30 seconds
    const interval = setInterval(() => {
      metricsApi.get().then(setStats).catch(console.error)
      metricsApi.healthScore().then(setHealth).catch(console.error)
    }, 30000)

    return () => clearInterval(interval)
  }, [])

  if (!stats || !health) {
    return <div style={{ color: '#999' }}>Loading metrics...</div>
  }

  const agentData = [
    { name: 'Invoice', value: stats.agent_usage.invoice || 0 },
    { name: 'Document', value: stats.agent_usage.document || 0 },
    { name: 'Sentiment', value: stats.agent_usage.sentiment || 0 }
  ]

  const healthColor = health.status === 'healthy'
    ? '#2d6a4f' : health.status === 'degraded'
    ? '#c05621' : '#c0392b'

  return (
    <div>
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '24px', fontWeight: 700,
          color: '#1a1a2e' }}>Metrics</h1>
        <p style={{ color: '#666' }}>Agent performance dashboard</p>
      </div>

      {/* Health score */}
      <div style={{
        padding: '24px', background: '#fff',
        borderRadius: '12px', border: '1px solid #e0e7ff',
        marginBottom: '24px', display: 'flex',
        alignItems: 'center', gap: '24px'
      }}>
        <div style={{
          width: '80px', height: '80px', borderRadius: '50%',
          background: healthColor, display: 'flex',
          flexDirection: 'column', alignItems: 'center',
          justifyContent: 'center', color: '#fff'
        }}>
          <div style={{ fontSize: '24px', fontWeight: 700 }}>
            {health.score}
          </div>
          <div style={{ fontSize: '11px' }}>/ 100</div>
        </div>
        <div>
          <div style={{ fontSize: '20px', fontWeight: 700,
            color: healthColor, textTransform: 'capitalize' }}>
            {health.status}
          </div>
          <div style={{ color: '#666', fontSize: '14px',
            marginTop: '4px' }}>
            {health.total_runs} total runs ·{' '}
            {(health.success_rate * 100).toFixed(0)}% success ·{' '}
            {health.avg_duration_seconds}s avg
          </div>
        </div>
      </div>

      {/* Stat cards */}
      <div style={{ display: 'flex', gap: '16px', marginBottom: '24px' }}>
        {[
          { icon: Activity, label: 'Total Runs',
            value: stats.total_runs, color: '#6c8fff' },
          { icon: CheckCircle, label: 'Success Rate',
            value: `${(stats.success_rate * 100).toFixed(0)}%`,
            color: '#2d6a4f' },
          { icon: Clock, label: 'Avg Duration',
            value: `${stats.avg_duration_seconds}s`,
            color: '#c05621' },
        ].map(card => (
          <div key={card.label} style={{
            flex: 1, padding: '20px', background: '#fff',
            borderRadius: '12px', border: '1px solid #e0e7ff'
          }}>
            <card.icon size={20} color={card.color}
              style={{ marginBottom: '8px' }} />
            <div style={{ color: '#666', fontSize: '13px' }}>
              {card.label}
            </div>
            <div style={{ fontSize: '22px', fontWeight: 700,
              color: '#1a1a2e', marginTop: '4px' }}>
              {card.value}
            </div>
          </div>
        ))}
      </div>

      {/* Agent usage chart */}
      <div style={{
        padding: '24px', background: '#fff',
        borderRadius: '12px', border: '1px solid #e0e7ff',
        marginBottom: '24px'
      }}>
        <div style={{ fontWeight: 600, marginBottom: '16px' }}>
          Agent Usage
        </div>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={agentData}>
            <XAxis dataKey="name" />
            <YAxis allowDecimals={false} />
            <Tooltip />
            <Bar dataKey="value" radius={[4, 4, 0, 0]}>
              {agentData.map((_, i) => (
                <Cell key={i}
                  fill={['#6c8fff', '#2d6a4f', '#c05621'][i]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Recent runs */}
      <div style={{
        background: '#fff', borderRadius: '12px',
        border: '1px solid #e0e7ff', overflow: 'hidden'
      }}>
        <div style={{
          padding: '16px', fontWeight: 600,
          borderBottom: '1px solid #f0f0f0'
        }}>
          Recent Runs
        </div>
        {stats.recent_runs.length === 0 && (
          <div style={{
            padding: '32px', textAlign: 'center', color: '#999'
          }}>
            No runs yet. Use the Chat page to start.
          </div>
        )}
        {[...stats.recent_runs].reverse().map((run, i) => (
          <div key={i} style={{
            padding: '12px 16px',
            borderBottom: '1px solid #f0f0f0',
            display: 'flex', justifyContent: 'space-between',
            alignItems: 'center', fontSize: '13px'
          }}>
            <div style={{ flex: 1, color: '#444',
              overflow: 'hidden', textOverflow: 'ellipsis',
              whiteSpace: 'nowrap', marginRight: '12px' }}>
              {run.user_message_preview}
            </div>
            <div style={{ display: 'flex', gap: '8px',
              alignItems: 'center', flexShrink: 0 }}>
              <span style={{ color: '#999' }}>
                {run.duration_seconds}s
              </span>
              <span style={{
                padding: '2px 8px', borderRadius: '4px',
                background: run.success ? '#f0fff4' : '#fff5f5',
                color: run.success ? '#2d6a4f' : '#c0392b',
                fontSize: '12px'
              }}>
                {run.success ? 'OK' : 'Failed'}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}