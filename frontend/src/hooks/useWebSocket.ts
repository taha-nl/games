import { useEffect, useRef } from 'react'

type Handlers = Record<string, (data: Record<string, unknown>) => void>

export function useWebSocket(url: string, handlers: Handlers) {
  const wsRef = useRef<WebSocket | null>(null)
  const handlersRef = useRef(handlers)
  handlersRef.current = handlers

  useEffect(() => {
    let cancelled = false

    function connect() {
      if (cancelled) return
      const ws = new WebSocket(url)
      wsRef.current = ws

      ws.onmessage = (e) => {
        try {
          const msg = JSON.parse(e.data) as { type: string } & Record<string, unknown>
          const handler = handlersRef.current[msg.type]
          if (handler) handler(msg)
        } catch { /* ignore malformed messages */ }
      }

      ws.onclose = () => {
        if (!cancelled) setTimeout(connect, 2000)
      }
    }

    connect()
    return () => {
      cancelled = true
      wsRef.current?.close()
    }
  }, [url])
}
