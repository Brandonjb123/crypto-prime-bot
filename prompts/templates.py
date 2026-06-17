# prompts/templates.py


def build_analyze_prompt(pair: str, price_data: dict, news_headlines: list) -> str:
    headlines_str = "\n".join(f"- {h}" for h in news_headlines[:5])
    return f"""Analisa pair berikut dan kembalikan HANYA JSON, tanpa teks lain, tanpa markdown backticks, langsung JSON object saja.

PAIR: {pair}

DATA TEKNIKAL (dari CoinGecko):
- Harga sekarang: {price_data['current_price']} USD
- Change 24h: {price_data['price_change_24h']}%
- Change 7d: {price_data['price_change_7d']}%
- High 24h: ${price_data['high_24h']}
- Low 24h: ${price_data['low_24h']}
- Volume 24h: ${price_data['total_volume']:,.0f}
- Market Cap: ${price_data['market_cap']:,.0f}

BERITA & SENTIMEN (5 headline terkini dari Google News):
{headlines_str}

Berikan analisa multi-factor dan verdict LAYAK atau TIDAK LAYAK.
Return JSON sesuai schema. Kalau TIDAK LAYAK, field side/entry_price/target_price/stop_loss/summary/risk_notes diisi null.

PENTING: Untuk pair dengan harga < $1 (seperti PEPE, SHIB), pastikan entry_price, target_price, dan stop_loss menggunakan format desimal yang sesuai dengan harga aslinya (contoh: 0.00000300 bukan 3000000).

JSON schema yang harus kamu ikuti:
{{
  "pair": "{pair}",
  "verdict": "LAYAK",
  "technical_bias": "Bullish",
  "sentiment": "Positif",
  "liquidity": "Tinggi",
  "verdict_reason": "...",
  "side": "LONG",
  "entry_price": 67200,
  "target_price": 70000,
  "stop_loss": 65800,
  "summary": "...",
  "risk_notes": "..."
}}
"""