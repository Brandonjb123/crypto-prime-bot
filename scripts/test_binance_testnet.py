"""Binance Futures TESTNET Verification Script.

Script ini TIDAK mengubah PAPER mode.
Script ini HANYA berjalan jika EXCHANGE_ENV=TESTNET.
Tidak mengeksekusi production endpoint.
Tidak menampilkan API key/secret.
"""

import asyncio
import os
import sys

from dotenv import load_dotenv

from src.exchange.adapters.binance.client import BinanceClient

# Load .env hanya jika ada
load_dotenv()


def safe_print(label: str, value: str) -> None:
    """Print tanpa menampilkan credential."""
    print(f"{label}: {value}")


def require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        print(f"FAIL: Environment variable {name} tidak boleh kosong.")
        sys.exit(1)
    return value


async def run_verification() -> None:
    # Safety gate
    exchange_env = os.getenv("EXCHANGE_ENV", "").upper()
    if exchange_env != "TESTNET":
        print(f"FAIL: EXCHANGE_ENV harus TESTNET, ditemukan: {exchange_env or 'KOSONG'}")
        sys.exit(1)

    api_key = require_env("EXCHANGE_API_KEY")
    api_secret = require_env("EXCHANGE_API_SECRET")

    # Mask key untuk log
    masked_key = f"{api_key[:6]}...{api_key[-4:]}" if len(api_key) > 10 else "***"
    print(f"Using TESTNET. API key: {masked_key}")
    print("=" * 60)

    client = BinanceClient(api_key=api_key, api_secret=api_secret, testnet=True)

    # 1. Authentication + get_balance
    print("STEP 1: get_balance()")
    try:
        balance = await client.get_balance()
        print("PASS: get_balance")
        # Hanya tampilkan beberapa asset
        for asset in ("USDT", "BTC", "BNB"):
            if asset in balance:
                print(f"  {asset}: {balance[asset]}")
    except Exception as e:
        print(f"FAIL: get_balance | {type(e).__name__}: {e}")

    # 2. get_positions
    print("\nSTEP 2: get_positions()")
    try:
        positions = await client.get_positions()
        open_positions = [p for p in positions if float(p.get("positionAmt", 0)) != 0]
        print(f"PASS: get_positions (total={len(positions)}, open={len(open_positions)})")
    except Exception as e:
        print(f"FAIL: get_positions | {type(e).__name__}: {e}")

    # 3. get_open_orders
    print("\nSTEP 3: get_open_orders(BTCUSDT)")
    try:
        open_orders = await client.get_open_orders(symbol="BTCUSDT")
        print(f"PASS: get_open_orders (count={len(open_orders)})")
    except Exception as e:
        print(f"FAIL: get_open_orders | {type(e).__name__}: {e}")

    # 4. place_order (LIMIT, jauh di bawah market agar tidak terisi)
    print("\nSTEP 4: place_order (BTCUSDT BUY 0.001 LIMIT @10000)")
    order_result = None
    try:
        order_result = await client.place_order(
            symbol="BTCUSDT",
            side="BUY",
            quantity=0.001,
            price=10000.0,
            order_type="LIMIT",
            client_order_id="testnet_verify_12b",
        )
        print("PASS: place_order")
        print(f"  exchange_order_id: {order_result.get('orderId')}")
        print(f"  status: {order_result.get('status')}")
        print(f"  client_order_id: {order_result.get('clientOrderId')}")
    except Exception as e:
        print(f"FAIL: place_order | {type(e).__name__}: {e}")

    # 5. get_order
    print("\nSTEP 5: get_order()")
    if order_result and order_result.get("orderId"):
        order_id = order_result["orderId"]
        try:
            fetched = await client.get_order(order_id=str(order_id))
            print("PASS: get_order")
            print(f"  status: {fetched.get('status')}")
            print(f"  executedQty: {fetched.get('executedQty')}")
        except Exception as e:
            print(f"FAIL: get_order | {type(e).__name__}: {e}")
    else:
        print("SKIP: get_order (tidak ada order ID dari place_order)")

    # 6. cancel_order
    print("\nSTEP 6: cancel_order()")
    if order_result and order_result.get("orderId"):
        try:
            cancelled = await client.cancel_order(order_id=str(order_result["orderId"]))
            print("PASS: cancel_order")
            print(f"  status: {cancelled.get('status')}")
        except Exception as e:
            print(f"FAIL: cancel_order | {type(e).__name__}: {e}")
    else:
        print("SKIP: cancel_order (tidak ada order ID)")

    print("\nVerification script selesai.")


if __name__ == "__main__":
    asyncio.run(run_verification())