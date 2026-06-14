# prompts/templates.py


def build_analysis_prompt(
    pair: str,
    timeframe: str,
    market_condition: str,
    current_price_data: dict,
) -> str:
    """
    Susun prompt lengkap untuk analisis trading.
    Gabungkan data real-time dengan input user.
    """
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

Based on the above data and user context, please provide a structured analysis:

1. **Entry Zone** — Suggested buy zone or entry area
2. **Exit / Take Profit** — Suggested target(s)
3. **Stop Loss** — Suggested stop loss level
4. **Risk Assessment** — Potential risks and risk/reward ratio
5. **Key Notes** — Any additional observations or warnings

Remember: Never guarantee profits. Always emphasize risk management.
"""
    return prompt