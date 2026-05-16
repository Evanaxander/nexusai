import axios from 'axios'

const client = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' }
})

export const agentApi = {
  chat: (message) =>
    client.post('/agent/chat', { message }).then(r => r.data)
}

export const invoiceApi = {
  list: () =>
    client.get('/invoices/').then(r => r.data),
  weeklySummary: () =>
    client.get('/invoices/weekly-summary').then(r => r.data),
  upload: (formData) =>
    client.post('/invoices/process', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    }).then(r => r.data),
  delete: (invoiceId) =>
    client.delete(`/invoices/${invoiceId}`).then(r => r.data)
}

export const documentApi = {
  list: () =>
    client.get('/documents/').then(r => r.data),
  upload: (formData) =>
    client.post('/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    }).then(r => r.data),
  query: (question, documentIds) =>
    client.post('/documents/query', {
      question,
      document_ids: documentIds,
      top_k: 5,
      stream: false
    }).then(r => r.data),
  delete: (documentId) =>
    client.delete(`/documents/${documentId}`).then(r => r.data)
}

export const metricsApi = {
  get: () => client.get('/metrics/').then(r => r.data),
  healthScore: () => client.get('/metrics/health-score').then(r => r.data)
}