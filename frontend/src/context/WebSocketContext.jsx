import React, { createContext, useContext, useEffect, useRef, useState, useCallback } from 'react';
import { useAuth } from './AuthContext';
import { getAccessToken } from '../api/axios';

const WebSocketContext = createContext(null);

export function WebSocketProvider({ children }) {
  const { isAuthenticated } = useAuth();
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef(null);
  const listenersRef = useRef(new Map());
  const reconnectTimeoutRef = useRef(null);

  const connect = useCallback(() => {
    const token = getAccessToken();
    if (!isAuthenticated || !token) return;

    if (wsRef.current && (wsRef.current.readyState === WebSocket.OPEN || wsRef.current.readyState === WebSocket.CONNECTING)) {
      return;
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const defaultWsUrl = `${protocol}//${window.location.hostname}:8000/api/v1/ws`;
    const baseWsUrl = import.meta.env.VITE_WS_URL || defaultWsUrl;
    const wsUrl = baseWsUrl.includes('?') ? `${baseWsUrl}&token=${token}` : `${baseWsUrl}?token=${token}`;

    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current);
          reconnectTimeoutRef.current = null;
        }
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          const eventName = data.event;
          if (eventName && listenersRef.current.has(eventName)) {
            listenersRef.current.get(eventName).forEach((cb) => cb(data.payload));
          }
        } catch (e) {
          console.error('Error parsing WebSocket message:', e);
        }
      };

      ws.onclose = (e) => {
        setIsConnected(false);
        wsRef.current = null;
        // Auto-reconnect after 3 seconds if not intentionally closed by logout
        if (e.code !== 1000) {
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, 3000);
        }
      };

      ws.onerror = (err) => {
        console.error('WebSocket error:', err);
      };
    } catch (e) {
      console.error('WebSocket init error:', e);
    }
  }, [isAuthenticated]);

  useEffect(() => {
    const token = getAccessToken();
    if (isAuthenticated && token) {
      connect();
    } else {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close(1000, 'User logged out');
        wsRef.current = null;
      }
      setIsConnected(false);
    }

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close(1000);
      }
    };
  }, [isAuthenticated, connect]);

  const send = useCallback((cmd, payload) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      const msg = JSON.stringify({ v: 1, cmd, payload });
      wsRef.current.send(msg);
      return true;
    }
    return false;
  }, []);

  const subscribe = useCallback((eventName, callback) => {
    if (!listenersRef.current.has(eventName)) {
      listenersRef.current.set(eventName, new Set());
    }
    listenersRef.current.get(eventName).add(callback);

    return () => {
      if (listenersRef.current.has(eventName)) {
        listenersRef.current.get(eventName).delete(callback);
      }
    };
  }, []);

  return (
    <WebSocketContext.Provider value={{ isConnected, send, subscribe }}>
      {children}
    </WebSocketContext.Provider>
  );
}

export function useWebSocket() {
  return useContext(WebSocketContext);
}
