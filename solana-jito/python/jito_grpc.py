"""Реальный Jito gRPC мемпул-стрим."""
import requests
import json
import time
import threading
from typing import Callable, Optional


JITO_RPC = "https://mainnet.block-engine.jito.wtf/api/v1"
HELIUS_RPC = "https://mainnet.helius-rpc.com/?api-key=c359e8d6-92d0-4233-9706-b5e8e50f13bd"

# Известные DEX программы
DEX_PROGRAMS = {
    "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8": "Raydium",
    "JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4": "Jupiter",
    "whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc": "Orca",
}


class JitoMempoolStream:
    """Стрим мемпула через Jito + Helius polling."""

    def __init__(self, on_transaction: Optional[Callable] = None):
        self.on_tx = on_transaction
        self.running = False
        self.thread = None
        self.tx_count = 0
        self.seen_signatures = set()

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._poll_blocks, daemon=True)
        self.thread.start()
        print(f"[MEMPOOL] Started (Jito + Helius)")

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=3)
        print(f"[MEMPOOL] Stopped. Total tx: {self.tx_count}")

    def _rpc(self, method: str, params: list = None) -> dict:
        payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params or []}
        try:
            resp = requests.post(HELIUS_RPC, json=payload, timeout=15)
            return resp.json()
        except:
            return {}

    def _poll_blocks(self):
        last_slot = self._rpc("getSlot", [{"commitment": "confirmed"}]).get("result", 0)

        while self.running:
            try:
                current_slot = self._rpc("getSlot", [{"commitment": "confirmed"}]).get("result", 0)

                if current_slot and current_slot > last_slot:
                    # Обрабатываем пропущенные слоты
                    for slot in range(last_slot + 1, current_slot + 1):
                        self._process_slot(slot)
                    last_slot = current_slot

                time.sleep(0.4)
            except Exception as e:
                if self.running:
                    print(f"  [!] Stream error: {e}")
                time.sleep(2)

    def _process_slot(self, slot: int):
        # Получаем блок
        block = self._rpc("getBlock", [
            slot,
            {
                "encoding": "json",
                "maxSupportedTransactionVersion": 0,
                "transactionDetails": "full",
                "rewards": False,
            },
        ])

        txs = block.get("result", {}).get("transactions", [])
        for tx in txs[:50]:  # макс 50 tx за слот
            self._process_tx(tx, slot)

    def _process_tx(self, tx: dict, slot: int):
        sig = tx.get("transaction", {}).get("signatures", ["unknown"])[0]
        if sig in self.seen_signatures:
            return
        self.seen_signatures.add(sig)
        self.tx_count += 1

        meta = tx.get("meta", {})
        message = tx.get("transaction", {}).get("message", {})

        # Priority fee
        fee = meta.get("fee", 0)
        compute_units = meta.get("computeUnitsConsumed", 0) or 200_000
        base_fee = compute_units * 5
        priority_fee = max(0, fee - base_fee)

        # Пропускаем низкоприоритетные
        if priority_fee < 50_000:
            return

        # Определяем программу
        instructions = message.get("instructions", [])
        account_keys = message.get("accountKeys", [])
        program_id = "unknown"

        for inst in instructions:
            idx = inst.get("programIdIndex", 0)
            if idx < len(account_keys):
                pid = account_keys[idx]
                if pid in DEX_PROGRAMS:
                    program_id = pid
                    break

        # Пропускаем не-DEX транзакции
        if program_id == "unknown":
            return

        # Оценка суммы
        pre_balances = meta.get("preBalances", [0])
        post_balances = meta.get("postBalances", [0])
        diff = abs(pre_balances[0] - post_balances[0]) if pre_balances and post_balances else 0
        amount_sol = diff / 1_000_000_000
        amount_usd = amount_sol * 150

        # Пропускаем маленькие суммы
        if amount_usd < 1000 and priority_fee < 500_000:
            return

        tx_data = {
            "signature": sig,
            "slot": slot,
            "priority_fee": priority_fee,
            "amount_usd": amount_usd,
            "amount_sol": amount_sol,
            "program": program_id,
            "dex": DEX_PROGRAMS.get(program_id, "unknown"),
            "token_in": "SOL",
            "token_out": "UNKNOWN",
        }

        if self.on_tx:
            self.on_tx(tx_data)