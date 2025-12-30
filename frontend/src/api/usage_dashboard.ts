import axios from 'axios';

export const connectUsageDashboard = (userId: string, onMessage: (data: any) => void) => {
  const ws = new WebSocket(`${import.meta.env.VITE_API_WS_URL || 'ws://localhost:8000'}/usage-dashboard/ws/usage-dashboard/${userId}`);
  ws.onmessage = (event) => {
    onMessage(JSON.parse(event.data));
  };
  return ws;
};
