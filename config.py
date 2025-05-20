from datetime import datetime

OUTPUT_DIR = "FinancialNewsData"
BASE_URL = 'https://www.theguardian.com/business/stock-markets'
BUSINESS_URL = 'https://www.theguardian.com/uk/business'
START_DATE = datetime(2023, 1, 1)
END_DATE = datetime(2025, 5, 15)
SENTIMENT_THRESHOLD = 0.4
FINANCIAL_KEYWORDS = [
    'stock', 'stocks', 'market', 'markets', 'shares', 'equity', 'equities', 'securities',
    'trading', 'trader', 'traders', 'investor', 'investors', 'investment', 'investments',
    'portfolio', 'volatility', 'hedge', 'hedge fund', 'etf', 'etfs', 'index', 'indices',

    'ftse', 'nasdaq', 'dow jones', 'sp 500', 's&p', 's&p 500', 'russell 2000', 'vix',

    'bond', 'bonds', 'treasury', 'treasuries', 'corporate bond', 'muni bond', 'junk bond',
    'high yield', 'sovereign debt', 'bond market', 'bond yield', 'bond prices', 'duration',
    'fixed income', 'coupon', 'bond issuance', 'bond auction',

    'interest rate', 'interest rates', 'rate hike', 'rate cut', 'rate decision',
    'central bank', 'federal reserve', 'fed', 'ecb', 'boe', 'boj', 'tightening', 'easing',
    'quantitative easing', 'qe', 'liquidity', 'repo', 'reverse repo', 'fed funds rate',

    'inflation', 'deflation', 'stagflation', 'disinflation', 'cpi', 'ppi', 'core cpi',
    'employment', 'unemployment', 'jobless claims', 'nonfarm payrolls', 'gdp', 'growth',
    'recession', 'depression', 'economic', 'economy', 'business cycle', 'housing starts',
    'consumer confidence', 'industrial production', 'retail sales', 'manufacturing index',
    'ism', 'leading indicators', 'productivity', 'import', 'export', 'trade deficit',
    'current account', 'balance of payments',

    'bank', 'banks', 'banking', 'credit', 'loan', 'loans', 'debt', 'mortgage', 'mortgages',
    'liquidity', 'capital', 'default', 'risk', 'rating', 'credit rating', 'delinquency',
    'bankruptcy', 'bailout', 'write-off', 'insolvency',

    'currency', 'currencies', 'foreign exchange', 'fx', 'exchange rate', 'exchange rates',
    'usd', 'eur', 'jpy', 'gbp', 'cny', 'forex', 'devaluation', 'appreciation',

    'earnings', 'eps', 'revenue', 'sales', 'profit', 'loss', 'dividend', 'dividends',
    'guidance', 'quarter', 'quarterly', 'fiscal', 'annual', 'forecast', 'outlook',

    'commodity', 'commodities', 'oil', 'crude', 'brent', 'wti', 'gas', 'natural gas',
    'gold', 'silver', 'copper', 'metal', 'metals', 'energy', 'grain', 'agriculture',

    'futures', 'options', 'option', 'derivative', 'derivatives', 'swap', 'cds', 'puts', 'calls',

    'fund', 'funds', 'mutual fund', 'institutional investor', 'pension', 'sovereign fund',

    'regulation', 'regulatory', 'sec', 'ipo', 'listing', 'bankruptcy', 'bailout',
    'merger', 'acquisition', 'm&a', 'buyback', 'spin-off', 'spinoff', 'spac',

    'bull', 'bullish', 'bear', 'bearish', 'rally', 'crash', 'dip', 'correction',
    'surge', 'plunge', 'sell-off', 'breakout', 'momentum', 'overbought', 'oversold'
]
CATEGORY_KEYWORDS = {
    "Recession": [
        "recession", "slowdown", "contraction", "economic downturn", "gdp shrink", "negative growth",
        "unemployment", "jobless", "layoffs", "reduced output"
    ],
    "Inflation": [
        "inflation", "cpi", "ppi", "consumer price index", "producer price index",
        "price rise", "cost of living", "stagflation", "deflation", "hyperinflation"
    ],
    "Interest Rates": [
        "interest rate", "fed", "federal reserve", "rate hike", "rate cut", "benchmark rate",
        "central bank", "tightening", "loosening", "monetary policy", "fomc"
    ],
    "Stock Market": [
        "nasdaq", "s&p 500", "dow jones", "equity", "stock", "market crash", "bull market",
        "bear market", "ipo", "index", "share price", "volatility", "earnings", "dividends"
    ],
    "Tariffs & Trade": [
        "tariff", "trade war", "import duty", "export ban", "us-china", "trade agreement",
        "wto", "sanction", "import", "export", "subsidy", "quota"
    ],
    "Banking & Credit": [
        "bank", "bank failure", "credit", "loan", "mortgage", "repo", "bankruptcy",
        "liquidity", "deposit", "default", "insolvency", "run on the bank", "interest spread"
    ],
    "Corporate": [
        "merger", "acquisition", "m&a", "ipo", "layoffs", "restructuring", "divestment",
        "earnings report", "profit warning", "revenue", "buyback", "shareholder"
    ],
    "Commodities": [
        "oil", "gold", "crude", "commodity", "energy", "supply chain", "wheat", "natural gas",
        "barrel", "metals", "futures", "mining", "opec"
    ],
    "Technology & Innovation": [
        "ai", "technology", "startup", "machine learning", "cloud", "big data", "quantum",
        "blockchain", "cybersecurity", "fintech", "software", "ipo"
    ],
    "Crypto & Digital Assets": [
        "bitcoin", "crypto", "ethereum", "token", "stablecoin", "nft", "blockchain", "web3",
        "defi", "coinbase", "binance", "crypto regulation", "digital currency"
    ],
    "Housing & Real Estate": [
        "housing", "real estate", "mortgage", "home sales", "property", "construction",
        "housing bubble", "housing prices", "rent", "foreclosure", "building permits"
    ],
    "Employment & Labor": [
        "employment", "unemployment", "job growth", "labor market", "jobless claims",
        "hiring", "wage", "labor shortage", "strike", "union", "layoff"
    ],
    "Geopolitical Events": [
        "war", "conflict", "invasion", "sanctions", "geopolitics", "russia", "china", "ukraine",
        "diplomacy", "embargo", "military", "terrorism", "nato", "un"
    ],
    "Government & Regulation": [
        "regulation", "sec", "congress", "policy", "law", "oversight", "compliance",
        "legislation", "probe", "fines", "antitrust", "tax"
    ],
    "Climate & ESG": [
        "esg", "climate", "sustainability", "carbon", "green", "renewable", "environment",
        "emissions", "solar", "net zero", "energy transition", "climate risk"
    ],
    "Consumer & Retail": [
        "consumer", "spending", "retail", "shopping", "ecommerce", "black friday", "inflation",
        "sales", "discount", "amazon", "supply chain", "demand"
    ],
    "Global Markets": [
        "global", "emerging market", "europe", "asia", "china", "japan", "india",
        "currency", "exchange rate", "devaluation", "yen", "euro", "dollar", "forex"
    ],
    "Financial Crisis & Major Events": [
        "covid", "pandemic", "natural disaster", "earthquake", "hurricane", "flood",
        "tsunami", "financial crisis", "2008", "lehman brothers", "dot-com bubble", "black swan",
        "bank run", "great depression", "systemic risk", "shock event", "crisis", "outbreak"
    ],
}
