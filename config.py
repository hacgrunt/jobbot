"""
JobBot Configuration
All keywords, company lists, filter rules, and settings.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ─── API Keys & Credentials ────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS", "")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL", "harry.cammer@gmail.com")

# ─── Title Keywords (what the role is called) ───────────────────────
TITLE_KEYWORDS = [
    "product marketing",
    "pmm",
    "growth marketing",
    "marketing manager",
    "marketing lead",
    "head of marketing",
    "brand marketing",
    "content marketing",
    "ecosystem marketing",
    "protocol marketing",
    "director of marketing",
    "director, marketing",
    "vp marketing",
    "vp of marketing",
    "vp, marketing",
    "vice president marketing",
    "gtm",
    "go-to-market",
    "go to market",
    "cmo",
    "chief marketing officer",
    "marketing director",
    "senior marketing",
    "staff marketing",
    "principal marketing",
    "communications manager",
    "communications lead",
    "head of communications",
    "developer relations",
    "devrel",
    "community marketing",
]

# ─── Industry Keywords (what makes it crypto/web3/AI) ───────────────
INDUSTRY_KEYWORDS = [
    "crypto",
    "cryptocurrency",
    "blockchain",
    "web3",
    "defi",
    "decentralized finance",
    "digital assets",
    "digital currency",
    "nft",
    "dao",
    "stablecoin",
    "tokenomics",
    "token",
    "protocol",
    "layer 1",
    "layer 2",
    "l1",
    "l2",
    "ethereum",
    "solana",
    "bitcoin",
    "fintech",
    "onchain",
    "on-chain",
    "smart contract",
    "dapp",
    "dex",
    "defi",
    "cefi",
    "wallet",
    "custody",
    "artificial intelligence",
    "ai ",
    "llm",
    "machine learning",
    "generative ai",
]

# ─── Location Filters ───────────────────────────────────────────────
ACCEPTED_LOCATIONS = [
    "remote",
    "anywhere",
    "worldwide",
    "global",
    "distributed",
    "work from home",
    "wfh",
    "new york",
    "nyc",
    "ny",
    "manhattan",
    "brooklyn",
    "united states",
    "usa",
    "us",
]

# ─── Exclusion Filters ──────────────────────────────────────────────
EXCLUDED_LEVELS = [
    "junior",
    "jr.",
    "jr ",
    "entry level",
    "entry-level",
    "associate",
    "intern ",
    "internship",
    "graduate",
    "new grad",
]

EXCLUDED_TYPES = [
    "contract",
    "freelance",
    "part-time",
    "part time",
    "temporary",
    "contractor",
]

# Staffing agencies and recruiters - these are never direct-hire quality roles
EXCLUDED_COMPANIES = [
    "creative circle",
    "robert half",
    "robert half international",
    "kforce",
    "teksystems",
    "tek systems",
    "hays",
    "randstad",
    "adecco",
    "manpower",
    "manpowergroup",
    "kelly services",
    "insight global",
    "aston carter",
    "beacon hill",
    "staffing",
    "recruiting agency",
    "talent solutions",
    "hired",
    "toptal",
    "aquent",
    "onward search",
    "24 seven",
    "mondo",
    "vitamin t",
    "the creative group",
    "cella",
    "yoh",
    "allegis",
    "spherion",
]

# Minimum salary threshold (lenient since roles negotiate up)
MIN_SALARY = 140_000

# Only include jobs posted within this many hours
MAX_AGE_HOURS = 48

# ─── Blue-Chip Companies ────────────────────────────────────────────
# The "gold standard" list - established, PMF, not going anywhere.
# Used for: (1) AI scoring boost, (2) "New at Top Companies" email section

TOP_COMPANIES = [
    # --- Exchanges ---
    "Coinbase",
    "Kraken",
    "Gemini",
    "Binance",
    "OKX",
    "Crypto.com",
    "Bybit",
    "Bitstamp",
    "Bitfinex",
    # --- DEX / DeFi Protocols ---
    "Uniswap",
    "Uniswap Labs",
    "Hyperliquid",
    "Aave",
    "Aave Labs",
    "Avara",
    "dYdX",
    "MakerDAO",
    "Sky",
    "Lido",
    "Curve",
    "Jupiter",
    "Pendle",
    "Compound",
    "Synthetix",
    "Yearn",
    "1inch",
    "SushiSwap",
    "Balancer",
    "Raydium",
    # --- L1 / L2 Protocols & Labs ---
    "Solana Labs",
    "Solana Foundation",
    "Solana",
    "Ava Labs",
    "Avalanche",
    "Polygon",
    "Polygon Labs",
    "Offchain Labs",
    "Arbitrum",
    "Arbitrum Foundation",
    "OP Labs",
    "Optimism",
    "Optimism Foundation",
    "Consensys",
    "ConsenSys",
    "Ripple",
    "Mysten Labs",
    "Sui",
    "StarkWare",
    "Starknet",
    "NEAR",
    "NEAR Foundation",
    "Aptos",
    "Aptos Labs",
    "Base",
    "Sei Labs",
    "Sei",
    "Monad",
    "Monad Labs",
    "Celestia",
    "Celestia Labs",
    "EigenLayer",
    "Eigen Labs",
    "Scroll",
    "zkSync",
    "Matter Labs",
    # --- Stablecoins ---
    "Circle",
    "Tether",
    "Paxos",
    # --- Custody / Institutional Infrastructure ---
    "Anchorage Digital",
    "Anchorage",
    "Fireblocks",
    "BitGo",
    "Copper",
    "Fidelity Digital Assets",
    "Galaxy Digital",
    "Galaxy",
    # --- Developer Infrastructure ---
    "Alchemy",
    "QuickNode",
    "Chainlink",
    "Chainlink Labs",
    "ENS",
    "ENS Labs",
    "The Graph",
    "Blockdaemon",
    "Figment",
    "Infura",
    "Moralis",
    "Helius",
    "Tenderly",
    # --- Security / Analytics / Compliance ---
    "Chainalysis",
    "TRM Labs",
    "Elliptic",
    "Nansen",
    "Dune",
    "Dune Analytics",
    "Gauntlet",
    "OpenZeppelin",
    # --- Wallets / Consumer ---
    "Phantom",
    "Ledger",
    "MetaMask",
    "OpenSea",
    "Blur",
    "Magic Eden",
    "Rainbow",
    "Exodus",
    "Trezor",
    # --- Data / Research ---
    "Messari",
    "CoinGecko",
    "The Block",
    "Kaiko",
    "Coin Metrics",
    "Artemis",
    # --- Media ---
    "Blockworks",
    "CoinDesk",
    "Decrypt",
    "CoinTelegraph",
    # --- VC / Investment ---
    "a16z crypto",
    "a16z",
    "Andreessen Horowitz",
    "Paradigm",
    "Pantera",
    "Pantera Capital",
    "Polychain",
    "Polychain Capital",
    "Dragonfly",
    "Multicoin Capital",
    "Multicoin",
    "Variant",
    "Variant Fund",
    "Electric Capital",
    "Framework Ventures",
    "Placeholder",
    "Blockchain Capital",
    "Digital Currency Group",
    "DCG",
    "Grayscale",
    # --- Other Established Players ---
    "Animoca Brands",
    "Dapper Labs",
    "Yuga Labs",
    "Immutable",
    "21Shares",
    "21.co",
    "Bitwise",
    "VanEck",
    "Hashnote",
    "Securitize",
    "Anchorage Digital",
    "Marathon Digital",
    "MARA",
    "Core Scientific",
    "Riot Platforms",
    "Robinhood Crypto",
    "Robinhood",
    "PayPal Crypto",
    "Block",
    "Stripe Crypto",
]

# Normalized set for fast lookup (lowercase)
TOP_COMPANIES_SET = {c.lower() for c in TOP_COMPANIES}

# ─── ATS Board Configurations ──────────────────────────────────────
# Greenhouse: boards-api.greenhouse.io/v1/boards/{slug}/jobs
GREENHOUSE_BOARDS = {
    "Coinbase": "coinbase",
    "Uniswap Labs": "uniswaplabs",
    "Fireblocks": "fireblocks",
    "BitGo": "bitgo",
    "Gemini": "gemini",
    "Ava Labs": "avalabs",
    "Alchemy": "alchemy",
    "Circle": "circle",
    "Ripple": "ripple",
    "OKX": "okx",
    "TRM Labs": "trmlabs",
    "dYdX": "dydx",
    "Copper": "copper",
    "Galaxy Digital": "galaxydigitalservices",
    "Solana Labs": "solanalabs",
    "Consensys": "consensys",
    "Figment": "figment",
    "Aptos Labs": "aptoslabs",
    "OpenZeppelin": "openzeppelin",
    "Paxos": "paxos",
    "Dapper Labs": "dapperlabs",
    "Immutable": "immutable",
    "Yuga Labs": "yugalabs",
}

# Lever: api.lever.co/v0/postings/{slug}
LEVER_BOARDS = {
    "Anchorage Digital": "anchorage",
    "Aave Labs": "aavelabs",
    "Ledger": "ledger",
    "Offchain Labs": "offchainlabs",
    "Crypto.com": "crypto",
    "Chainlink Labs": "chainlinklabs",
    "Protocol Labs": "protocol",
    "Bitwise": "bitwiseinvestments",
    "Securitize": "securitize",
    "Dune Analytics": "daboralabs",
}

# Ashby: api.ashby.io/posting-api/job-board/{slug}
ASHBY_BOARDS = {
    "Kraken": "Kraken",
    "Chainalysis": "Chainalysis",
    "Phantom": "Phantom",
    "Polygon Labs": "Polygon%20Labs",
    "Solana Foundation": "Solana%20Foundation",
    "Optimism": "Optimism",
    "OP Labs": "OP%20Labs",
    "Mysten Labs": "MystenLabs",
    "QuickNode": "QuickNode",
    "Blockworks": "Blockworks",
    "ENS Labs": "ENS%20Labs",
    "OpenSea": "OpenSea",
    "Hyperliquid": "Hyperliquid",
    "Monad": "Monad",
    "EigenLayer": "EigenLabs",
    "Scroll": "Scroll",
    "Matter Labs": "MatterLabs",
}

# ─── JobSpy Search Queries ──────────────────────────────────────────
# Each query is a (search_term, site_name_filter) pair.
# We run multiple queries to maximize coverage.
JOBSPY_QUERIES = [
    "product marketing crypto",
    "product marketing blockchain",
    "product marketing web3",
    "product marketing digital assets",
    "product marketing defi",
    "marketing manager crypto",
    "marketing manager blockchain",
    "marketing manager web3",
    "growth marketing crypto",
    "growth marketing web3",
    "head of marketing crypto",
    "head of marketing web3",
    "PMM crypto",
    "PMM blockchain",
    "PMM web3",
    "product marketing AI",
    "product marketing artificial intelligence",
    "marketing lead crypto",
    "marketing lead web3",
    "marketing director crypto",
    "marketing director blockchain",
]

# ─── Email Settings ─────────────────────────────────────────────────
EMAIL_SUBJECT_PREFIX = "JobBot Daily"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# ─── Scoring ────────────────────────────────────────────────────────
SCORING_MODEL = "claude-sonnet-4-5-20250929"
MIN_RELEVANCE_SCORE = 6
SCORING_BATCH_SIZE = 20  # Jobs per API call

# ─── Database ───────────────────────────────────────────────────────
DB_PATH = os.path.join(os.path.dirname(__file__), "jobbot.db")
