# prompts/templates.py

def build_analyze_prompt(pair: str, price_data: dict, news_headlines: list) -> str:
    current_price = price_data['current_price']
    headlines_str = "\n".join(f"- {h}" for h in news_headlines[:5])

    # Tentukan format contoh angka berdasarkan harga asli
    if current_price >= 10000:
        price_example = f"{int(current_price * 0.999)}"
        target_example = f"{int(current_price * 1.04)}"
        sl_example = f"{int(current_price * 0.975)}"
    elif current_price >= 100:
        price_example = f"{current_price * 0.999:.2f}"
        target_example = f"{current_price * 1.04:.2f}"
        sl_example = f"{current_price * 0.975:.2f}"
    elif current_price >= 1:
        price_example = f"{current_price * 0.999:.4f}"
        target_example = f"{current_price * 1.04:.4f}"
        sl_example = f"{current_price * 0.975:.4f}"
    elif current_price >= 0.0001:
        price_example = f"{current_price * 0.999:.6f}"
        target_example = f"{current_price * 1.04:.6f}"
        sl_example = f"{current_price * 0.975:.6f}"
    else:
        price_example = f"{current_price * 0.999:.8f}"
        target_example = f"{current_price * 1.04:.8f}"
        sl_example = f"{current_price * 0.975:.8f}"

    return f"""Analisa pair berikut untuk FUTURES TRADING dan kembalikan
HANYA JSON, tanpa teks lain, tanpa markdown backticks.

PAIR: {pair}
HARGA SEKARANG: {current_price} USD

DATA TEKNIKAL (dari CoinGecko):
- Harga sekarang: {current_price} USD
- Change 24h: {price_data['price_change_24h']}%
- Change 7d: {price_data['price_change_7d']}%
- High 24h: {price_data['high_24h']} USD
- Low 24h: {price_data['low_24h']} USD
- Volume 24h: ${price_data['total_volume']:,.0f}
- Market Cap: ${price_data['market_cap']:,.0f}

BERITA & SENTIMEN (5 headline terkini):
{headlines_str}

INSTRUKSI WAJIB UNTUK ANGKA:
- Harga pair ini adalah {current_price} USD
- entry_price HARUS dalam range {current_price * 0.95:.8f} sampai {current_price * 1.05:.8f}
- Gunakan skala desimal yang SAMA dengan harga asli ({current_price})
- Jangan kalikan atau bagi dengan 10, 100, atau 1000
- R:R minimum 1:1.5, jika tidak tercapai beri verdict TIDAK LAYAK

JSON schema (gunakan angka sesuai skala harga {current_price}):
{{
  "pair": "{pair}",
  "verdict": "SETUP_VALID atau NO_SETUP",
  "technical_bias": "Bullish atau Bearish atau Sideways",
  "sentiment": "Positif atau Negatif atau Neutral",
  "liquidity": "Tinggi atau Cukup atau Rendah",
  "verdict_reason": "alasan singkat 1-2 kalimat",
  "side": "LONG atau SHORT (null jika TIDAK LAYAK)",
  "entry_price": {price_example},
  "target_price": {target_example},
  "stop_loss": {sl_example},
  "summary": "ringkasan analisa (null jika TIDAK LAYAK)",
  "risk_notes": "catatan risiko (null jika TIDAK LAYAK)"
}}
"""