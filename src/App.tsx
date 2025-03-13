import React from 'react';
import './App.css';
import LiveTrading from './components/LiveTrading';
import AllSymbols from './components/AllSymbols';
import CurrencyStrengthMeter from './components/CurrencyStrengthMeter';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>MT5 Trading Dashboard</h1>
        <p>Account: Exness-MT5Trial7 (203405414)</p>
      </header>
      <main>
        <div className="grid grid-cols-1 gap-4">
          <section>
            <h2 className="text-xl font-bold mb-4">Currency Strength Analysis</h2>
            <CurrencyStrengthMeter />
          </section>
          <section>
            <h2 className="text-xl font-bold mb-4">Live Trading</h2>
            <LiveTrading />
          </section>
          <section>
            <h2 className="text-xl font-bold mb-4">All Currency Pairs</h2>
            <AllSymbols />
          </section>
        </div>
      </main>
    </div>
  );
}

export default App; 