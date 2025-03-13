# Trading Website Documentation

## Project Overview
A comprehensive trading platform that integrates with MetaTrader 5 (MT5) to provide real-time trading capabilities, market analysis, and trade management features.

## Detailed Project Structure and Working

### 1. Root Directory
```
Trading website/
├── app.py
├── config.py
├── requirements.txt
├── README.md
├── templates/
├── static/
└── src/
```

#### Core Files Working
- `app.py`: 
  - Main application entry point
  - Handles MT5 connection and authentication
  - Manages API routes and request handling
  - Processes trade execution and management
  - Functions:
    - `connect_mt5()`: Establishes MT5 connection
    - `get_account_info()`: Fetches real-time account data
    - `get_positions()`: Retrieves open positions
    - `get_closed_trades()`: Gets historical trade data
    - `place_trade()`: Executes new trades
    - `close_trade()`: Closes existing positions

- `config.py`:
  - Stores configuration settings
  - MT5 credentials and server details
  - API keys and security settings
  - Database configurations
  - Environment variables

### 2. Templates Directory (`/templates`)
```
templates/
├── dashboard.html
├── index.html
├── strength.html
├── correlation.html
└── pair_movements.html
```

#### Working of Each Template
- `dashboard.html`:
  - Main trading interface
  - Components:
    - Account summary section (balance, equity)
    - TradingView chart integration
    - Open positions table with real-time updates
    - Closed trades history with filtering
    - Trade execution panel
  - Features:
    - Real-time data updates via WebSocket
    - Interactive chart controls
    - Trade management buttons
    - Risk calculation tools

- `index.html`:
  - Landing page
  - Login/Registration forms
  - Platform features showcase
  - Quick access to different analysis tools

- `strength.html`:
  - Currency strength analysis
  - Components:
    - Strength indicators for major currencies
    - Historical strength charts
    - Comparison tools
    - Time period selectors

- `correlation.html`:
  - Pair correlation analysis
  - Features:
    - Correlation matrix
    - Heat maps
    - Historical correlation data
    - Custom timeframe selection

- `pair_movements.html`:
  - Market movement analysis
  - Components:
    - Price action indicators
    - Trend analysis
    - Volume analysis
    - Support/Resistance levels

### 3. Static Directory (`/static`)
```
static/
├── css/
│   ├── main.css
│   ├── dashboard.css
│   └── charts.css
├── js/
│   ├── trading.js
│   ├── charts.js
│   └── websocket.js
├── images/
│   ├── flags/
│   └── icons/
└── lib/
    ├── tradingview/
    └── technical-indicators/
```

#### Working of Static Components
- `css/`:
  - `main.css`: Global styles and layouts
  - `dashboard.css`: Trading dashboard specific styles
  - `charts.css`: Chart customization and widgets

- `js/`:
  - `trading.js`:
    - Trade execution logic
    - Position management
    - Risk calculation
    - Order validation

  - `charts.js`:
    - TradingView chart configuration
    - Custom indicator setup
    - Chart event handlers
    - Technical analysis tools

  - `websocket.js`:
    - Real-time data handling
    - Price updates
    - Position tracking
    - Account updates

- `images/`:
  - Currency flags for visual identification
  - UI icons and symbols
  - Platform logos and branding

- `lib/`:
  - Third-party libraries and dependencies
  - Custom technical indicators
  - Chart plugins and extensions

### 4. Source Directory (`/src`)
```
src/
├── components/
│   ├── AllSymbols.tsx
│   └── LiveTrading.tsx
├── utils/
│   ├── tradingUtils.ts
│   └── dataProcessing.ts
└── types/
    └── trading.d.ts
```

#### Working of Source Components
- `components/`:
  - `AllSymbols.tsx`:
    - Symbol list management
    - Market watch functionality
    - Price updates handling
    - Symbol filtering and search

  - `LiveTrading.tsx`:
    - Real-time trading interface
    - Order execution
    - Position tracking
    - Risk management tools

- `utils/`:
  - Trading utilities and helpers
  - Data processing functions
  - API integration helpers
  - Common calculations

### 5. Data Flow and Integration

#### Trading Flow
1. User Authentication:
   ```
   Login → MT5 Connection → Session Management
   ```

2. Market Data Flow:
   ```
   MT5 → WebSocket → Frontend Updates
   ```

3. Trade Execution:
   ```
   User Input → Validation → MT5 Execution → Position Update
   ```

4. Analysis Tools:
   ```
   Market Data → Processing → Visualization → User Interface
   ```

### 6. Real-time Updates Implementation
- WebSocket connections for live data
- Event-driven architecture for updates
- Optimized data processing
- Efficient state management

### 7. Error Handling and Logging
- Comprehensive error tracking
- System status monitoring
- Performance metrics
- Debug logging

### 8. Security Implementation
- Secure MT5 integration
- Data encryption
- Session management
- API authentication

### 9. Development and Deployment
- Local development setup
- Testing procedures
- Deployment process
- Maintenance routines

## Getting Started

### Development Setup
1. Clone repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure MT5:
   ```python
   # config.py
   MT5_CONFIG = {
       "login": "your_login",
       "password": "your_password",
       "server": "your_server"
   }
   ```
4. Start development server:
   ```bash
   python app.py
   ```

### Production Deployment
1. Set environment variables
2. Configure production server
3. Setup SSL certificates
4. Deploy application

## Support and Maintenance
- Regular updates and patches
- Technical support
- Feature requests
- Bug reporting

## License
[Your License Type] - See LICENSE file for details 