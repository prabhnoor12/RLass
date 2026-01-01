import React, { useEffect, useRef, useState } from 'react';
import { connectUsageDashboard } from '../../api/usage_dashboard';
import { Line } from 'react-chartjs-2';

interface UsageDashboardProps {
  userId: string;
}

const UsageDashboard: React.FC<UsageDashboardProps> = ({ userId }) => {
  const [stats, setStats] = useState<any>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    wsRef.current = connectUsageDashboard(userId, setStats);
    return () => {
      wsRef.current?.close();
    };
  }, [userId]);

  if (!stats) return <div>Loading usage data...</div>;

  // Example: render endpoint usage as a chart
  const endpoints = stats.usage_summary?.map((item: any) => item.endpoint || 'unknown');
  const counts = stats.usage_summary?.map((item: any) => item.count);

  const chartData = {
    labels: endpoints,
    datasets: [
      {
        label: 'Usage by Endpoint',
        data: counts,
        fill: false,
        borderColor: 'rgb(75, 192, 192)',
        tension: 0.1,
      },
    ],
  };

  return (
    <div>
      <h2>Real-time Usage & Quota Dashboard</h2>
      <Line data={chartData} />
      {/* Add more charts for error types, time windows, etc. */}
    </div>
  );
};

export default UsageDashboard;
