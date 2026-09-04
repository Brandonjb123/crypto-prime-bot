"""Prompt Builder — mengubah AnalysisResult menjadi prompt untuk AI."""


class PromptBuilder:
    def build(self, analysis) -> str:
        prompt = (
            "You are a professional crypto trading analyst. "
            "Based on the market analysis below, decide the action: BUY, SELL, or WAIT.\n\n"
            f"Trend: {analysis.trend}\n"
            f"Momentum: {analysis.momentum}\n"
            f"Volatility: {analysis.volatility}\n"
            f"Volume: {analysis.volume_strength}\n"
            f"Structure: {analysis.market_structure}\n\n"
            "Return ONLY valid JSON. No markdown, no explanation outside JSON.\n\n"
            "Format:\n"
            '{"decision": "BUY", "confidence": 87, "risk_level": "MEDIUM", '
            '"reasoning": ["reason1", "reason2"]}'
        )
        return prompt