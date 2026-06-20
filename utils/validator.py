# utils/validator.py

RISK_PERCENT = 0.02   # 2% risk
REWARD_PERCENT = 0.04 # 4% reward → R:R = 1:2.0


def calculate_target_and_stop(entry_price: float, side: str) -> tuple:
    """
    Hitung target_price dan stop_loss secara matematis.
    R:R selalu tepat 1:2.0 (RISK_PERCENT vs REWARD_PERCENT).
    Return (target_price, stop_loss)
    """
    if side == "LONG":
        stop_loss = entry_price * (1 - RISK_PERCENT)
        target_price = entry_price * (1 + REWARD_PERCENT)
    elif side == "SHORT":
        stop_loss = entry_price * (1 + RISK_PERCENT)
        target_price = entry_price * (1 - REWARD_PERCENT)
    else:
        return None, None

    return round(target_price, 8), round(stop_loss, 8)


def inject_calculated_prices(data: dict) -> dict:
    """
    Setelah Groq return JSON, isi target_price dan stop_loss
    secara matematis berdasarkan entry_price dan side dari Groq.
    Panggil fungsi ini SEBELUM validate_signal_prices().
    """
    if data.get("verdict") != "SETUP_VALID":
        return data

    entry = data.get("entry_price")
    side = data.get("side")

    if not entry or side not in ("LONG", "SHORT"):
        data["verdict"] = "NO_SETUP"
        data["verdict_reason"] = "Entry price atau side tidak valid dari analisa."
        return data

    try:
        entry = float(entry)
    except (TypeError, ValueError):
        data["verdict"] = "NO_SETUP"
        data["verdict_reason"] = "Entry price tidak valid."
        return data

    target, stop = calculate_target_and_stop(entry, side)
    data["target_price"] = target
    data["stop_loss"] = stop

    return data


def validate_signal_prices(data: dict, current_price: float) -> bool:
    """
    Validasi entry_price dari Groq.
    target_price dan stop_loss sudah dihitung matematis (selalu valid),
    jadi validator hanya perlu cek entry_price masuk akal.
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
        current_price = float(current_price)
    except (TypeError, ValueError):
        return False

    # Validasi: entry tidak boleh menyimpang >50% dari current_price
    if current_price > 0:
        deviation = abs(entry - current_price) / current_price
        if deviation > 0.50:
            return False

    return True