import React, { useState, useEffect } from 'react';
import axios from 'axios';

interface SymbolData {
    symbol: string;
    bid: number;
    ask: number;
    spread: number;
    digits: number;
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
    description: string;
    trade_mode: number;
    currency_base: string;
    currency_profit: string;
}

const AllSymbols: React.FC = () => {
    const [symbols, setSymbols] = useState<SymbolData[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [searchTerm, setSearchTerm] = useState('');
    const [sortConfig, setSortConfig] = useState<{ key: keyof SymbolData; direction: 'asc' | 'desc' } | null>(null);

    useEffect(() => {
        fetchSymbols();
        const interval = setInterval(fetchSymbols, 5000); // Update every 5 seconds
        return () => clearInterval(interval);
    }, []);

    const fetchSymbols = async () => {
        try {
            const response = await axios.get('http://localhost:5000/api/all_symbols');
            setSymbols(response.data.symbols);
            setLoading(false);
        } catch (err) {
            setError('Failed to fetch symbols data');
            setLoading(false);
        }
    };

    const handleSort = (key: keyof SymbolData) => {
        let direction: 'asc' | 'desc' = 'asc';
        if (sortConfig && sortConfig.key === key && sortConfig.direction === 'asc') {
            direction = 'desc';
        }
        setSortConfig({ key, direction });
    };

    const filteredAndSortedSymbols = React.useMemo(() => {
        let result = [...symbols];
        
        // Apply search filter
        if (searchTerm) {
            result = result.filter(symbol => 
                symbol.symbol.toLowerCase().includes(searchTerm.toLowerCase()) ||
                symbol.description.toLowerCase().includes(searchTerm.toLowerCase())
            );
        }

        // Apply sorting
        if (sortConfig) {
            result.sort((a, b) => {
                if (a[sortConfig.key] < b[sortConfig.key]) return sortConfig.direction === 'asc' ? -1 : 1;
                if (a[sortConfig.key] > b[sortConfig.key]) return sortConfig.direction === 'asc' ? 1 : -1;
                return 0;
            });
        }

        return result;
    }, [symbols, searchTerm, sortConfig]);

    if (loading) return <div>Loading symbols data...</div>;
    if (error) return <div>Error: {error}</div>;

    return (
        <div className="p-4">
            <div className="mb-4">
                <input
                    type="text"
                    placeholder="Search symbols..."
                    className="p-2 border rounded w-full"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                />
            </div>
            <div className="overflow-x-auto">
                <table className="min-w-full bg-white border rounded-lg">
                    <thead>
                        <tr className="bg-gray-100">
                            <th className="p-3 cursor-pointer" onClick={() => handleSort('symbol')}>Symbol</th>
                            <th className="p-3 cursor-pointer" onClick={() => handleSort('bid')}>Bid</th>
                            <th className="p-3 cursor-pointer" onClick={() => handleSort('ask')}>Ask</th>
                            <th className="p-3 cursor-pointer" onClick={() => handleSort('spread')}>Spread</th>
                            <th className="p-3 cursor-pointer" onClick={() => handleSort('high')}>High</th>
                            <th className="p-3 cursor-pointer" onClick={() => handleSort('low')}>Low</th>
                            <th className="p-3 cursor-pointer" onClick={() => handleSort('volume')}>Volume</th>
                            <th className="p-3">Description</th>
                        </tr>
                    </thead>
                    <tbody>
                        {filteredAndSortedSymbols.map((symbol, index) => (
                            <tr key={symbol.symbol} className={index % 2 === 0 ? 'bg-gray-50' : ''}>
                                <td className="p-3 font-medium">{symbol.symbol}</td>
                                <td className="p-3">{symbol.bid.toFixed(symbol.digits)}</td>
                                <td className="p-3">{symbol.ask.toFixed(symbol.digits)}</td>
                                <td className="p-3">{symbol.spread}</td>
                                <td className="p-3">{symbol.high.toFixed(symbol.digits)}</td>
                                <td className="p-3">{symbol.low.toFixed(symbol.digits)}</td>
                                <td className="p-3">{symbol.volume}</td>
                                <td className="p-3">{symbol.description}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default AllSymbols; 