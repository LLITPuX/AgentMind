'use client'

import { useEffect, useState } from 'react'
import styles from './page.module.css'

type ConnectionStatus = 'disconnected' | 'connecting' | 'connected' | 'error'

interface WebSocketMessage {
  type: string
  message?: string
  status?: string
  timestamp?: string
  [key: string]: any
}

export default function Home() {
  const [wsStatus, setWsStatus] = useState<ConnectionStatus>('disconnected')
  const [messages, setMessages] = useState<WebSocketMessage[]>([])
  const [ws, setWs] = useState<WebSocket | null>(null)

  useEffect(() => {
    // WebSocket підключення
    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'
    const websocket = new WebSocket(`${wsUrl}/ws/graph-updates`)

    websocket.onopen = () => {
      console.log('✅ WebSocket підключено')
      setWsStatus('connected')
    }

    websocket.onmessage = (event) => {
      try {
        const data: WebSocketMessage = JSON.parse(event.data)
        console.log('📨 Отримано:', data)
        setMessages((prev) => [...prev, data].slice(-10)) // Останні 10 повідомлень
      } catch (error) {
        console.error('❌ Помилка парсингу:', error)
      }
    }

    websocket.onerror = (error) => {
      console.error('❌ WebSocket помилка:', error)
      setWsStatus('error')
    }

    websocket.onclose = () => {
      console.log('🔌 WebSocket відключено')
      setWsStatus('disconnected')
    }

    setWs(websocket)

    // Cleanup при демонтажі
    return () => {
      websocket.close()
    }
  }, [])

  const sendTestMessage = () => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      const message = {
        type: 'test',
        content: 'Привіт з фронтенду!',
        timestamp: new Date().toISOString(),
      }
      ws.send(JSON.stringify(message))
      console.log('📤 Відправлено:', message)
    }
  }

  const getStatusColor = () => {
    switch (wsStatus) {
      case 'connected':
        return '#4ade80'
      case 'connecting':
        return '#fbbf24'
      case 'error':
        return '#ef4444'
      default:
        return '#6b7280'
    }
  }

  const getStatusText = () => {
    switch (wsStatus) {
      case 'connected':
        return 'Підключено'
      case 'connecting':
        return 'Підключення...'
      case 'error':
        return 'Помилка'
      default:
        return 'Відключено'
    }
  }

  return (
    <div className={styles.container}>
      <main className={styles.main}>
        <h1 className={styles.title}>
          🧠 AgentMind
        </h1>
        
        <p className={styles.description}>
          Платформа для управління пам'яттю самонавчальних ШІ-агентів
        </p>

        <div className={styles.statusCard}>
          <div className={styles.statusRow}>
            <span className={styles.statusLabel}>WebSocket:</span>
            <div className={styles.statusIndicator}>
              <div 
                className={styles.statusDot}
                style={{ backgroundColor: getStatusColor() }}
              />
              <span className={styles.statusText}>{getStatusText()}</span>
            </div>
          </div>
        </div>

        {wsStatus === 'connected' && (
          <button className={styles.button} onClick={sendTestMessage}>
            📤 Відправити тестове повідомлення
          </button>
        )}

        {messages.length > 0 && (
          <div className={styles.messagesCard}>
            <h3 className={styles.messagesTitle}>📨 Останні повідомлення:</h3>
            <div className={styles.messagesList}>
              {messages.map((msg, idx) => (
                <div key={idx} className={styles.message}>
                  <div className={styles.messageType}>{msg.type}</div>
                  <div className={styles.messageContent}>
                    {JSON.stringify(msg, null, 2)}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className={styles.infoCard}>
          <h3 className={styles.infoTitle}>ℹ️ Інформація</h3>
          <ul className={styles.infoList}>
            <li>✅ Frontend: Next.js 14</li>
            <li>✅ Backend: FastAPI</li>
            <li>✅ WebSocket: Реальний час</li>
            <li>✅ Database: FalkorDB</li>
          </ul>
        </div>

        <div className={styles.footer}>
          <p>Версія 0.1.0 • Етап 0: Фундамент завершено</p>
        </div>
      </main>
    </div>
  )
}
