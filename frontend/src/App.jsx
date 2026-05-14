import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Chat from './pages/Chat'
import Invoices from './pages/Invoices'
import Documents from './pages/Documents'
import Metrics from './pages/Metrics'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Chat />} />
          <Route path="invoices" element={<Invoices />} />
          <Route path="documents" element={<Documents />} />
          <Route path="metrics" element={<Metrics />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}