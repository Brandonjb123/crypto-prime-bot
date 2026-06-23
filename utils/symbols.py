# utils/symbols.py
SYMBOL_TO_COINGECKO_ID = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "BNB": "binancecoin",
    "XRP": "ripple",
    "ADA": "cardano",
    "SOL": "solana",
    "DOGE": "dogecoin",
    "DOT": "polkadot",
    "MATIC": "polygon-ecosystem-token",
    "POL": "polygon-ecosystem-token",
    "TRX": "tron",
    "AVAX": "avalanche-2",
    "LINK": "chainlink",
    "UNI": "uniswap",
    "ATOM": "cosmos",
    "LTC": "litecoin",
    "FIL": "filecoin",
    "APT": "aptos",
    "ARB": "arbitrum",
    "OP": "optimism",
    "NEAR": "near",
    "INJ": "injective-protocol",
    "SUI": "sui",
    "PEPE": "pepe",
    "SHIB": "shiba-inu",
}

def get_coin_id(pair: str):
    """
    Ambil coin_id dari pair, terlepas dari formatnya
    ("BTC" atau "BTC/USDT" sama-sama bisa diproses).
    Ini SATU-SATUNYA titik lookup coin_id di seluruh codebase.
    """
    # Bersihkan format: ambil bagian sebelum "/" kalau ada
    symbol = pair.split("/")[0].upper().strip()
    return SYMBOL_TO_COINGECKO_ID.get(symbol)