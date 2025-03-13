from flask import Flask, render_template, request, jsonify
import MetaTrader5 as mt5
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import pytz

app = Flask(__name__)

# MT5 credentials - Replace with your credentials
MT5_CONFIG = {
    "server": "Exness-MT5Trial7",
    "login": 203405414,
    "password": "Arun@123"
}

def connect_mt5():
    """Initialize and test MT5 connection"""
    try:
        # Shutdown existing connections
        mt5.shutdown()
        
        # Initialize MT5
        if not mt5.initialize():
            error = mt5.last_error()
            print(f"Failed to initialize MT5: {error}")
            return False, f"Failed to initialize MT5: {error}"
        
        # Attempt to login
        if not mt5.login(login=MT5_CONFIG["login"], 
                        password=MT5_CONFIG["password"], 
                        server=MT5_CONFIG["server"]):
            error = mt5.last_error()
            print(f"Failed to login to MT5: {error}")
            return False, f"Failed to login to MT5: {error}"
            
        # Get account info to verify connection
        account_info = mt5.account_info()
        if account_info is None:
            error = mt5.last_error()
            print(f"Failed to get account info: {error}")
            return False, f"Failed to get account info: {error}"
            
        print(f"Successfully connected to MT5 account {account_info.login}")
        print(f"Balance: {account_info.balance}")
        print(f"Equity: {account_info.equity}")
        return True, "Connected successfully"
        
    except Exception as e:
        print(f"Exception in connect_mt5: {str(e)}")
        return False, str(e)

def calculate_rsi(prices, period=14):
    """Calculate RSI for a price series"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def get_account_data():
    """Get current account information and positions"""
    try:
        account_info = mt5.account_info()
        if account_info is None:
            return None

        # Get open positions
        positions = mt5.positions_get()
        open_positions = []
        if positions:
            for pos in positions:
                open_positions.append({
                    "ticket": pos.ticket,
                    "symbol": pos.symbol,
                    "type": "Buy" if pos.type == 0 else "Sell",
                    "volume": pos.volume,
                    "open_price": pos.price_open,
                    "current_price": pos.price_current,
                    "profit": pos.profit,
                    "swap": pos.swap,
                    "sl": pos.sl,
                    "tp": pos.tp
                })

        # Get all closed trades (history)
        from_date = datetime(2000, 1, 1)  # Start from a very old date to get all history
        to_date = datetime.now()
        deals = mt5.history_deals_get(from_date, to_date)
        closed_orders = []
        if deals:
            for deal in deals:
                closed_orders.append({
                    "ticket": deal.ticket,
                    "symbol": deal.symbol,
                    "type": "Buy" if deal.type == 0 else "Sell",
                    "volume": deal.volume,
                    "price": deal.price,
                    "profit": deal.profit,
                    "commission": deal.commission,
                    "swap": deal.swap,
                    "time": datetime.fromtimestamp(deal.time)
                })
            
            # Sort by time, most recent first
            closed_orders.sort(key=lambda x: x["time"], reverse=True)

        return {
            "account": {
                "login": account_info.login,
                "server": account_info.server,
                "balance": account_info.balance,
                "equity": account_info.equity,
                "margin": account_info.margin,
                "free_margin": account_info.margin_free,
                "margin_level": account_info.margin_level
            },
            "positions": open_positions,
            "history": closed_orders,
            "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        print(f"Error getting account data: {e}")
        return None

@app.route('/')
def index():
    """Main dashboard page"""
    data = get_account_data()
    if data is None:
        return "Error: Could not connect to MT5"
    return render_template('dashboard.html', data=data)

@app.route('/get_symbols')
def get_symbols():
    """Get available trading symbols"""
    try:
        # Get all symbols from MT5
        all_symbols = mt5.symbols_get()
        if all_symbols is None:
            return jsonify({'error': 'Failed to get symbols'}), 500
            
        # Filter for forex pairs and format them
        available_pairs = []
        for symbol in all_symbols:
            # Include both standard forex pairs (6 chars) and pairs with 'm' suffix
            if (len(symbol.name) == 6 or (len(symbol.name) == 7 and symbol.name.endswith('m'))) and symbol.trade_mode != 0:
                available_pairs.append(symbol.name)
        
        # Sort the pairs alphabetically
        available_pairs.sort()
        
        return jsonify(available_pairs)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/analyze_correlation', methods=['POST'])
def analyze_correlation():
    """Analyze correlation between two symbols"""
    try:
        print("Received correlation analysis request")
        data = request.get_json()
        print(f"Request data: {data}")
        
        # Extract parameters
        pair1 = data.get('pair1')
        pair2 = data.get('pair2')
        timeframe = data.get('timeframe', 'H4')
        bars = int(data.get('analysis_period', 30)) * 24
        rsi_period = int(data.get('rsi_period', 14))
        rsi_overbought = float(data.get('rsi_overbought', 70))
        rsi_oversold = float(data.get('rsi_oversold', 30))
        corr_entry_threshold = float(data.get('corr_entry_threshold', 0.7))
        corr_exit_threshold = float(data.get('corr_exit_threshold', 0.3))

        print(f"Processing pairs: {pair1} and {pair2}")
        print(f"Timeframe: {timeframe}, Bars: {bars}")

        # Map timeframe
        tf_map = {
            'M1': mt5.TIMEFRAME_M1,
            'M5': mt5.TIMEFRAME_M5,
            'M15': mt5.TIMEFRAME_M15,
            'M30': mt5.TIMEFRAME_M30,
            'H1': mt5.TIMEFRAME_H1,
            'H4': mt5.TIMEFRAME_H4,
            'D1': mt5.TIMEFRAME_D1
        }
        mt5_timeframe = tf_map.get(timeframe, mt5.TIMEFRAME_H4)

        # Get price data
        rates1 = mt5.copy_rates_from_pos(pair1, mt5_timeframe, 0, bars)
        rates2 = mt5.copy_rates_from_pos(pair2, mt5_timeframe, 0, bars)
        
        print(f"Retrieved data - Pair1: {rates1 is not None}, Pair2: {rates2 is not None}")
        
        if rates1 is None or rates2 is None:
            error_msg = f"Failed to fetch price data for {pair1 if rates1 is None else pair2}"
            print(f"Error: {error_msg}")
            return jsonify({'error': error_msg}), 400
            
        # Convert to DataFrames
        df1 = pd.DataFrame(rates1)
        df2 = pd.DataFrame(rates2)
        
        print(f"DataFrame shapes - Pair1: {df1.shape}, Pair2: {df2.shape}")
        
        # Calculate returns
        df1['returns'] = df1['close'].pct_change()
        df2['returns'] = df2['close'].pct_change()
        
        # Calculate RSI
        df1['rsi'] = calculate_rsi(df1['close'], rsi_period)
        df2['rsi'] = calculate_rsi(df2['close'], rsi_period)
        
        # Calculate correlations
        price_corr = df1['close'].corr(df2['close'])
        rsi_corr = df1['rsi'].corr(df2['rsi'])
        returns_corr = df1['returns'].corr(df2['returns'])
        
        print(f"Correlations - Price: {price_corr}, RSI: {rsi_corr}, Returns: {returns_corr}")
        
        # Calculate rolling correlation
        rolling_corr = df1['close'].rolling(window=20).corr(df2['close'])
        
        # Calculate additional statistics
        stats1 = {
            'mean': float(df1['close'].mean()),
            'std': float(df1['close'].std()),
            'min': float(df1['close'].min()),
            'max': float(df1['close'].max()),
            'volatility': float(df1['returns'].std() * np.sqrt(252)),  # Annualized volatility
            'skewness': float(df1['returns'].skew()),
            'kurtosis': float(df1['returns'].kurtosis()),
            'sharpe': float((df1['returns'].mean() / df1['returns'].std()) * np.sqrt(252)) if df1['returns'].std() != 0 else 0,
            'current_price': float(df1['close'].iloc[-1]),
            'price_change': float((df1['close'].iloc[-1] / df1['close'].iloc[0] - 1) * 100)  # Percentage change
        }
        
        stats2 = {
            'mean': float(df2['close'].mean()),
            'std': float(df2['close'].std()),
            'min': float(df2['close'].min()),
            'max': float(df2['close'].max()),
            'volatility': float(df2['returns'].std() * np.sqrt(252)),  # Annualized volatility
            'skewness': float(df2['returns'].skew()),
            'kurtosis': float(df2['returns'].kurtosis()),
            'sharpe': float((df2['returns'].mean() / df2['returns'].std()) * np.sqrt(252)) if df2['returns'].std() != 0 else 0,
            'current_price': float(df2['close'].iloc[-1]),
            'price_change': float((df2['close'].iloc[-1] / df2['close'].iloc[0] - 1) * 100)  # Percentage change
        }

        # Analyze correlation signals
        signals = []
        in_trade = False
        current_signal = None
        
        for i, corr in enumerate(rolling_corr):
            if pd.isna(corr):
                continue
                
            if not in_trade and abs(corr) >= corr_entry_threshold:
                current_signal = {
                    'start_index': i,
                    'start_corr': float(corr) if not pd.isna(corr) else None
                }
                in_trade = True
            elif in_trade and abs(corr) <= corr_exit_threshold:
                current_signal['end_index'] = i
                current_signal['end_corr'] = float(corr) if not pd.isna(corr) else None
                current_signal['duration'] = i - current_signal['start_index']
                signals.append(current_signal)
                current_signal = None
                in_trade = False

        # Calculate statistics, handling NaN values
        signal_durations = [s['duration'] for s in signals]
        avg_duration = float(np.mean(signal_durations)) if signal_durations else 0
        max_duration = float(np.max(signal_durations)) if signal_durations else 0

        print("Preparing response data")
        response = {
            'timestamps': [datetime.fromtimestamp(x).strftime('%Y-%m-%d %H:%M') for x in df1['time']],
            'prices1': [float(x) if not pd.isna(x) else None for x in df1['close']],
            'prices2': [float(x) if not pd.isna(x) else None for x in df2['close']],
            'rsi1': [float(x) if not pd.isna(x) else None for x in df1['rsi']],
            'rsi2': [float(x) if not pd.isna(x) else None for x in df2['rsi']],
            'rolling_correlation': [float(x) if not pd.isna(x) else None for x in rolling_corr],
            'price_correlation': float(price_corr) if not pd.isna(price_corr) else None,
            'rsi_correlation': float(rsi_corr) if not pd.isna(rsi_corr) else None,
            'returns_correlation': float(returns_corr) if not pd.isna(returns_corr) else None,
            'signals': signals,
            'stats': {
                'total_signals': len(signals),
                'avg_duration': float(avg_duration) if not pd.isna(avg_duration) else 0,
                'max_duration': float(max_duration) if not pd.isna(max_duration) else 0,
                'current_correlation': float(rolling_corr.iloc[-1]) if len(rolling_corr) > 0 and not pd.isna(rolling_corr.iloc[-1]) else None
            },
            'pair1_stats': stats1,
            'pair2_stats': stats2
        }
        
        print("Sending response")
        return jsonify(response)
        
    except Exception as e:
        print(f"Error in analyze_correlation: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/place_trade', methods=['POST'])
def place_trade():
    """Place a new trade"""
    try:
        data = request.get_json()
        symbol = data.get('symbol')
        trade_type = data.get('type')  # 'buy' or 'sell'
        volume = float(data.get('volume', 0.01))
        sl = float(data.get('sl', 0))
        tp = float(data.get('tp', 0))
        
        # Get current price
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            return jsonify({'error': f'Symbol {symbol} not found'}), 400
            
        price = symbol_info.ask if trade_type.lower() == 'buy' else symbol_info.bid
        
        # Prepare trade request
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": mt5.ORDER_TYPE_BUY if trade_type.lower() == 'buy' else mt5.ORDER_TYPE_SELL,
            "price": price,
            "sl": sl,
            "tp": tp,
            "deviation": 20,
            "magic": 234000,
            "comment": "python trade",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        # Send trade
        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            return jsonify({'error': f'Trade failed: {result.comment}'}), 400
            
        return jsonify({
            'success': True,
            'order': {
                'ticket': result.order,
                'volume': volume,
                'price': price
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/close_trade', methods=['POST'])
def close_trade():
    """Close an existing trade"""
    try:
        data = request.get_json()
        ticket = data.get('ticket')
        
        position = mt5.positions_get(ticket=ticket)
        if not position:
            return jsonify({'error': 'Position not found'}), 400
            
        position = position[0]
        
        # Prepare close request
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": position.symbol,
            "volume": position.volume,
            "type": mt5.ORDER_TYPE_SELL if position.type == 0 else mt5.ORDER_TYPE_BUY,
            "position": position.ticket,
            "price": mt5.symbol_info_tick(position.symbol).bid if position.type == 0 else mt5.symbol_info_tick(position.symbol).ask,
            "deviation": 20,
            "magic": 234000,
            "comment": "python close",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        # Send close request
        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            return jsonify({'error': f'Close failed: {result.comment}'}), 400
            
        return jsonify({
            'success': True,
            'closed_position': {
                'ticket': ticket,
                'profit': position.profit
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/update_account')
def update_account():
    """Get latest account information"""
    data = get_account_data()
    if data is None:
        return jsonify({'error': 'Failed to get account data'}), 500
    return jsonify(data)

@app.route('/correlation')
def correlation():
    """Correlation analysis page"""
    return render_template('correlation.html')

@app.route('/strength')
def strength():
    """Currency Strength Meter page"""
    return render_template('strength.html')

@app.route('/pair_movements')
def pair_movements():
    """Pair Movements Analysis page"""
    return render_template('pair_movements.html')

@app.route('/market_movements')
def market_movements():
    """Market Movements page"""
    return render_template('market_movements.html')

@app.route('/api/all_symbols', methods=['GET'])
def get_all_symbols():
    """Get all available currency pairs and their current data"""
    try:
        # Get all symbols
        all_symbols = mt5.symbols_get()
        if all_symbols is None:
            return jsonify({"error": "Failed to get symbols", "details": mt5.last_error()}), 400

        symbols_data = []
        for symbol in all_symbols:
            # Only include forex pairs (they typically contain both currencies separated by a slash)
            if '/' in symbol.name or len(symbol.name) == 6:  # Standard forex pair length is 6 (e.g., EURUSD)
                # Get the last tick
                tick = mt5.symbol_info_tick(symbol.name)
                if tick is not None:
                    # Get daily OHLCV data
                    today = datetime.now()
                    rates = mt5.copy_rates_from(symbol.name, mt5.TIMEFRAME_D1, today, 1)
                    
                    if rates is not None and len(rates) > 0:
                        rate = rates[0]
                        symbols_data.append({
                            "symbol": symbol.name,
                            "bid": tick.bid,
                            "ask": tick.ask,
                            "spread": symbol.spread,
                            "digits": symbol.digits,
                            "open": rate['open'],
                            "high": rate['high'],
                            "low": rate['low'],
                            "close": rate['close'],
                            "volume": rate['tick_volume'],
                            "description": symbol.description,
                            "trade_mode": symbol.trade_mode,
                            "currency_base": symbol.currency_base,
                            "currency_profit": symbol.currency_profit
                        })

        return jsonify({
            "status": "success",
            "count": len(symbols_data),
            "symbols": symbols_data
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/currency_strength')
def get_currency_strength():
    """Calculate and return currency strength for all major currencies"""
    try:
        # Get timeframe from query parameter, default to '1D'
        timeframe = request.args.get('timeframe', '1D')
        
        # Map timeframe to MT5 timeframe
        tf_map = {
            '1D': mt5.TIMEFRAME_D1,
            '4H': mt5.TIMEFRAME_H4
        }
        mt5_timeframe = tf_map.get(timeframe, mt5.TIMEFRAME_D1)
        
        currencies = [
            'USD', 'EUR', 'GBP', 'JPY', 'AUD', 'NZD', 'CAD', 'CHF',
            'SEK', 'NOK', 'SGD', 'HKD', 'TRY', 'ZAR', 'MXN', 'CNY', 'INR', 'BRL'
        ]
        
        # Define all possible pairs with 'm' suffix
        pairs = [
            # Major pairs
            'EURUSDm', 'GBPUSDm', 'USDJPYm', 'AUDUSDm', 'NZDUSDm', 'USDCADm', 'USDCHFm',
            'EURGBPm', 'EURJPYm', 'EURAUDm', 'EURNZDm', 'EURCADm', 'EURCHFm',
            'GBPJPYm', 'GBPAUDm', 'GBPNZDm', 'GBPCADm', 'GBPCHFm',
            'AUDJPYm', 'NZDJPYm', 'CADJPYm', 'CHFJPYm',
            'AUDNZDm', 'AUDCADm', 'AUDCHFm',
            'NZDCADm', 'NZDCHFm',
            'CADCHFm',
            
            # Additional pairs
            'USDSEKm', 'USDNOKm', 'USDSGDm', 'USDHKDm', 'USDTRYm', 'USDZARm',
            'USDMXNm', 'USDCNHm', 'USDINRm', 'USDBRLm',
            'EURSEKm', 'EURNOKm', 'EURTRYm', 'EURZARm', 'EURMXNm',
            'GBPSEKm', 'GBPNOKm', 'GBPTRYm', 'GBPZARm',
            'CHFTRYm', 'CHFNOKm', 'CHFSEKm', 'JPYTRYm'
        ]

        # Initialize currency scores
        currency_scores = {currency: 0.0 for currency in currencies}
        valid_pairs_count = {currency: 0 for currency in currencies}

        # Calculate strength based on current prices
        for pair in pairs:
            tick = mt5.symbol_info_tick(pair)
            if tick is not None:
                base = pair[:3]
                quote = pair[3:6]  # Exclude the 'm' suffix
                
                # Get current and previous prices based on timeframe
                rates = mt5.copy_rates_from_pos(pair, mt5_timeframe, 0, 2)
                if rates is not None and len(rates) >= 2:
                    prev_close = rates[0]['close']
                    curr_close = rates[1]['close']
                    
                    # Calculate price change percentage
                    change = ((curr_close - prev_close) / prev_close) * 100
                    
                    # Update scores
                    if base in currency_scores:
                        currency_scores[base] += change
                        valid_pairs_count[base] += 1
                    if quote in currency_scores:
                        currency_scores[quote] -= change
                        valid_pairs_count[quote] += 1

        # Average the scores by the number of pairs for each currency
        for currency in currencies:
            if valid_pairs_count[currency] > 0:
                currency_scores[currency] /= valid_pairs_count[currency]

        # Normalize scores to 0-100 range
        min_score = min(currency_scores.values())
        max_score = max(currency_scores.values())
        score_range = max_score - min_score if max_score != min_score else 1

        normalized_scores = {}
        for currency in currencies:
            normalized_scores[currency] = ((currency_scores[currency] - min_score) / score_range) * 100

        # Create response with current timestamp and timeframe
        strength_data = [{
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'timeframe': timeframe,
            **normalized_scores
        }]

        return jsonify(strength_data)
        
    except Exception as e:
        print(f"Error calculating currency strength: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/strongest_currencies')
def get_strongest_currencies():
    """Get the strongest currencies with their details"""
    try:
        # Get all symbols with 'm' suffix
        all_symbols = mt5.symbols_get()
        if all_symbols is None:
            return jsonify({"error": "Failed to get symbols"}), 500

        # Get currency strength data
        strength_data = get_currency_strength().get_json()
        if not strength_data or 'error' in strength_data:
            return jsonify({"error": "Failed to get currency strength"}), 500

        latest_strength = strength_data[0]  # Get the latest strength data
        
        # Get the strongest currencies sorted by strength
        currencies = [
            'USD', 'EUR', 'GBP', 'JPY', 'AUD', 'NZD', 'CAD', 'CHF',
            'SEK', 'NOK', 'SGD', 'HKD', 'TRY', 'ZAR', 'MXN', 'CNY', 'INR', 'BRL'
        ]
        
        currency_data = []
        for currency in currencies:
            # Find a representative pair for this currency (preferably against USD)
            base_pair = None
            if currency != 'USD':
                base_pair = f"{currency}USDm"
            else:
                base_pair = "EURUSDm"  # Use EURUSD for USD strength
            
            # Get the latest tick and daily change
            if base_pair:
                tick = mt5.symbol_info_tick(base_pair)
                rates = mt5.copy_rates_from_pos(base_pair, mt5.TIMEFRAME_D1, 0, 2)
                
                if tick is not None and rates is not None and len(rates) >= 2:
                    prev_close = rates[0]['close']
                    curr_close = rates[1]['close']
                    
                    # Calculate change
                    change_pct = ((curr_close - prev_close) / prev_close) * 100
                    change_pips = (curr_close - prev_close) * (10000 if 'JPY' not in base_pair else 100)
                    
                    # Adjust for quote currency
                    if currency == 'USD':
                        change_pct *= -1
                        change_pips *= -1
                    
                    currency_data.append({
                        'currency': currency,
                        'strength': latest_strength[currency],
                        'change_percent': change_pct,
                        'change_pips': change_pips,
                        'last_price': curr_close
                    })
        
        # Sort by strength in descending order
        currency_data.sort(key=lambda x: x['strength'], reverse=True)
        
        return jsonify({
            'timestamp': latest_strength['timestamp'],
            'currencies': currency_data
        })
        
    except Exception as e:
        print(f"Error getting strongest currencies: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/strongest_pairs')
def get_strongest_pairs():
    """Get the strongest currency pairs with their details"""
    try:
        print("Fetching strongest pairs...")
        # Get all symbols with 'm' suffix
        all_symbols = mt5.symbols_get()
        if all_symbols is None:
            print("Failed to get symbols from MT5")
            return jsonify({"error": "Failed to get symbols"}), 500

        pairs_data = []
        for symbol in all_symbols:
            # Only include forex pairs with 'm' suffix
            if (len(symbol.name) == 7 and symbol.name.endswith('m')) and symbol.trade_mode != 0:
                print(f"Processing pair: {symbol.name}")
                # Get the latest tick and daily change
                tick = mt5.symbol_info_tick(symbol.name)
                rates = mt5.copy_rates_from_pos(symbol.name, mt5.TIMEFRAME_D1, 0, 2)
                
                if tick is not None and rates is not None and len(rates) >= 2:
                    prev_close = rates[0]['close']
                    curr_close = rates[1]['close']
                    
                    # Calculate changes
                    change_pct = ((curr_close - prev_close) / prev_close) * 100
                    change_pips = (curr_close - prev_close) * (10000 if 'JPY' not in symbol.name else 100)
                    
                    pairs_data.append({
                        'symbol': symbol.name[:-1],  # Remove 'm' suffix
                        'change_percent': change_pct,
                        'change_pips': change_pips,
                        'last_price': curr_close,
                        'spread': symbol.spread,
                        'volume': int(rates[1]['tick_volume'])  # Convert uint64 to int
                    })
                    print(f"Added pair {symbol.name[:-1]} with change {change_pct:.2f}%")
        
        if not pairs_data:
            print("No pairs data collected")
            return jsonify({"error": "No pairs data available"}), 500
            
        # Sort by absolute percentage change in descending order
        pairs_data.sort(key=lambda x: abs(x['change_percent']), reverse=True)
        
        response_data = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'pairs': pairs_data[:20]  # Return top 20 most volatile pairs
        }
        print(f"Returning {len(response_data['pairs'])} pairs")
        return jsonify(response_data)
        
    except Exception as e:
        print(f"Error getting strongest pairs: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/market_movements')
def get_market_movements():
    """Get market movements data including volatility and sentiment"""
    try:
        # Get timeframe from query parameter, default to '1H'
        timeframe = request.args.get('timeframe', '1H')
        
        # Map timeframe to MT5 timeframe and number of candles
        tf_map = {
            '1H': (mt5.TIMEFRAME_H1, 1),
            '2H': (mt5.TIMEFRAME_H1, 2),  # Use 2 1-hour candles for 2H
            '1D': (mt5.TIMEFRAME_D1, 1)
        }
        mt5_timeframe, num_candles = tf_map.get(timeframe, (mt5.TIMEFRAME_H1, 1))
        
        # Get major pairs data
        major_pairs = ['EURUSDm', 'GBPUSDm', 'USDJPYm', 'USDCHFm', 'USDCADm', 'AUDUSDm', 'NZDUSDm']
        major_pairs_data = []
        
        for pair in major_pairs:
            rates = mt5.copy_rates_from_pos(pair, mt5_timeframe, 0, num_candles + 1)
            if rates is not None and len(rates) >= num_candles + 1:
                prev_close = rates[0]['close']
                curr_close = rates[-1]['close']
                change = ((curr_close - prev_close) / prev_close) * 100
                major_pairs_data.append({
                    'symbol': pair[:-1],
                    'change': change
                })
        
        # Get volatility data (24-hour)
        volatility_data = {
            'timestamps': [],
            'values': []
        }
        
        for pair in major_pairs:
            rates = mt5.copy_rates_from_pos(pair, mt5.TIMEFRAME_H1, 0, 24)
            if rates is not None:
                for i, rate in enumerate(rates):
                    if i == 0:
                        continue
                    timestamp = datetime.fromtimestamp(rate['time']).strftime('%H:%M')
                    volatility = abs((rate['high'] - rate['low']) / rate['low'] * 100)
                    
                    if i >= len(volatility_data['timestamps']):
                        volatility_data['timestamps'].append(timestamp)
                        volatility_data['values'].append(volatility)
                    else:
                        volatility_data['values'][i-1] += volatility
        
        # Average volatility across pairs
        volatility_data['values'] = [v / len(major_pairs) for v in volatility_data['values']]
        
        # Calculate market sentiment
        sentiment_data = {
            'bullish': 0,
            'bearish': 0,
            'neutral': 0
        }
        
        all_symbols = mt5.symbols_get()
        if all_symbols is not None:
            for symbol in all_symbols:
                if (len(symbol.name) == 7 and symbol.name.endswith('m')) and symbol.trade_mode != 0:
                    rates = mt5.copy_rates_from_pos(symbol.name, mt5_timeframe, 0, num_candles + 1)
                    if rates is not None and len(rates) >= num_candles + 1:
                        change = ((rates[-1]['close'] - rates[0]['close']) / rates[0]['close']) * 100
                        if change > 0.1:
                            sentiment_data['bullish'] += 1
                        elif change < -0.1:
                            sentiment_data['bearish'] += 1
                        else:
                            sentiment_data['neutral'] += 1
        
        # Get detailed movement analysis
        movements = []
        for symbol in all_symbols:
            if (len(symbol.name) == 7 and symbol.name.endswith('m')) and symbol.trade_mode != 0:
                rates = mt5.copy_rates_from_pos(symbol.name, mt5_timeframe, 0, 20)
                if rates is not None and len(rates) >= num_candles + 1:
                    curr_close = rates[-1]['close']
                    prev_close = rates[0]['close']
                    change = ((curr_close - prev_close) / prev_close) * 100
                    pips = (curr_close - prev_close) * (10000 if 'JPY' not in symbol.name else 100)
                    
                    # Calculate volatility
                    volatility = np.std([((r['high'] - r['low']) / r['low']) * 100 for r in rates])
                    
                    # Determine trend
                    closes = [r['close'] for r in rates]
                    ma_short = np.mean(closes[-5:])
                    ma_long = np.mean(closes[-20:])
                    trend = 'up' if ma_short > ma_long else 'down' if ma_short < ma_long else 'neutral'
                    
                    movements.append({
                        'symbol': symbol.name[:-1],
                        'change': change,
                        'pips': abs(pips),
                        'volatility': volatility,
                        'trend': trend
                    })
        
        # Sort movements by absolute change
        movements.sort(key=lambda x: abs(x['change']), reverse=True)
        
        return jsonify({
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'timeframe': timeframe,
            'major_pairs': major_pairs_data,
            'volatility': volatility_data,
            'sentiment': sentiment_data,
            'movements': movements[:30]  # Return top 30 movements
        })
        
    except Exception as e:
        print(f"Error getting market movements: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/account_info')
def get_account_info():
    """Get current account information and positions"""
    try:
        # Get account info
        account_info = mt5.account_info()
        if account_info is None:
            return jsonify({'error': 'Failed to get account info'}), 500

        # Get open positions
        positions = mt5.positions_get()
        positions_list = []
        
        if positions is not None:
            for pos in positions:
                positions_list.append({
                    'ticket': pos.ticket,
                    'symbol': pos.symbol,
                    'type': 'Buy' if pos.type == 0 else 'Sell',
                    'volume': pos.volume,
                    'price_open': pos.price_open,
                    'price_current': pos.price_current,
                    'profit': pos.profit,
                    'swap': pos.swap,
                    'time': datetime.fromtimestamp(pos.time).strftime('%Y-%m-%d %H:%M:%S')
                })

        # Get closed trades (last 24 hours by default)
        from_date = datetime.now() - timedelta(days=1)
        closed_trades = mt5.history_deals_get(from_date)
        closed_trades_list = []

        if closed_trades is not None:
            for trade in closed_trades:
                if trade.type <= 1:  # Only include buy and sell trades
                    closed_trades_list.append({
                        'ticket': trade.ticket,
                        'symbol': trade.symbol,
                        'type': 'Buy' if trade.type == 0 else 'Sell',
                        'volume': trade.volume,
                        'price': trade.price,
                        'profit': trade.profit,
                        'time': datetime.fromtimestamp(trade.time).strftime('%Y-%m-%d %H:%M:%S')
                    })

        return jsonify({
            'balance': account_info.balance,
            'equity': account_info.equity,
            'margin_free': account_info.margin_free,
            'floating_pl': account_info.equity - account_info.balance,
            'positions': positions_list,
            'closed_trades': closed_trades_list
        })

    except Exception as e:
        print(f"Error in get_account_info: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/strength_data')
def get_strength_data():
    try:
        currencies = ['EUR', 'USD', 'GBP', 'JPY', 'CHF', 'AUD', 'CAD', 'NZD']
        currency_data = []
        
        for currency in currencies:
            # Calculate strength based on multiple pairs
            pairs = []
            strength = 0
            total_weight = 0
            
            # Define pairs for each currency
            if currency == 'USD':
                pairs = ['EURUSD', 'GBPUSD', 'AUDUSD', 'NZDUSD', 'USDCHF', 'USDJPY', 'USDCAD']
            elif currency == 'EUR':
                pairs = ['EURUSD', 'EURGBP', 'EURAUD', 'EURNZD', 'EURCHF', 'EURJPY', 'EURCAD']
            elif currency == 'GBP':
                pairs = ['GBPUSD', 'EURGBP', 'GBPAUD', 'GBPNZD', 'GBPCHF', 'GBPJPY', 'GBPCAD']
            else:
                # For other currencies, create pairs with major currencies
                for major in ['USD', 'EUR', 'GBP']:
                    if major != currency:
                        pairs.append(f"{currency}{major}")
                        pairs.append(f"{major}{currency}")
            
            # Calculate weighted strength
            for pair in pairs:
                try:
                    rates = mt5.copy_rates_from_pos(pair + 'm', mt5.TIMEFRAME_H1, 0, 2)
                    if rates is not None and len(rates) >= 2:
                        prev_close = rates[0]['close']
                        curr_close = rates[1]['close']
                        
                        # Calculate change percentage
                        change = ((curr_close - prev_close) / prev_close) * 100
                        
                        # Adjust change based on position in pair
                        if pair.startswith(currency):
                            strength += change
                        else:
                            strength -= change
                            
                        total_weight += 1
                except:
                    continue
            
            # Calculate average strength
            avg_strength = strength / total_weight if total_weight > 0 else 0
            
            # Normalize to 0-1 range (will be converted to percentage in frontend)
            normalized_strength = (avg_strength + 5) / 10  # Assuming typical range is -5% to +5%
            normalized_strength = max(0, min(1, normalized_strength))  # Clamp between 0 and 1
            
            currency_data.append({
                'code': currency,
                'strength': round(normalized_strength, 3),
                'change': round(avg_strength, 3)
            })
        
        # Sort by strength
        currency_data.sort(key=lambda x: x['strength'], reverse=True)
        
        # Calculate opportunities
        opportunities = []
        for i in range(len(currency_data)):
            for j in range(i + 1, len(currency_data)):
                strong = currency_data[i]
                weak = currency_data[j]
                strength_diff = strong['strength'] - weak['strength']
                
                if strength_diff > 0.3:  # Only show significant differences
                    opportunities.append({
                        'pair': f"{strong['code']}/{weak['code']}",
                        'type': 'Buy',
                        'strength_diff': round(strength_diff * 100, 1)
                    })
                elif strength_diff < -0.3:
                    opportunities.append({
                        'pair': f"{weak['code']}/{strong['code']}",
                        'type': 'Sell',
                        'strength_diff': round(abs(strength_diff) * 100, 1)
                    })
        
        return jsonify({
            'currencies': currency_data,
            'opportunities': sorted(opportunities, key=lambda x: x['strength_diff'], reverse=True)[:5],
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
    except Exception as e:
        print(f"Error in get_strength_data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/pair_movements')
def get_pair_movements():
    """Get all pairs that moved more than 1% in last 2 hours with their graph data"""
    try:
        # Get all symbols with 'm' suffix
        all_symbols = mt5.symbols_get()
        if all_symbols is None:
            return jsonify({"error": "Failed to get symbols"}), 500

        pairs_data = []
        for symbol in all_symbols:
            # Only include forex pairs with 'm' suffix
            if (len(symbol.name) == 7 and symbol.name.endswith('m')) and symbol.trade_mode != 0:
                # Get 2 hours of data with 5-minute intervals (24 points)
                rates = mt5.copy_rates_from_pos(symbol.name, mt5.TIMEFRAME_M5, 0, 24)
                
                if rates is not None and len(rates) >= 24:
                    # Calculate percentage change from 2 hours ago
                    start_price = rates[0]['close']
                    current_price = rates[-1]['close']
                    change_pct = ((current_price - start_price) / start_price) * 100
                    
                    # Only include pairs that moved more than 1%
                    if abs(change_pct) >= 1:
                        # Prepare graph data
                        graph_data = {
                            'timestamps': [datetime.fromtimestamp(rate['time']).strftime('%H:%M') for rate in rates],
                            'prices': [rate['close'] for rate in rates]
                        }
                        
                        pairs_data.append({
                            'symbol': symbol.name[:-1],  # Remove 'm' suffix
                            'change_percent': change_pct,
                            'start_price': start_price,
                            'current_price': current_price,
                            'graph_data': graph_data
                        })
        
        # Sort by absolute percentage change in descending order
        pairs_data.sort(key=lambda x: abs(x['change_percent']), reverse=True)
        
        return jsonify({
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'pairs': pairs_data
        })
        
    except Exception as e:
        print(f"Error getting pair movements: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/closed_trades')
def get_closed_trades():
    """Get all closed trades history"""
    try:
        print("Starting to fetch closed trades...")
        
        # First ensure we have a valid MT5 connection
        if not mt5.initialize():
            return jsonify({'error': 'Failed to initialize MT5 connection', 'trades': []})
            
        # Reconnect to the account if needed
        if not mt5.login(login=MT5_CONFIG["login"], 
                        password=MT5_CONFIG["password"], 
                        server=MT5_CONFIG["server"]):
            return jsonify({'error': 'Failed to login to MT5', 'trades': []})
        
        # Use a very old start date to get all history
        start_time = datetime(2000, 1, 1)
        end_time = datetime.now()
        
        print(f"Fetching trades from {start_time} to {end_time}")
        
        # Get all deals from MT5
        deals = mt5.history_deals_get(start_time, end_time)
        
        if deals is None:
            error = mt5.last_error()
            error_msg = f"Failed to get trades: {error}" if error else "No trades found"
            print(error_msg)
            return jsonify({'error': error_msg, 'trades': []})
        
        print(f"Found {len(deals)} total deals")
        
        # Process and format trades
        processed_trades = []
        positions_dict = {}  # To store position info
        
        # First pass: collect all positions
        for deal in deals:
            if deal.position_id not in positions_dict:
                positions_dict[deal.position_id] = {
                    'open_time': deal.time,
                    'open_price': deal.price,
                    'close_time': deal.time,
                    'close_price': deal.price,
                    'profit': deal.profit,
                    'volume': deal.volume,
                    'symbol': deal.symbol,
                    'type': deal.type,
                    'commission': deal.commission,
                    'swap': deal.swap
                }
            else:
                # Update position with closing details
                pos = positions_dict[deal.position_id]
                if deal.time > pos['close_time']:
                    pos['close_time'] = deal.time
                    pos['close_price'] = deal.price
                    pos['profit'] += deal.profit
                    pos['commission'] += deal.commission
                    pos['swap'] += deal.swap
        
        # Convert positions to trades
        for pos_id, pos in positions_dict.items():
            if pos['profit'] != 0:  # Only include completed trades
                processed_trades.append({
                    'close_time': int(pos['close_time'] * 1000),  # Convert to milliseconds for JS
                    'symbol': pos['symbol'],
                    'type': 'buy' if pos['type'] == 0 else 'sell',
                    'volume': float(pos['volume']),
                    'open_price': float(pos['open_price']),
                    'close_price': float(pos['close_price']),
                    'profit': float(pos['profit']),
                    'commission': float(pos['commission']),
                    'swap': float(pos['swap'])
                })
        
        print(f"Successfully processed {len(processed_trades)} valid trades")
        
        # Sort by close time, most recent first
        processed_trades.sort(key=lambda x: x['close_time'], reverse=True)
        
        return jsonify({
            'trades': processed_trades,
            'total_trades': len(processed_trades),
            'start_time': start_time.strftime('%Y-%m-%d %H:%M:%S'),
            'end_time': end_time.strftime('%Y-%m-%d %H:%M:%S')
        })
        
    except Exception as e:
        print(f"Error in get_closed_trades: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e), 'trades': []}), 500

if __name__ == '__main__':
    success, message = connect_mt5()
    if success:
        app.run(host='0.0.0.0', debug=True)
    else:
        print(f"Failed to start: {message}") 