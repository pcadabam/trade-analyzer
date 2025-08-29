# Zerodha Trade Analyzer

Analyze your Zerodha trading data to get actionable insights on closed trades, optimize exit strategies, and identify behavioral patterns using **real market data** from multiple sources.

## Features

### 📊 Core Analysis
- **P&L Analysis**: Track profit/loss across all closed trades
- **Win/Loss Statistics**: Analyze win rates and success patterns
- **Stock Performance**: Identify best and worst performing stocks
- **Behavioral Insights**: Detect trading patterns and biases

### 🔍 What-If Analysis
- **Individual Trade Analysis**: Deep-dive into any trade with candlestick charts
- **Real Price Data Integration**: Fetch actual market prices during your trades
- **Exit Scenario Simulation**: See what would have happened with different exit strategies:
  - Best early exit opportunities
  - Best late exit opportunities  
  - Trailing stop-loss simulation
- **Technical Indicators**: RSI, SMA, VWAP, and volume analysis at entry/exit points
- **Trade-Specific Insights**: Personalized recommendations for each trade

### 💡 Enhanced Insights
- **Real Exit Optimization**: Based on actual price movements, not just patterns
- **Missed Opportunity Analysis**: Quantify profits left on the table
- **Trailing Stop Benefits**: Calculate exact benefits of using trailing stops
- **Volatility Assessment**: Identify high-risk trades based on actual price swings

### 📡 Multi-Source Data Reliability
- **Primary Source**: Yahoo Finance (100% reliability)
- **Secondary Sources**: Google Finance, Alpha Vantage 
- **Intelligent Fallback**: Automatically tries multiple sources if one fails
- **Rate Limiting**: Respects API limits and prevents overuse
- **Source Status**: Real-time monitoring of data source health

## Installation

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Or using pip
pip install -r requirements.txt
```

## Configuration

### Optional: Set up Alpha Vantage API (Free Backup Source)
1. Get a free API key from [Alpha Vantage](https://www.alphavantage.co/support/#api-key)
2. Set environment variable:
```bash
export ALPHA_VANTAGE_API_KEY=your_api_key_here
```

## Usage

1. **Export your trades from Zerodha Console**:
   - Log into Zerodha Console
   - Go to Reports → P&L → Tradebook
   - Export as CSV

2. **Run the app**:
```bash
uv run streamlit run app.py
```

3. **Upload your CSV** and explore insights

## Sample Data & Demo Generation

### Pre-built Demo Files
- `data/demo/demo_tradebook.csv` - Mixed portfolio (30 days)
- `data/demo/tech_trader_demo.csv` - Tech-focused aggressive trader (45 days) 
- `data/demo/bank_trader_demo.csv` - Banking sector swing trader (60 days)
- `data/demo/conservative_trader_demo.csv` - Conservative long-term trader (90 days)

### Generate Custom Demo Data
Use the CLI tool to create realistic demo data with actual market prices:

```bash
# Generate tech sector demo
uv run python generate_demo_cli.py \
  --stocks TCS,INFY,WIPRO,TECHM \
  --days 45 \
  --output data/demo/my_tech_demo.csv \
  --win-rate 0.52 \
  --intraday-ratio 0.8 \
  --avg-quantity 40

# Generate banking sector demo  
uv run python generate_demo_cli.py \
  --stocks HDFC,ICICIBANK,AXISBANK,SBIN \
  --days 60 \
  --output data/demo/my_bank_demo.csv \
  --win-rate 0.64 \
  --intraday-ratio 0.4 \
  --avg-quantity 35

# Generate diversified portfolio
uv run python generate_demo_cli.py \
  --stocks RELIANCE,TCS,HDFC,INFY,ICICIBANK \
  --days 30 \
  --output data/demo/my_portfolio_demo.csv
```

**CLI Options:**
- `--stocks`: Comma-separated stock names (see available stocks below)
- `--days`: Number of days back to generate data (default: 30)
- `--win-rate`: Win rate percentage 0.0-1.0 (default: 0.55)
- `--intraday-ratio`: Ratio of intraday vs swing trades (default: 0.6)
- `--avg-quantity`: Average shares per trade (default: 30)
- `--output`: Output CSV filename

**Available Stocks:** RELIANCE, TCS, INFY, HDFC, ICICIBANK, WIPRO, TECHM, HCLTECH, AXISBANK, SBIN

### Original Sample Data
A sample CSV is also provided at `data/sample/tradebook-SIL558-EQ.csv` for testing.

## Data Sources

The app uses multiple data sources with intelligent fallback:

### Primary Sources (Always Available)
1. **Yahoo Finance** - Most reliable, covers NSE/BSE stocks
2. **Google Finance** - Secondary fallback for some stocks

### API-Based Sources (Optional)
3. **Alpha Vantage** - Requires free API key, used as last resort
4. **NSE API** - Under development
5. **Investing.com** - Under development

### Fallback Strategy
```
Yahoo Finance → Google Finance → NSE API → Investing.com → Alpha Vantage
     ↓              ↓              ↓           ↓              ↓
   Primary      Secondary      Tertiary   Quaternary    Last Resort
  (100% up)    (20% success)  (Dev only)  (Dev only)   (Rate limited)
```

## Testing

```bash
# Run all tests
uv run test_all.py

# Test data sources specifically
uv run test_data_sources.py

# Test with Alpha Vantage API key
ALPHA_VANTAGE_API_KEY=your_key uv run test_alpha_vantage.py
```

## Project Structure

```
trade-analyzer/
├── app.py                     # Main Streamlit application
├── src/
│   ├── core/
│   │   ├── trade_parser.py    # Parse Zerodha CSV files
│   │   └── trade_matcher.py   # Match buy/sell trades
│   ├── data/
│   │   ├── price_fetcher.py   # Enhanced price fetcher with multi-source
│   │   └── multi_source_fetcher.py # Multiple data source implementation
│   └── insights/
│       └── insight_generator.py # Generate trading insights
├── tests/
└── data/sample/              # Sample data for testing
```

## Key Insights Generated

### Traditional Analysis
- **Exit Timing**: Analyze if you're exiting too early or holding losers too long
- **Entry Timing**: Identify best times of day/week for trading
- **Stock Selection**: Find consistently profitable stocks
- **Risk Management**: Detect risk-reward imbalances
- **Behavioral Patterns**: Identify overtrading and emotional biases

### Real Market Data Insights
- **Actual Missed Profits**: "You missed ₹50,000 by exiting TITAN too early"
- **Trailing Stop Benefits**: "A 2% trailing stop would have earned ₹25,000 more"
- **Volatility Warnings**: "Price swung 15% during your trade - consider smaller positions"
- **Technical Signal Analysis**: "RSI was overbought at 75 when you bought"

## Dependencies

- pandas: Data manipulation
- streamlit: Web interface
- plotly: Interactive charts
- yfinance: Primary market data
- requests: API calls for additional sources
- pandas-ta: Technical indicators

## Reliability & Uptime

- **Yahoo Finance**: 99%+ uptime, primary source
- **Multi-source fallback**: Ensures data availability even if primary source fails
- **Rate limiting**: Prevents API abuse and maintains service availability
- **Caching**: Reduces redundant API calls and improves performance

## License

MIT