import { useState } from 'react'
import { agentApi } from '../api/client'
import { Send, Bot, User, Loader } from 'lucide-react'

const styles = {
  container: { display: 'flex', flexDirection: 'column', height: '80vh' },
  header: { marginBottom: '24px' },
  title: { fontSize: '24px', fontWeight: 700, color: '#1a1a2e' },
  subtitle: { color: '#666', marginTop: '4px' },
  messages: {
    flex: 1, overflowY: 'auto', display: 'flex',
    flexDirection: 'column', gap: '16px',
    padding: '16px', background: '#fff',
    borderRadius: '12px', border: '1px solid #e0e7ff',
    marginBottom: '16px'
  },
  inputRow: { display: 'flex', gap: '12px' },
  input: {
    flex: 1, padding: '12px 16px', borderRadius: '8px',
    border: '2px solid #e0e7ff', fontSize: '15px',
    outline: 'none'
  },
  sendBtn: {
    padding: '12px 20px', background: '#6c8fff',
    color: '#fff', border: 'none', borderRadius: '8px',
    cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '8px'
  },
  badge: {
    display: 'inline-block', padding: '2px 8px',
    borderRadius: '4px', fontSize: '12px',
    background: '#e0e7ff', color: '#6c8fff',
    marginRight: '6px'
  }
}

function Message({ role, content, meta }) {
  const isUser = role === 'user'
  return (
    <div style={{
      display: 'flex', gap: '12px',
      justifyContent: isUser ? 'flex-end' : 'flex-start'
    }}>
      {!isUser && (
        <div style={{
          width: '32px', height: '32px', borderRadius: '50%',
          background: '#6c8fff', display: 'flex',
          alignItems: 'center', justifyContent: 'center', flexShrink: 0
        }}>
          <Bot size={16} color="#fff" />
        </div>
      )}
      <div style={{ maxWidth: '70%' }}>
        <div style={{
          padding: '12px 16px',
          background: isUser ? '#6c8fff' : '#f5f7ff',
          color: isUser ? '#fff' : '#1a1a2e',
          borderRadius: isUser
            ? '12px 12px 0 12px' : '12px 12px 12px 0',
          fontSize: '14px', lineHeight: '1.6',
          whiteSpace: 'pre-wrap'
        }}>
          {content}
        </div>
        {meta && (
          <div style={{ marginTop: '6px', fontSize: '12px' }}>
            {meta.agents_used?.invoice && (
              <span style={styles.badge}>Invoice Agent</span>
            )}
            {meta.agents_used?.document && (
              <span style={styles.badge}>Document Agent</span>
            )}
            {meta.agents_used?.sentiment && (
              <span style={styles.badge}>Sentiment Agent</span>
            )}
            {meta.duration_seconds && (
              <span style={{ color: '#999' }}>
                {meta.duration_seconds}s
              </span>
            )}
          </div>
        )}
      </div>
      {isUser && (
        <div style={{
          width: '32px', height: '32px', borderRadius: '50%',
          background: '#e0e7ff', display: 'flex',
          alignItems: 'center', justifyContent: 'center', flexShrink: 0
        }}>
          <User size={16} color="#6c8fff" />
        </div>
      )}
    </div>
  )
}

export default function Chat() {
  const [messages, setMessages] = useState([{
    role: 'assistant',
    content: 'Hello! I am NexusAI. Ask me about your expenses, ' +
             'documents, or paste customer feedback to analyze sentiment.'
  }])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)

  const send = async () => {
    if (!input.trim() || loading) return

    const userMsg = { role: 'user', content: input }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setLoading(true)

    try {
      const response = await agentApi.chat(input)
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: response.final_answer,
        meta: {
          agents_used: response.agents_used,
          duration_seconds: response.duration_seconds
        }
      }])
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Something went wrong. Please try again.'
      }])
    } finally {
      setLoading(false)
    }
  }

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      send()
    }
  }

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <div style={styles.title}>Agent Chat</div>
        <div style={styles.subtitle}>
          Ask about expenses, documents, or customer feedback
        </div>
      </div>

      <div style={styles.messages}>
        {messages.map((msg, i) => (
          <Message key={i} {...msg} />
        ))}
        {loading && (
          <div style={{ display: 'flex', gap: '8px',
            alignItems: 'center', color: '#999' }}>
            <Loader size={16} className="spin" />
            <span>Thinking...</span>
          </div>
        )}
      </div>

      <div style={styles.inputRow}>
        <input
          style={styles.input}
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKey}
          placeholder="Type a message... (Enter to send)"
        />
        <button style={styles.sendBtn} onClick={send} disabled={loading}>
          <Send size={16} />
          Send
        </button>
      </div>
    </div>
  )
}