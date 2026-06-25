# prompts/templates.py

def build_analyze_prompt(pair: str, price_data: dict, news_headlines: list, indicators: dict = None) -> str:
    current_price = price_data.get('current_price') or 0
    change_24h = price_data.get('price_change_24h') or 0
    change_7d = price_data.get('price_change_7d') or 0
    high_24h = price_data.get('high_24h') or 0
    low_24h = price_data.get('low_24h') or 0
    total_volume = price_data.get('total_volume') or 0
    market_cap = price_data.get('market_cap') or 0

    headlines_str = "\n".join(f"- {h}" for h in news_headlines[:5])

    # Tentukan format contoh angka berdasarkan harga asli
    if current_price >= 10000:
        price_example = f"{int(current_price * 0.999)}"
    elif current_price >= 100:
        price_example = f"{current_price * 0.999:.2f}"
    elif current_price >= 1:
        price_example = f"{current_price * 0.999:.4f}"
    elif current_price >= 0.0001:
        price_example = f"{current_price * 0.999:.6f}"
    else:
        price_example = f"{current_price * 0.999:.8f}"

    # Section indikator teknikal (RSI, EMA, posisi harga)
    indicators_section = ""
    if indicators:
        rsi_signal = indicators.get('rsi_signal', '-')
        ema_signal = indicators.get('ema_signal', '-')
        price_pos = indicators.get('price_position_pct')
        pos_str = f"{price_pos}% dari Low ke High 24h" if price_pos is not None else '-'

        indicators_section = f"""
INDIKATOR TEKNIKAL:
- RSI (14)  : {rsi_signal}
- EMA Signal: {ema_signal}
- Posisi    : {pos_str} (0% = di Low, 100% = di High)
"""

    return f"""Analisa pair berikut untuk FUTURES TRADING dan kembalikan
HANYA JSON, tanpa teks lain, tanpa markdown backticks.

PAIR: {pair}
HARGA SEKARANG: {current_price} USD

DATA TEKNIKAL (dari CoinGecko):
- Harga sekarang: {current_price} USD
- Change 24h: {change_24h}%
- Change 7d: {change_7d}%
- High 24h: {high_24h} USD
- Low 24h: {low_24h} USD
- Volume 24h: ${total_volume:,.0f}
- Market Cap: ${market_cap:,.0f}
{indicators_section}
BERITA & SENTIMEN (5 headline terkini):
{headlines_str}

INSTRUKSI WAJIB UNTUK entry_price:
- entry_price HARUS dalam range {current_price * 0.95:.8f} sampai {current_price * 1.05:.8f}
- Gunakan skala desimal yang SAMA dengan harga asli ({current_price})
- Jangan kalikan atau bagi dengan 10, 100, atau 1000

CATATAN: Kamu TIDAK PERLU menghitung target_price dan stop_loss.
Sistem akan menghitungnya otomatis. Cukup isi null untuk kedua
field tersebut di JSON.

JSON schema (gunakan angka sesuai skala harga {current_price}):
{{
  "pair": "{pair}",
  "verdict": "SETUP_VALID atau NO_SETUP",
  "technical_bias": "Bullish atau Bearish atau Sideways",
  "sentiment": "Positif atau Negatif atau Neutral",
  "liquidity": "Tinggi atau Cukup atau Rendah",
  "verdict_reason": "alasan singkat 1-2 kalimat",
  "side": "LONG atau SHORT (null jika NO_SETUP)",
  "entry_price": {price_example},
  "target_price": null,
  "stop_loss": null,
  "summary": "ringkasan analisa (null jika NO_SETUP)",
  "risk_notes": "catatan risiko (null jika NO_SETUP)"
}}
"""