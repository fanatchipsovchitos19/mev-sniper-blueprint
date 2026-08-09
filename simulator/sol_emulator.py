"""Арбитражный симулятор: Binance vs Solana DEX."""
import requests
from dataclasses import dataclass
from typing import List, Optional


BINANCE_API = "https://api.binance.com/api/v3/ticker/price"

TOKENS = [
    ("SOL", "SOLUSDT"),
    ("RAY", "RAYUSDT"),
    ("ORCA", "ORCAUSDT"),
    ("JTO", "JTOUSDT"),
    ("WIF", "WIFUSDT"),
    ("BONK", "BONKUSDT"),
    ("JUP", "JUPUSDT"),
    ("PYTH", "PYTHUSDT"),
    ("HNT", "HNTUSDT"),
    ("TNSR", "TNSRUSDT"),
    ("W", "WUSDT"),
    ("KMNO", "KMNOUSDT"),
    ("CLOUD", "CLOUDUSDT"),
    ("DRIFT", "DRIFTUSDT"),
    ("MEW", "MEWUSDT"),
    ("POPCAT", "POPCATUSDT"),
    ("RENDER", "RENDERUSDT"),
    ("PYUSD", "PYUSDUSDT"),
]

TRIANGLES = [
    # 2-step: SOL -> Token -> SOL
    ["SOL", "RAY", "SOL"],
    ["SOL", "ORCA", "SOL"],
    ["SOL", "JTO", "SOL"],
    ["SOL", "WIF", "SOL"],
    ["SOL", "BONK", "SOL"],
    ["SOL", "JUP", "SOL"],
    ["SOL", "PYTH", "SOL"],
    ["SOL", "HNT", "SOL"],
    ["SOL", "TNSR", "SOL"],
    ["SOL", "W", "SOL"],
    ["SOL", "KMNO", "SOL"],
    ["SOL", "CLOUD", "SOL"],
    ["SOL", "DRIFT", "SOL"],
    ["SOL", "MEW", "SOL"],
    ["SOL", "POPCAT", "SOL"],
    ["SOL", "RENDER", "SOL"],
    # 3-step: SOL -> Token1 -> Token2 -> SOL
    ["SOL", "RAY", "JTO", "SOL"],
    ["SOL", "JTO", "RAY", "SOL"],
    ["SOL", "RAY", "ORCA", "SOL"],
    ["SOL", "ORCA", "RAY", "SOL"],
    ["SOL", "WIF", "BONK", "SOL"],
    ["SOL", "BONK", "WIF", "SOL"],
    ["SOL", "JUP", "PYTH", "SOL"],
    ["SOL", "PYTH", "JUP", "SOL"],
    ["SOL", "JTO", "WIF", "SOL"],
    ["SOL", "WIF", "JTO", "SOL"],
    ["SOL", "HNT", "TNSR", "SOL"],
    ["SOL", "TNSR", "HNT", "SOL"],
    ["SOL", "KMNO", "CLOUD", "SOL"],
    ["SOL", "CLOUD", "KMNO", "SOL"],
    ["SOL", "DRIFT", "MEW", "SOL"],
    ["SOL", "MEW", "DRIFT", "SOL"],
    ["SOL", "POPCAT", "RENDER", "SOL"],
    ["SOL", "RENDER", "POPCAT", "SOL"],
    # 4-step: SOL -> Token1 -> Token2 -> Token3 -> SOL
    ["SOL", "RAY", "ORCA", "JTO", "SOL"],
    ["SOL", "JTO", "WIF", "BONK", "SOL"],
    ["SOL", "JUP", "PYTH", "RENDER", "SOL"],
    ["SOL", "HNT", "TNSR", "W", "SOL"],
    ["SOL", "DRIFT", "CLOUD", "KMNO", "SOL"],
    ["SOL", "POPCAT", "MEW", "WIF", "SOL"],
    ["SOL", "RAY", "JUP", "PYTH", "SOL"],
    ["SOL", "ORCA", "RENDER", "POPCAT", "SOL"],
]


@dataclass
class SimResult:
    found: bool
    path: List[str]
    amount_in_sol: float
    amount_out_sol: float
    profit_usd: float
    fees_usd: float
    net_usd: float
    verdict: str


class SolEmulator:
    def __init__(self, rpc_url: str = None):
        self.rpc_url = rpc_url

    def get_binance_prices(self) -> dict:
        try:
            resp = requests.get(BINANCE_API, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                return {item["symbol"]: float(item["price"]) for item in data}
        except Exception as e:
            print(f"  [!] Binance error: {e}")
        return {}

    def simulate_arbitrage(self, amount_in_sol: float = 1.0) -> SimResult:
        prices = self.get_binance_prices()

        if not prices:
            return SimResult(False, [], amount_in_sol, 0, 0, 0.75, -0.75, "Убыточно")

        sol_price = prices.get("SOLUSDT", 150.0)

        token_prices = {}
        for name, symbol in TOKENS:
            if symbol in prices:
                token_prices[name] = prices[symbol]

        best = SimResult(False, [], amount_in_sol, 0, 0, 0.75, -0.75, "Убыточно")

        for path in TRIANGLES:
            amount = amount_in_sol
            current = "SOL"
            success = True

            for next_token in path[1:]:
                if current == "SOL":
                    token_price = token_prices.get(next_token, 0)
                    if token_price == 0:
                        success = False
                        break
                    amount = amount * sol_price / token_price * 0.997
                    current = next_token
                elif next_token == "SOL":
                    token_price = token_prices.get(current, 0)
                    if token_price == 0:
                        success = False
                        break
                    amount = amount * token_price / sol_price * 0.997
                    current = "SOL"
                else:
                    price1 = token_prices.get(current, 0)
                    price2 = token_prices.get(next_token, 0)
                    if price1 == 0 or price2 == 0:
                        success = False
                        break
                    amount = amount * price1 / price2 * 0.997
                    current = next_token

            if success and current == "SOL":
                profit_sol = amount - amount_in_sol
                profit_usd = profit_sol * sol_price
                fees_usd = 0.005 * sol_price + amount_in_sol * sol_price * 0.003 * (len(path) - 1)
                net_usd = profit_usd - fees_usd

                verdict = "Отправлять" if net_usd > 0 else ("Не отправлять" if profit_usd > 0 else "Убыточно")

                if net_usd > best.net_usd or not best.path:
                    best = SimResult(
                        found=net_usd > 0,
                        path=path,
                        amount_in_sol=amount_in_sol,
                        amount_out_sol=amount,
                        profit_usd=profit_usd,
                        fees_usd=fees_usd,
                        net_usd=net_usd,
                        verdict=verdict,
                    )

        return best