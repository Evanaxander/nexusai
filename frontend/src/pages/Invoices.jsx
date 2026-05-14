import { useState, useEffect } from 'react'
import { invoiceApi } from '../api/client'
import { Upload, TrendingUp, Trash2 } from 'lucide-react'

export default function Invoices() {
  const [invoices, setInvoices] = useState([])
  const [summary, setSummary] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [message, setMessage] = useState('')

  useEffect(() => {
    invoiceApi.list().then(setInvoices).catch(console.error)
    invoiceApi.weeklySummary().then(setSummary).catch(console.error)
  }, [])

  const handleUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return

    setUploading(true)
    setMessage('')

    const formData = new FormData()
    formData.append('file', file)
    formData.append('uploaded_by', 'dashboard')

    try {
      const result = await invoiceApi.upload(formData)
      setMessage(
        `Invoice saved: ${result.vendor} — ${result.amount} ${result.currency}`
      )
      const updated = await invoiceApi.list()
      setInvoices(updated)
      const updatedSummary = await invoiceApi.weeklySummary()
      setSummary(updatedSummary)
    } catch (err) {
      setMessage('Upload failed. Please try a clearer image.')
    } finally {
      setUploading(false)
    }
  }

  const handleDelete = async (invoiceId) => {
    if (!window.confirm('Are you sure you want to delete this invoice?')) {
      return
    }
    
    try {
      await invoiceApi.delete(invoiceId)
      const updated = await invoiceApi.list()
      setInvoices(updated)
      const updatedSummary = await invoiceApi.weeklySummary()
      setSummary(updatedSummary)
      setMessage('Invoice deleted successfully.')
    } catch (err) {
      setMessage('Failed to delete invoice.')
      console.error(err)
    }
  }

  return (
    <div>
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '24px', fontWeight: 700,
          color: '#1a1a2e' }}>Invoices</h1>
        <p style={{ color: '#666' }}>
          Upload receipts and track expenses
        </p>
      </div>

      {/* Summary cards */}
      {summary && (
        <div style={{ display: 'flex', gap: '16px', marginBottom: '24px' }}>
          {[
            { label: 'Total This Week',
              value: `${summary.total_expenses} BDT` },
            { label: 'Invoices', value: summary.invoice_count },
            { label: 'Top Vendor',
              value: summary.top_vendors[0] || 'None' }
          ].map(card => (
            <div key={card.label} style={{
              flex: 1, padding: '20px', background: '#fff',
              borderRadius: '12px', border: '1px solid #e0e7ff'
            }}>
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
      )}

      {/* Upload */}
      <div style={{
        padding: '24px', background: '#fff',
        borderRadius: '12px', border: '2px dashed #e0e7ff',
        marginBottom: '24px', textAlign: 'center'
      }}>
        <Upload size={32} color="#6c8fff"
          style={{ marginBottom: '12px' }} />
        <div style={{ color: '#666', marginBottom: '12px' }}>
          Upload invoice or receipt image
        </div>
        <label style={{
          padding: '10px 20px', background: '#6c8fff',
          color: '#fff', borderRadius: '8px',
          cursor: 'pointer', fontSize: '14px'
        }}>
          {uploading ? 'Processing...' : 'Choose Image'}
          <input
            type="file" accept="image/*"
            onChange={handleUpload} style={{ display: 'none' }}
          />
        </label>
        {message && (
          <div style={{
            marginTop: '12px', padding: '10px',
            background: '#f0fff4', borderRadius: '8px',
            color: '#2d6a4f', fontSize: '14px'
          }}>
            {message}
          </div>
        )}
      </div>

      {/* Table */}
      <div style={{
        background: '#fff', borderRadius: '12px',
        border: '1px solid #e0e7ff', overflow: 'hidden'
      }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ background: '#f5f7ff' }}>
              {['#', 'Vendor', 'Amount', 'Date', 'Verified', 'Actions'].map(h => (
                <th key={h} style={{
                  padding: '12px 16px', textAlign: 'left',
                  fontSize: '13px', color: '#666',
                  fontWeight: 600
                }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {invoices.map((inv, i) => (
              <tr key={inv.id} style={{
                borderTop: '1px solid #f0f0f0'
              }}>
                <td style={{ padding: '12px 16px',
                  color: '#999', fontSize: '13px' }}>
                  #{inv.id}
                </td>
                <td style={{ padding: '12px 16px',
                  fontWeight: 600 }}>{inv.vendor}</td>
                <td style={{ padding: '12px 16px',
                  color: '#2d6a4f' }}>
                  {inv.amount} {inv.currency}
                </td>
                <td style={{ padding: '12px 16px',
                  color: '#666', fontSize: '13px' }}>
                  {inv.invoice_date || '—'}
                </td>
                <td style={{ padding: '12px 16px' }}>
                  {inv.is_verified ? (
                    <span style={{
                      padding: '2px 8px', borderRadius: '4px',
                      fontSize: '12px', background: '#f0fff4', color: '#2d6a4f'
                    }}>
                      Verified
                    </span>
                  ) : (
                    <button
                      onClick={async () => {
                        await fetch(`/api/v1/invoices/${inv.id}/verify`, {
                          method: 'PATCH',
                          headers: { 'Content-Type': 'application/json' },
                          body: JSON.stringify({ is_verified: true })
                        })
                        const updated = await invoiceApi.list()
                        setInvoices(updated)
                      }}
                      style={{
                        padding: '2px 10px', borderRadius: '4px',
                        fontSize: '12px', background: '#fff7ed',
                        color: '#c05621', border: '1px solid #fed7aa',
                        cursor: 'pointer'
                      }}
                    >
                      Verify
                    </button>
                  )}
                </td>
                <td style={{ padding: '12px 16px' }}>
                  <button
                    onClick={() => handleDelete(inv.id)}
                    style={{
                      padding: '4px 8px', borderRadius: '4px',
                      fontSize: '12px', background: '#fef2f2',
                      color: '#dc2626', border: '1px solid #fecaca',
                      cursor: 'pointer', display: 'flex', alignItems: 'center',
                      gap: '4px'
                    }}
                  >
                    <Trash2 size={14} />
                    Delete
                  </button>
                </td>
              </tr>
            ))}
            {invoices.length === 0 && (
              <tr>
                <td colSpan={6} style={{
                  padding: '32px', textAlign: 'center', color: '#999'
                }}>
                  No invoices yet. Upload one above.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}