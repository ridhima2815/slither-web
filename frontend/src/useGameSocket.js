import { useCallback, useEffect, useRef, useState } from "react";

// Override with VITE_WS_URL when the backend isn't on port 8000 of this host.
function wsUrl() {
  return (
    import.meta.env.VITE_WS_URL ??
    `${location.protocol === "https:" ? "wss" : "ws"}://${location.hostname}:8000/ws`
  );
}

/**
 * Owns the WebSocket. Reconnects with backoff when it drops.
 * `stateRef` always holds the newest server snapshot (read by the canvas loop);
 * `state` mirrors it for React components (HUD, overlays).
 */
export function useGameSocket() {
  const [conn, setConn] = useState("connecting"); // connecting | open | reconnecting
  const [state, setState] = useState(null);
  const stateRef = useRef(null);
  const wsRef = useRef(null);

  const send = useCallback((cmd) => {
    const ws = wsRef.current;
    if (ws && ws.readyState === WebSocket.OPEN) ws.send(cmd);
  }, []);

  useEffect(() => {
    let disposed = false;
    let attempt = 0;
    let timer;

    const open = () => {
      const ws = new WebSocket(wsUrl());
      wsRef.current = ws;
      ws.onopen = () => {
        attempt = 0;
        setConn("open");
      };
      ws.onmessage = (e) => {
        let msg;
        try {
          msg = JSON.parse(e.data);
        } catch {
          return;
        }
        if (msg.type === "state") {
          stateRef.current = msg;
          setState(msg);
        }
      };
      ws.onclose = () => {
        if (disposed) return;
        setConn("reconnecting");
        attempt += 1;
        timer = setTimeout(open, Math.min(500 * 2 ** attempt, 4000));
      };
      ws.onerror = () => ws.close();
    };

    open();
    return () => {
      disposed = true;
      clearTimeout(timer);
      wsRef.current?.close();
    };
  }, []);

  return { conn, state, stateRef, send };
}
