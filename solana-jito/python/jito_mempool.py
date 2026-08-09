"""Jito Mempool Stream — Python интерфейс."""
import subprocess
import json
import threading
import queue
from typing import Callable, Optional


class MempoolListener:
    """Слушатель мемпула Solana через Jito."""

    def __init__(self, on_tx: Optional[Callable] = None):
        self.on_tx = on_tx
        self.queue = queue.Queue()
        self.running = False
        self.thread = None

    def start(self):
        """Запустить слушатель в отдельном потоке."""
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        print("[MEMPOOL] Started mempool listener")

    def stop(self):
        """Остановить слушатель."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        print("[MEMPOOL] Stopped")

    def _run(self):
        """Запуск Rust-бинаря для gRPC стрима."""
        try:
            # В будущем здесь будет запуск Rust-бинаря
            # Пока эмулируем мемпул для демонстрации
            import time
            import random

            tokens = ["SOL", "USDC", "RAY", "ORCA", "JTO", "BONK", "WIF"]
            programs = [
                "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8",
                "JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4",
            ]

            while self.running:
                tx = {
                    "signature": f"sim_{random.randint(0, 2**64):x}",
                    "slot": random.randint(300_000_000, 350_000_000),
                    "priority_fee": random.uniform(10_000, 1_000_000),
                    "token_in": random.choice(tokens),
                    "token_out": random.choice(tokens),
                    "amount_usd": random.uniform(100, 100_000),
                    "program": random.choice(programs),
                }

                if self.on_tx:
                    self.on_tx(tx)
                else:
                    self.queue.put(tx)

                time.sleep(random.uniform(0.1, 2.0))

        except Exception as e:
            print(f"[MEMPOOL] Error: {e}")