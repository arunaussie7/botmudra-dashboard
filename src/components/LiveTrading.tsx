import React, { useEffect, useState } from 'react';
import io from 'socket.io-client';
import axios from 'axios';

interface AccountInfo {
  login: number;
  balance: number;
  equity: number;
  margin: number;
  free_margin: number;
  margin_level: number;
  leverage: number;
  currency: string;
}

interface Position {
  ticket: number;
  symbol: string;
  type: string;
  volume: number;
  open_price: number;
  current_price: number;
  sl: number;
  tp: number;
  profit: number;
  swap: number;
  open_time: string;
  comment: string;
}

interface PendingOrder {
  ticket: number;
  symbol: string;
  type: number;
  volume: number;
  price: number;
  sl: number;
  tp: number;
  time_setup: string;
}

interface ClosedOrder {
  ticket: number;
  symbol: string;
  type: string;
  volume: number;
  price: number;
  profit: number;
  swap: number;
  commission: number;
  time: string;
  comment: string;
}

interface MT5Data {
  account_info: AccountInfo;
  open_positions: Position[];
  pending_orders: PendingOrder[];
  closed_orders: ClosedOrder[];
  last_update: string;
}

interface SymbolResponse {
    data: string[];
}

const LiveTrading: React.FC = () => {
  const [mt5Data, setMT5Data] = useState<MT5Data | null>(null);
  const [connected, setConnected] = useState(false);
  const [availableSymbols, setAvailableSymbols] = useState<string[]>([]);
  const [symbolSearch, setSymbolSearch] = useState('');
  const [selectedSymbol1, setSelectedSymbol1] = useState('');
  const [selectedSymbol2, setSelectedSymbol2] = useState('');

  useEffect(() => {
    const socket = io('http://localhost:5000', {
      transports: ['websocket'],
      upgrade: false
    });

    socket.on('connect', () => {
      setConnected(true);
      console.log('Connected to server');
    });

    socket.on('disconnect', () => {
      setConnected(false);
      console.log('Disconnected from server');
    });

    socket.on('mt5_data', (data: MT5Data) => {
      setMT5Data(data);
    });

    return () => {
      socket.disconnect();
    };
  }, []);

  useEffect(() => {
    // Fetch available symbols
    const fetchSymbols = async () => {
      try {
        const response = await axios.get<string[]>('http://localhost:5000/get_symbols');
        if (Array.isArray(response.data)) {
          setAvailableSymbols(response.data);
          if (response.data.length > 0) {
            setSelectedSymbol1(response.data[0]);
            setSelectedSymbol2(response.data[1]);
          }
        }
      } catch (error) {
        console.error('Failed to fetch symbols:', error);
      }
    };
    
    fetchSymbols();
  }, []);

  const formatMoney = (amount: number, currency: string = 'USD') => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency
    }).format(amount);
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString();
  };

  const getOrderTypeName = (type: number) => {
    const types = {
      0: 'Buy',
      1: 'Sell',
      2: 'Buy Limit',
      3: 'Sell Limit',
      4: 'Buy Stop',
      5: 'Sell Stop'
    };
    return types[type as keyof typeof types] || type;
  };

  const filteredSymbols = availableSymbols.filter(symbol =>
    symbol.toLowerCase().includes(symbolSearch.toLowerCase())
  );

  // Add this new component for symbol selection
  const SymbolSelector = ({ value, onChange, label }: { value: string; onChange: (value: string) => void; label: string }) => (
  <div className="mb-4">
    <label className="block text-sm font-medium text-gray-700">{label}</label>
    <div className="mt-1">
      <input
        type="text"
        placeholder="Search symbols..."
        className="p-2 border rounded w-full mb-2"
        value={symbolSearch}
        onChange={(e) => setSymbolSearch(e.target.value)}
      />
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
      >
        {filteredSymbols.map(symbol => (
          <option key={symbol} value={symbol}>
            {symbol}
          </option>
        ))}
      </select>
    </div>
  </div>
);

  return (
    <div className="container mx-auto p-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <SymbolSelector
          value={selectedSymbol1}
          onChange={setSelectedSymbol1}
          label="Symbol 1"
        />
        <SymbolSelector
          value={selectedSymbol2}
          onChange={setSelectedSymbol2}
          label="Symbol 2"
        />
      </div>
      
      <div className="live-trading">
        <h2>Live Trading Activity</h2>
        <div className={`connection-status ${connected ? 'connected' : 'disconnected'}`}>
          Status: {connected ? 'Connected' : 'Disconnected'}
        </div>
        
        {mt5Data ? (
          <div className="trading-info">
            <div className="account-summary">
              <h3>Account Summary</h3>
              <div className="summary-grid">
                <div className="summary-item">
                  <label>Account:</label>
                  <span>{mt5Data.account_info.login}</span>
                </div>
                <div className="summary-item">
                  <label>Balance:</label>
                  <span>{formatMoney(mt5Data.account_info.balance, mt5Data.account_info.currency)}</span>
                </div>
                <div className="summary-item">
                  <label>Equity:</label>
                  <span>{formatMoney(mt5Data.account_info.equity, mt5Data.account_info.currency)}</span>
                </div>
                <div className="summary-item">
                  <label>Margin:</label>
                  <span>{formatMoney(mt5Data.account_info.margin, mt5Data.account_info.currency)}</span>
                </div>
                <div className="summary-item">
                  <label>Free Margin:</label>
                  <span>{formatMoney(mt5Data.account_info.free_margin, mt5Data.account_info.currency)}</span>
                </div>
                <div className="summary-item">
                  <label>Margin Level:</label>
                  <span>{mt5Data.account_info.margin_level}%</span>
                </div>
                <div className="summary-item">
                  <label>Leverage:</label>
                  <span>1:{mt5Data.account_info.leverage}</span>
                </div>
              </div>
              <p className="last-update">Last Update: {formatDate(mt5Data.last_update)}</p>
            </div>
            
            <div className="orders">
              <div className="orders-section">
                <h3>Open Positions</h3>
                {mt5Data.open_positions.length === 0 ? (
                  <p className="no-orders">No open positions</p>
                ) : (
                  <div className="orders-list">
                    {mt5Data.open_positions.map((position) => (
                      <div key={position.ticket} className="order-item">
                        <div className="order-header">
                          <span className="symbol">{position.symbol}</span>
                          <span className={`type ${position.type.toLowerCase()}`}>
                            {position.type.toUpperCase()}
                          </span>
                        </div>
                        <div className="order-details">
                          <div>Volume: {position.volume}</div>
                          <div>Open: {formatMoney(position.open_price)}</div>
                          <div>Current: {formatMoney(position.current_price)}</div>
                          <div>SL: {position.sl ? formatMoney(position.sl) : 'None'}</div>
                          <div>TP: {position.tp ? formatMoney(position.tp) : 'None'}</div>
                          <div className={`profit ${position.profit >= 0 ? 'positive' : 'negative'}`}>
                            Profit: {formatMoney(position.profit)}
                          </div>
                          <div>Swap: {formatMoney(position.swap)}</div>
                          <div className="time">Opened: {formatDate(position.open_time)}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="orders-section">
                <h3>Pending Orders</h3>
                {mt5Data.pending_orders.length === 0 ? (
                  <p className="no-orders">No pending orders</p>
                ) : (
                  <div className="orders-list">
                    {mt5Data.pending_orders.map((order) => (
                      <div key={order.ticket} className="order-item">
                        <div className="order-header">
                          <span className="symbol">{order.symbol}</span>
                          <span className="type">{getOrderTypeName(order.type)}</span>
                        </div>
                        <div className="order-details">
                          <div>Volume: {order.volume}</div>
                          <div>Price: {formatMoney(order.price)}</div>
                          <div>SL: {order.sl ? formatMoney(order.sl) : 'None'}</div>
                          <div>TP: {order.tp ? formatMoney(order.tp) : 'None'}</div>
                          <div className="time">Setup: {formatDate(order.time_setup)}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
              
              <div className="orders-section">
                <h3>Today's Trades</h3>
                {mt5Data.closed_orders.length === 0 ? (
                  <p className="no-orders">No trades today</p>
                ) : (
                  <div className="orders-list">
                    {mt5Data.closed_orders.map((order) => (
                      <div key={order.ticket} className="order-item">
                        <div className="order-header">
                          <span className="symbol">{order.symbol}</span>
                          <span className={`type ${order.type.toLowerCase()}`}>
                            {order.type.toUpperCase()}
                          </span>
                        </div>
                        <div className="order-details">
                          <div>Volume: {order.volume}</div>
                          <div>Price: {formatMoney(order.price)}</div>
                          <div className={`profit ${order.profit >= 0 ? 'positive' : 'negative'}`}>
                            Profit: {formatMoney(order.profit)}
                          </div>
                          <div>Swap: {formatMoney(order.swap)}</div>
                          <div>Commission: {formatMoney(order.commission)}</div>
                          <div className="time">
                            {formatDate(order.time)}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        ) : (
          <div className="loading">Loading MT5 data...</div>
        )}
      </div>
    </div>
  );
};

export default LiveTrading; 