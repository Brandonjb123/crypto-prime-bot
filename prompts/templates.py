def build_analysis_prompt(pair: str, timeframe: str, market_condition: str, current_price_data: dict) -> str:
    name = current_price_data.get("name", pair)
    symbol = current_price_data.get("symbol", pair)
    price = current_price_data.get("current_price", "N/A")
    change = current_price_data.get("price_change_percentage_24h", "N/A")
    volume = current_price_data.get("total_volume", "N/A")
    market_cap = current_price_data.get("market_cap", "N/A")

    prompt = f"""
📊 **TRADE SETUP ANALYSIS REQUEST**

**Pair:** {name} ({symbol})
**Timeframe:** {timeframe}
**Market Condition (user input):** {market_condition}

**Real-time Market Data (CoinGecko):**
- Current Price: ${price:,.2f} USD
- 24h Change: {change:.2f}%
- 24h Volume: ${volume:,.2f}
- Market Cap: ${market_cap:,.2f}

Based on the above data and user context, provide a structured analysis.

**IMPORTANT: You MUST respond in valid JSON format only. No markdown, no extra text outside the JSON.**

The JSON must have exactly these fields:
{{
  "pair": "{symbol}",
  "side": "long" or "short",
  "entry_price": number,
  "target_price": number,
  "stop_loss": number,
  "summary": "brief analysis in 1-2 sentences, in the same language as the user",
  "risk_notes": "risk management notes, including disclaimer"
}}

Rules:
- Never guarantee profits or give financial advice
- Always mention risk management in risk_notes
- entry_price, target_price, stop_loss must be realistic numbers based on current price
- side must be either "long" or "short" based on your analysis
- Respond in the same language as the user for summary and risk_notes (ID/EN)
"""
    return prompt