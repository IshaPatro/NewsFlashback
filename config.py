OUTPUT_DIR = "FinancialNewsData"
BASE_URL = 'https://www.theguardian.com/business/stock-markets'
BUSINESS_URL = 'https://www.theguardian.com/uk/business'
START_DATE = datetime(2023, 1, 1)
END_DATE = datetime(2025, 5, 15)
SENTIMENT_THRESHOLD = 0.4
FINANCIAL_KEYWORDS = [
    # Markets & Instruments
    'stock', 'stocks', 'market', 'markets', 'shares', 'equity', 'equities', 'securities',
    'trading', 'trader', 'traders', 'investor', 'investors', 'investment', 'investments',
    'portfolio', 'volatility', 'hedge', 'hedge fund', 'etf', 'etfs', 'index', 'indices',

    # Major Indexes
    'ftse', 'nasdaq', 'dow jones', 'sp 500', 's&p', 's&p 500', 'russell 2000', 'vix',

    # Bonds & Fixed Income
    'bond', 'bonds', 'treasury', 'treasuries', 'corporate bond', 'muni bond', 'junk bond',
    'high yield', 'sovereign debt', 'bond market', 'bond yield', 'bond prices', 'duration',
    'fixed income', 'coupon', 'bond issuance', 'bond auction',

    # Interest Rates & Monetary Policy
    'interest rate', 'interest rates', 'rate hike', 'rate cut', 'rate decision',
    'central bank', 'federal reserve', 'fed', 'ecb', 'boe', 'boj', 'tightening', 'easing',
    'quantitative easing', 'qe', 'liquidity', 'repo', 'reverse repo', 'fed funds rate',

    # Economic Indicators
    'inflation', 'deflation', 'stagflation', 'disinflation', 'cpi', 'ppi', 'core cpi',
    'employment', 'unemployment', 'jobless claims', 'nonfarm payrolls', 'gdp', 'growth',
    'recession', 'depression', 'economic', 'economy', 'business cycle', 'housing starts',
    'consumer confidence', 'industrial production', 'retail sales', 'manufacturing index',
    'ism', 'leading indicators', 'productivity', 'import', 'export', 'trade deficit',
    'current account', 'balance of payments',

    # Banking & Credit
    'bank', 'banks', 'banking', 'credit', 'loan', 'loans', 'debt', 'mortgage', 'mortgages',
    'liquidity', 'capital', 'default', 'risk', 'rating', 'credit rating', 'delinquency',
    'bankruptcy', 'bailout', 'write-off', 'insolvency',

    # Currency & FX
    'currency', 'currencies', 'foreign exchange', 'fx', 'exchange rate', 'exchange rates',
    'usd', 'eur', 'jpy', 'gbp', 'cny', 'forex', 'devaluation', 'appreciation',

    # Corporate Performance
    'earnings', 'eps', 'revenue', 'sales', 'profit', 'loss', 'dividend', 'dividends',
    'guidance', 'quarter', 'quarterly', 'fiscal', 'annual', 'forecast', 'outlook',

    # Commodities
    'commodity', 'commodities', 'oil', 'crude', 'brent', 'wti', 'gas', 'natural gas',
    'gold', 'silver', 'copper', 'metal', 'metals', 'energy', 'grain', 'agriculture',

    # Derivatives
    'futures', 'options', 'option', 'derivative', 'derivatives', 'swap', 'cds', 'puts', 'calls',

    # Funds & Institutions
    'fund', 'funds', 'mutual fund', 'institutional investor', 'pension', 'sovereign fund',

    # Regulatory & Corporate Events
    'regulation', 'regulatory', 'sec', 'ipo', 'listing', 'bankruptcy', 'bailout',
    'merger', 'acquisition', 'm&a', 'buyback', 'spin-off', 'spinoff', 'spac',

    # Market Sentiment & Movement
    'bull', 'bullish', 'bear', 'bearish', 'rally', 'crash', 'dip', 'correction',
    'surge', 'plunge', 'sell-off', 'breakout', 'momentum', 'overbought', 'oversold'
]