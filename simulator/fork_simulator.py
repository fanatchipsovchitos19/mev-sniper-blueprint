"""Симулятор форка Solana Mainnet — реальные данные из ончейна."""
import time
import requests
import base64
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from datetime import datetime


HELIUS_RPC = "https://mainnet.helius-rpc.com/?api-key=c359e8d6-92d0-4233-9706-b5e8e50f13bd"
BINANCE_API = "https://api.binance.com/api/v3/ticker/price"
RAYDIUM_PROGRAM_ID = "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8"


@dataclass
class ForkSimResult:
    success: bool
    chain: str
    block_number: int
    bundle_id: str
    transactions: List[Dict]
    total_gas_used: int
    total_gas_cost_usd: float
    expected_profit_usd: float
    net_profit_usd: float
    revert_reason: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class ForkSimulator:
    """Симулятор с реальными данными из ончейна."""

    def __init__(self, chain: str = "solana"):
        self.chain = chain
        self.rpc_url = HELIUS_RPC
        self.pool_reserves: Dict[str, Dict[str, float]] = {}
        self.token_prices: Dict[str, float] = {}
        self.sol_price_usd = 150.0
        self.pools_by_pair: Dict[str, str] = {}

    def fetch_token_prices(self) -> Dict[str, float]:
        try:
            resp = requests.get(BINANCE_API, timeout=10)
            if resp.status_code == 200:
                return {item["symbol"]: float(item["price"]) for item in resp.json()}
        except Exception as e:
            print(f"  [!] Binance error: {e}")
        return {}

    def fetch_pool_addresses(self, limit: int = 50) -> List[str]:
        print(f"  Searching Raydium pools...")
        payload = {
            "jsonrpc": "2.0", "id": 1,
            "method": "getProgramAccounts",
            "params": [RAYDIUM_PROGRAM_ID, {"encoding": "base64", "filters": [{"dataSize": 752}]}],
        }
        try:
            resp = requests.post(self.rpc_url, json=payload, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                if "result" in data:
                    found = [item["pubkey"] for item in data["result"] if "pubkey" in item]
                    print(f"  Found {len(found)} pools (total: {len(data['result'])})")
                    return found[:limit]
        except Exception as e:
            print(f"  RPC error: {e}")
        return []

    def fetch_pool_data(self, address: str) -> Optional[Dict]:
        payload = {
            "jsonrpc": "2.0", "id": 1,
            "method": "getAccountInfo",
            "params": [address, {"encoding": "base64"}],
        }
        try:
            resp = requests.post(self.rpc_url, json=payload, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if "result" in data and data["result"] and "value" in data["result"]:
                    value = data["result"]["value"]
                    if value and "data" in value:
                        raw = value["data"]
                        if isinstance(raw, list) and len(raw) >= 1:
                            return self._parse_pool_v4(base64.b64decode(raw[0]), address)
        except Exception:
            pass
        return None

    def _parse_pool_v4(self, data: bytes, address: str) -> Optional[Dict]:
        if len(data) < 296:
            return None

        reserve_a = int.from_bytes(data[208:216], 'little')
        reserve_b = int.from_bytes(data[288:296], 'little')

        if reserve_a < 100_000 or reserve_b < 100_000:
            return None

        token_a, token_b = self._identify_by_reserves(reserve_a, reserve_b)

        if token_a == "UNKNOWN" and token_b == "UNKNOWN":
            return None

        return {
            "address": address,
            "token_a": token_a,
            "token_b": token_b,
            "reserve_a": reserve_a,
            "reserve_b": reserve_b,
        }

    def _identify_by_reserves(self, r1: float, r2: float) -> tuple:
        """Определить токены по порядку величины резервов."""
        log1 = len(str(int(r1)))
        log2 = len(str(int(r2)))

        # SOL: 10^9 lamports за 1 SOL → для пула с 1000+ SOL: 10^12–10^13
        # USDC: 10^6 decimals → для пула с 1M USDC: 10^12–10^13
        # RAY/ORCA/JTO: обычно 10^9–10^11
        # Мемкоины (BONK/WIF): 10^14+

        if 11 <= log1 <= 13 and 11 <= log2 <= 13:
            return ("SOL", "USDC")
        if log1 >= 14 and 11 <= log2 <= 13:
            return ("BONK", "SOL")
        if 11 <= log1 <= 13 and log2 >= 14:
            return ("SOL", "BONK")
        if 9 <= log1 <= 11 and 9 <= log2 <= 11:
            return ("RAY", "SOL")
        if 8 <= log1 <= 10 and 11 <= log2 <= 13:
            return ("ORCA", "USDC")

        return ("UNKNOWN", "UNKNOWN")

    def load_data(self):
        print("\n  Loading real data...")
        print("  Prices: Binance API...")
        self.token_prices = self.fetch_token_prices()
        if "SOLUSDT" in self.token_prices:
            self.sol_price_usd = self.token_prices["SOLUSDT"]
            print(f"  [OK] SOL = ${self.sol_price_usd}")

        extra = {}
        for sym, price in self.token_prices.items():
            if sym.endswith("USDT"):
                extra[sym.replace("USDT", "")] = price
            elif sym.endswith("USDC"):
                extra[sym.replace("USDC", "")] = price
        self.token_prices.update(extra)

        print("  Pools: Helius RPC...")
        addresses = self.fetch_pool_addresses(limit=100)
        loaded = 0

        for addr in addresses:
            pool = self.fetch_pool_data(addr)
            if pool:
                name = f"{pool['token_a']}/{pool['token_b']}"
                if name not in self.pool_reserves:
                    self.pool_reserves[name] = {
                        pool['token_a']: pool['reserve_a'],
                        pool['token_b']: pool['reserve_b'],
                    }
                    self.pools_by_pair[name] = name
                    self.pools_by_pair[f"{pool['token_b']}/{pool['token_a']}"] = name
                    print(f"  [OK] {name}: {pool['token_a']}={pool['reserve_a']:,.0f}, {pool['token_b']}={pool['reserve_b']:,.0f}")
                    loaded += 1

        if "SOL/USDC" not in self.pool_reserves:
            print("  [!] Adding fallback SOL/USDC pool")
            self.pool_reserves["SOL/USDC"] = {"SOL": 4_042_287_200_334, "USDC": 3_794_744_337_201}
            self.pools_by_pair["SOL/USDC"] = "SOL/USDC"
            self.pools_by_pair["USDC/SOL"] = "SOL/USDC"
            loaded += 1

        print(f"  Loaded {loaded} pools, {len(self.token_prices)} prices\n")

    def get_pool(self, token_a: str, token_b: str) -> Optional[str]:
        return self.pools_by_pair.get(f"{token_a}/{token_b}")

    def simulate_swap(self, pool_name: str, token_in: str, amount_in: float) -> Optional[Dict]:
        if pool_name not in self.pool_reserves:
            return None

        pool = self.pool_reserves[pool_name]
        tokens = list(pool.keys())

        if token_in not in tokens:
            return None

        token_out = tokens[1] if token_in == tokens[0] else tokens[0]
        reserve_in = pool[token_in]
        reserve_out = pool[token_out]

        if reserve_in <= 0 or reserve_out <= 0:
            return None

        fee = 0.9975
        amount_in_with_fee = amount_in * fee
        new_reserve_in = reserve_in + amount_in_with_fee
        new_reserve_out = (reserve_in * reserve_out) / new_reserve_in
        amount_out = reserve_out - new_reserve_out

        return {
            "token_in": token_in,
            "token_out": token_out,
            "amount_in": amount_in,
            "amount_out": amount_out,
            "pool": pool_name,
            "price_impact": (amount_in / reserve_in) * 100,
        }

    def simulate_arbitrage_bundle(self, path: List[str], amount_in_sol: float = 1.0) -> ForkSimResult:
        if not self.pool_reserves:
            self.load_data()

        transactions = []
        total_gas = 0
        current_amount = amount_in_sol
        current_token = "SOL"
        success = True
        revert_reason = None

        for next_token in path[1:]:
            pool_name = self.get_pool(current_token, next_token)
            if not pool_name:
                revert_reason = f"No pool for {current_token} -> {next_token}"
                success = False
                break

            swap = self.simulate_swap(pool_name, current_token, current_amount)
            if not swap:
                revert_reason = f"Swap failed for {current_token} -> {next_token}"
                success = False
                break

            current_amount = swap["amount_out"]
            current_token = swap["token_out"]
            total_gas += 200_000

            transactions.append({
                "step": len(transactions) + 1,
                "pool": pool_name,
                "token_in": swap["token_in"],
                "token_out": swap["token_out"],
                "amount_in": swap["amount_in"],
                "amount_out": swap["amount_out"],
                "price_impact_pct": swap["price_impact"],
            })

        total_gas_lamports = total_gas + 100_000 + 5_000_000
        total_gas_usd = total_gas_lamports / 1_000_000_000 * self.sol_price_usd

        if success and current_token == "SOL":
            profit_sol = current_amount - amount_in_sol
            profit_usd = profit_sol * self.sol_price_usd
            net_usd = profit_usd - total_gas_usd
        else:
            profit_usd = 0
            net_usd = -total_gas_usd
            if not revert_reason:
                revert_reason = f"Ended at {current_token}, expected SOL"
                success = False

        return ForkSimResult(
            success=success and net_usd > 0,
            chain=self.chain,
            block_number=int(time.time()),
            bundle_id=f"sim_{int(time.time())}",
            transactions=transactions,
            total_gas_used=total_gas_lamports,
            total_gas_cost_usd=total_gas_usd,
            expected_profit_usd=profit_usd,
            net_profit_usd=net_usd,
            revert_reason=revert_reason if not success else None,
        )


if __name__ == "__main__":
    import sys

    sim = ForkSimulator(chain="solana")
    sim.load_data()

    path = sys.argv[1].split(",") if len(sys.argv) > 1 else ["SOL", "USDC", "SOL"]
    amount = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0

    print(f"\n{'='*55}")
    print(f"  MEV FORK SIMULATOR (LIVE DATA)")
    print(f"  Path: {' -> '.join(path)}")
    print(f"  Amount: {amount} SOL")
    print(f"{'='*55}\n")

    result = sim.simulate_arbitrage_bundle(path, amount)

    for tx in result.transactions:
        print(f"  Step {tx['step']}: {tx['token_in']} -> {tx['token_out']}")
        print(f"    Pool: {tx['pool']}")
        print(f"    In: {tx['amount_in']:.6f} {tx['token_in']}")
        print(f"    Out: {tx['amount_out']:.6f} {tx['token_out']}")
        print(f"    Impact: {tx['price_impact_pct']:.4f}%")

    print(f"\n  {'='*45}")
    print(f"  SOL Price: ${sim.sol_price_usd:.2f}")
    print(f"  Gas: ${result.total_gas_cost_usd:.4f}")
    print(f"  Profit: ${result.expected_profit_usd:.4f}")
    print(f"  Net: ${result.net_profit_usd:.4f}")
    print(f"  Success: {'YES' if result.success else 'NO'}")
    if result.revert_reason:
        print(f"  Reason: {result.revert_reason}")
    print(f"  {'='*45}\n")

    if result.success and result.net_profit_usd > 0:
        print("  VERDICT: SEND BUNDLE")
    elif result.expected_profit_usd > 0:
        print("  VERDICT: PROFITABLE BUT GAS TOO HIGH")
    else:
        print("  VERDICT: DO NOT SEND")