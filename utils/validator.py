# utils/validator.py

def validate_signal_prices(data: dict, current_price: float) -> bool:
    """
    Validasi entry/target/SL dari Groq LLM.
    Return True jika valid, False jika harus di-reject.

    Kriteria:
    1. entry_price tidak menyimpang >50% dari current_price
    2. R:R minimum 1:1.5
    3. Semua field ada dan bertipe angka
    """
    if data.get("verdict") != "SETUP_VALID":
        return True

    entry = data.get("entry_price")
    target = data.get("target_price")
    sl = data.get("stop_loss")

    if not all([entry, target, sl]):
        return False

    try:
        entry = float(entry)
        target = float(target)
        sl = float(sl)
        current_price = float(current_price)
    except (TypeError, ValueError):
        return False

    # Validasi 1: entry tidak boleh menyimpang >50% dari current_price
    if current_price > 0:
        deviation = abs(entry - current_price) / current_price
        if deviation > 0.50:
            return False

    # Validasi 2: R:R minimum 1.5
    side = data.get("side", "LONG")
    try:
        if side == "LONG":
            if entry <= sl:
                return False
            rr = (target - entry) / (entry - sl)
        else:  # SHORT
            if entry >= sl:
                return False
            rr = (entry - target) / (sl - entry)
    except ZeroDivisionError:
        return False

    if rr < 1.5:
        return False

    return True