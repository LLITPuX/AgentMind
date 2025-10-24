'use client'

import { useEffect, useState } from 'react'
import dynamic from 'next/dynamic';
import styles from './page.module.css'
import { getFullGraph, GraphData } from '../services/api';
import InteractionPanel from '../components/InteractionPanel';

const GraphVisualizer = dynamic(() => import('../components/GraphVisualizer'), {
    ssr: false,
});

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
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], links: [] });
  const [stmSize, setStmSize] = useState(0);
  const [lastSearchResult, setLastSearchResult] = useState<any>(null);
  const [lastConsolidationResult, setLastConsolidationResult] = useState<any>(null);
  const [isConsolidating, setIsConsolidating] = useState(false);


  // Initial graph data fetch
  useEffect(() => {
    const fetchGraphData = async () => {
        try {
            const data = await getFullGraph();
            setGraphData(data);
        } catch (error) {
            console.error('Failed to fetch initial graph data:', error);
        }
    };
    fetchGraphData();
  }, []);


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

        if (data.type === 'graph_update' && data.payload) {
            setGraphData(data.payload as GraphData);
            setIsConsolidating(false); // Consolidation finished
        }

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
          An interface for observing and interacting with an AI agent's memory.
        </p>

        <InteractionPanel
            onConsolidationStart={() => {
                setIsConsolidating(true);
                setLastConsolidationResult(null);
            }}
            onConsolidationComplete={(result) => setLastConsolidationResult(result)}
            onSearchResult={(result) => setLastSearchResult(result)}
            onStmUpdate={(newSize) => setStmSize(newSize)}
        />
        
        <div className={styles.graphContainer}>
            <GraphVisualizer graphData={graphData} />
        </div>

        <div className={styles.statusAndResults}>
            <div className={styles.statusCard}>
              <h3 className={styles.cardTitle}>System Status</h3>
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
              <div className={styles.statusRow}>
                <span className={styles.statusLabel}>STM Observations:</span>
                <span className={styles.statusValue}>{stmSize}</span>
              </div>
               <div className={styles.statusRow}>
                <span className={styles.statusLabel}>LTM Nodes:</span>
                <span className={styles.statusValue}>{graphData.nodes.length}</span>
              </div>
              <div className={styles.statusRow}>
                <span className={styles.statusLabel}>LTM Edges:</span>
                <span className={styles.statusValue}>{graphData.links.length}</span>
              </div>
               {isConsolidating && (
                <div className={styles.statusRow}>
                    <span className={styles.statusLabel}>Consolidation:</span>
                    <span className={styles.statusValue}>In Progress...</span>
                </div>
              )}
            </div>

            {lastSearchResult && (
                <div className={styles.resultsCard}>
                    <h3 className={styles.cardTitle}>Last Search Result</h3>
                    <p className={styles.resultsText}>{lastSearchResult.response}</p>
                </div>
            )}
        </div>

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
          <p>Version 1.0.0 • Stage 5: Full Stack Integration</p>
        </div>
      </main>
    </div>
  )
}
