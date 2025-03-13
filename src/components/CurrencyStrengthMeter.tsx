import React, { useEffect, useState } from 'react';
import axios from 'axios';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';

interface CurrencyStrength {
  timestamp: string;
  USD: number;
  EUR: number;
  GBP: number;
  JPY: number;
  AUD: number;
  NZD: number;
  CAD: number;
  CHF: number;
}

const CURRENCIES = ['USD', 'EUR', 'GBP', 'JPY', 'AUD', 'NZD', 'CAD', 'CHF'];
const COLORS = {
  USD: '#e91e63',
  EUR: '#ff4081',
  GBP: '#00bcd4',
  JPY: '#ff9800',
  AUD: '#2196f3',
  NZD: '#3f51b5',
  CAD: '#673ab7',
  CHF: '#4caf50'
};

const CurrencyStrengthMeter: React.FC = () => {
  const [strengthData, setStrengthData] = useState<CurrencyStrength[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchStrengthData();
    const interval = setInterval(fetchStrengthData, 60000); // Update every minute
    return () => clearInterval(interval);
  }, []);

  const fetchStrengthData = async () => {
    try {
      const response = await axios.get('http://localhost:5000/api/currency_strength');
      setStrengthData(response.data);
      setLoading(false);
    } catch (err) {
      setError('Failed to fetch currency strength data');
      setLoading(false);
    }
  };

  if (loading) return <div>Loading currency strength data...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div className="p-4">
      <h2 className="text-2xl font-bold mb-4">Currency Strength Meter</h2>
      <div className="mb-4">
        <div className="flex flex-wrap gap-2 mb-4">
          {CURRENCIES.map(currency => (
            <div
              key={currency}
              className="px-3 py-1 rounded-full text-white"
              style={{ backgroundColor: COLORS[currency as keyof typeof COLORS] }}
            >
              {currency}
            </div>
          ))}
        </div>
      </div>
      <div className="h-[500px]">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={strengthData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="timestamp"
              tickFormatter={(value) => new Date(value).toLocaleTimeString()}
            />
            <YAxis />
            <Tooltip
              labelFormatter={(value) => new Date(value).toLocaleString()}
              contentStyle={{ backgroundColor: '#fff', border: '1px solid #ccc' }}
            />
            <Legend />
            {CURRENCIES.map(currency => (
              <Line
                key={currency}
                type="monotone"
                dataKey={currency}
                stroke={COLORS[currency as keyof typeof COLORS]}
                dot={false}
                strokeWidth={2}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default CurrencyStrengthMeter; 