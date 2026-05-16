import { useState, useEffect } from 'react'
import { documentApi } from '../api/client'
import { Upload, Search, FileText, Trash2 } from 'lucide-react'

export default function Documents() {
  const [documents, setDocuments] = useState([])
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [querying, setQuerying] = useState(false)
  const [message, setMessage] = useState('')
  const [deleteConfirm, setDeleteConfirm] = useState(null)

  useEffect(() => {
    documentApi.list().then(setDocuments).catch(console.error)
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
      const result = await documentApi.upload(formData)
      setMessage(
        `Indexed: ${result.original_name} — ` +
        `${result.total_chunks} chunks, ${result.total_pages} pages`
      )
      const updated = await documentApi.list()
      setDocuments(updated)
    } catch (err) {
      setMessage('Upload failed.')
    } finally {
      setUploading(false)
    }
  }

  const handleQuery = async () => {
    if (!question.trim() || querying) return
    setQuerying(true)
    setAnswer(null)

    try {
      const result = await documentApi.query(question, null)
      setAnswer(result)
    } catch (err) {
      setAnswer({ answer: 'Query failed. Please try again.' })
    } finally {
      setQuerying(false)
    }
  }

  const handleDelete = async (docId, docName) => {
    if (!window.confirm(`Delete "${docName}"? This will also remove all indexed vectors.`)) {
      return
    }

    try {
      await documentApi.delete(docId)
      setMessage(`Deleted: ${docName}`)
      const updated = await documentApi.list()
      setDocuments(updated)
    } catch (err) {
      setMessage('Delete failed. Please try again.')
    } finally {
      setDeleteConfirm(null)
    }
  }

  return (
    <div>
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '24px', fontWeight: 700,
          color: '#1a1a2e' }}>Documents</h1>
        <p style={{ color: '#666' }}>
          Upload PDFs and ask questions about them
        </p>
      </div>

      {/* Upload */}
      <div style={{
        padding: '24px', background: '#fff',
        borderRadius: '12px', border: '2px dashed #e0e7ff',
        marginBottom: '24px', textAlign: 'center'
      }}>
        <FileText size={32} color="#6c8fff"
          style={{ marginBottom: '12px' }} />
        <div style={{ color: '#666', marginBottom: '12px' }}>
          Upload a PDF document to index it
        </div>
        <label style={{
          padding: '10px 20px', background: '#6c8fff',
          color: '#fff', borderRadius: '8px',
          cursor: 'pointer', fontSize: '14px'
        }}>
          {uploading ? 'Indexing...' : 'Choose PDF'}
          <input
            type="file" accept=".pdf"
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

      {/* Query */}
      <div style={{
        padding: '24px', background: '#fff',
        borderRadius: '12px', border: '1px solid #e0e7ff',
        marginBottom: '24px'
      }}>
        <div style={{ fontWeight: 600, marginBottom: '12px' }}>
          Ask a question
        </div>
        <div style={{ display: 'flex', gap: '12px' }}>
          <input
            style={{
              flex: 1, padding: '10px 14px', borderRadius: '8px',
              border: '2px solid #e0e7ff', fontSize: '14px'
            }}
            value={question}
            onChange={e => setQuestion(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleQuery()}
            placeholder="What does the contract say about payment terms?"
          />
          <button
            onClick={handleQuery}
            disabled={querying}
            style={{
              padding: '10px 20px', background: '#6c8fff',
              color: '#fff', border: 'none', borderRadius: '8px',
              cursor: 'pointer', display: 'flex',
              alignItems: 'center', gap: '8px'
            }}
          >
            <Search size={16} />
            {querying ? 'Searching...' : 'Ask'}
          </button>
        </div>

        {answer && (
          <div style={{ marginTop: '16px' }}>
            <div style={{
              padding: '16px', background: '#f5f7ff',
              borderRadius: '8px', fontSize: '14px',
              lineHeight: '1.7', whiteSpace: 'pre-wrap',
              color: '#1a1a2e', marginBottom: '12px'
            }}>
              {answer.answer}
            </div>
            {answer.sources && answer.sources.length > 0 && (
              <div>
                <div style={{ fontSize: '12px', color: '#999',
                  marginBottom: '6px' }}>
                  Sources:
                </div>
                {answer.sources.map((s, i) => (
                  <div key={i} style={{
                    fontSize: '12px', padding: '6px 10px',
                    background: '#e0e7ff', borderRadius: '6px',
                    marginBottom: '4px', color: '#444'
                  }}>
                    {s.document_name} — Page {s.page_number}
                    (score: {s.score})
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Document list */}
      <div style={{
        background: '#fff', borderRadius: '12px',
        border: '1px solid #e0e7ff', overflow: 'hidden'
      }}>
        <div style={{
          padding: '16px', fontWeight: 600,
          borderBottom: '1px solid #f0f0f0'
        }}>
          Indexed Documents ({documents.length})
        </div>
        {documents.map(doc => (
          <div key={doc.id} style={{
            padding: '16px', borderBottom: '1px solid #f0f0f0',
            display: 'flex', justifyContent: 'space-between',
            alignItems: 'center'
          }}>
            <div>
              <div style={{ fontWeight: 600, fontSize: '14px' }}>
                {doc.original_name}
              </div>
              <div style={{ color: '#999', fontSize: '12px',
                marginTop: '2px' }}>
                {doc.total_pages} pages · {doc.total_chunks} chunks
              </div>
            </div>
            <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
              <span style={{
                padding: '4px 10px', borderRadius: '4px',
                fontSize: '12px',
                background: doc.is_indexed ? '#f0fff4' : '#fff7ed',
                color: doc.is_indexed ? '#2d6a4f' : '#c05621'
              }}>
                {doc.is_indexed ? 'Indexed' : 'Processing'}
              </span>
              <button
                onClick={() => handleDelete(doc.id, doc.original_name)}
                style={{
                  padding: '6px 10px',
                  background: '#fee2e2',
                  color: '#dc2626',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  fontSize: '12px',
                  fontWeight: 500
                }}
              >
                <Trash2 size={14} />
                Delete
              </button>
            </div>
          </div>
        ))}
        {documents.length === 0 && (
          <div style={{
            padding: '32px', textAlign: 'center', color: '#999'
          }}>
            No documents yet. Upload a PDF above.
          </div>
        )}
      </div>
    </div>
  )
}