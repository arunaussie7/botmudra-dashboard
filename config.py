# MetaTrader 5 Configuration
MT5_CONFIG = {
    "login": 203405414,  # Your MT5 account number
    "password": "3nq1hkxw",  # Your MT5 password
    "server": "MetaQuotes-Demo",  # Your MT5 server
    "timeout": 60000,  # Timeout in milliseconds
}

# Server Configuration
SERVER_CONFIG = {
    "host": "0.0.0.0",
    "port": 5000,
    "debug": True,
    "use_reloader": True
}

# WebSocket Configuration
WEBSOCKET_CONFIG = {
    "ping_interval": 25,
    "ping_timeout": 10,
    "max_message_size": 1024 * 1024
}

# Security Configuration
SECURITY_CONFIG = {
    "session_lifetime": 3600,  # Session lifetime in seconds
    "max_login_attempts": 3,
    "password_min_length": 8
}

# Trading Configuration
TRADING_CONFIG = {
    "default_lot_size": 0.01,
    "max_lot_size": 100.0,
    "min_lot_size": 0.01,
    "default_stop_loss_pips": 50,
    "default_take_profit_pips": 100,
    "max_slippage": 3,
    "default_deviation": 20
}

# Symbols Configuration
SYMBOLS_CONFIG = {
    "default_pairs": [
        "EURUSD", "GBPUSD", "USDJPY", "USDCHF",
        "AUDUSD", "NZDUSD", "USDCAD", "EURJPY"
    ],
    "chart_timeframes": [
        "M1", "M5", "M15", "M30",
        "H1", "H4", "D1", "W1", "MN"
    ]
}

# Database Configuration (if needed)
DATABASE_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "trading_db",
    "user": "trading_user",
    "password": "trading_password"
}

# Logging Configuration
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": "trading_app.log",
    "max_size": 10 * 1024 * 1024,  # 10 MB
    "backup_count": 5
}

# API Rate Limits
RATE_LIMIT_CONFIG = {
    "default": "100/minute",
    "trading": "10/minute",
    "market_data": "1000/minute"
}

# Cache Configuration
CACHE_CONFIG = {
    "type": "redis",
    "host": "localhost",
    "port": 6379,
    "ttl": 300  # Time to live in seconds
}

# Error Messages
ERROR_MESSAGES = {
    "mt5_connection": "Failed to connect to MT5 terminal",
    "invalid_credentials": "Invalid MT5 credentials",
    "trade_failed": "Trade execution failed",
    "invalid_symbol": "Invalid trading symbol",
    "invalid_volume": "Invalid trading volume",
    "insufficient_margin": "Insufficient margin for trade",
    "market_closed": "Market is closed",
    "invalid_sl_tp": "Invalid Stop Loss or Take Profit levels"
}

# Success Messages
SUCCESS_MESSAGES = {
    "mt5_connected": "Successfully connected to MT5",
    "trade_executed": "Trade executed successfully",
    "position_closed": "Position closed successfully",
    "order_modified": "Order modified successfully"
} 