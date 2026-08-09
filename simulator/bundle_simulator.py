"""Симулятор отправки MEV-бандла на Solana с Jito."""
import random
import hashlib
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


@dataclass
class BundleResult:
    success: bool
    bundle_id: str
    slot: int
    gas_used: int
    priority_fee: int
    jito_tip: int
    total_fees_lamports: int
    total_fees_usd: float
    profit_after_fees_usd: float
    revert_reason: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class BundleSimulator:
    """Симулятор Jito Block Engine с реалистичной моделью конкуренции."""

    def __init__(self, sol_price_usd: float = 150.0):
        self.sol_price = sol_price_usd
        self.base_fee = 5_000  # lamports per tx

    def _generate_bundle_id(self) -> str:
        return hashlib.sha256(str(random.random()).encode()).hexdigest()[:44]

    def simulate_bundle(
        self,
        transactions: List[dict],
        expected_profit_usd: float,
        priority_fee_lamports: int = 100_000,
        jito_tip_lamports: int = 10_000_000,
    ) -> BundleResult:
        """Симуляция с моделью рисков."""
        tx_count = len(transactions)
        base_cost = self.base_fee * tx_count
        total_fees = base_cost + priority_fee_lamports + jito_tip_lamports
        total_fees_usd = total_fees / 1_000_000_000 * self.sol_price

        # Модель конкуренции: чем выше priority fee, тем меньше шанс что опередят
        competition_threshold = 500_000  # lamports
        if priority_fee_lamports < competition_threshold:
            outrun_chance = 0.4
        elif priority_fee_lamports < 1_000_000:
            outrun_chance = 0.2
        elif priority_fee_lamports < 5_000_000:
            outrun_chance = 0.08
        else:
            outrun_chance = 0.02

        # Шанс реверта из-за проскальзывания
        if expected_profit_usd < 1.0:
            revert_chance = 0.10
        elif expected_profit_usd < 5.0:
            revert_chance = 0.04
        else:
            revert_chance = 0.01

        roll = random.random()

        if roll < outrun_chance:
            return BundleResult(
                success=False,
                bundle_id=self._generate_bundle_id(),
                slot=random.randint(300_000_000, 350_000_000),
                gas_used=tx_count * 200_000,
                priority_fee=priority_fee_lamports,
                jito_tip=jito_tip_lamports,
                total_fees_lamports=total_fees,
                total_fees_usd=total_fees_usd,
                profit_after_fees_usd=expected_profit_usd - total_fees_usd,
                revert_reason="Outrun by another searcher"
            )

        if roll < outrun_chance + revert_chance:
            return BundleResult(
                success=False,
                bundle_id=self._generate_bundle_id(),
                slot=random.randint(300_000_000, 350_000_000),
                gas_used=tx_count * 200_000,
                priority_fee=priority_fee_lamports,
                jito_tip=jito_tip_lamports,
                total_fees_lamports=total_fees,
                total_fees_usd=total_fees_usd,
                profit_after_fees_usd=expected_profit_usd - total_fees_usd,
                revert_reason="Slippage exceeded — price moved"
            )

        return BundleResult(
            success=True,
            bundle_id=self._generate_bundle_id(),
            slot=random.randint(300_000_000, 350_000_000),
            gas_used=tx_count * 200_000,
            priority_fee=priority_fee_lamports,
            jito_tip=jito_tip_lamports,
            total_fees_lamports=total_fees,
            total_fees_usd=total_fees_usd,
            profit_after_fees_usd=expected_profit_usd - total_fees_usd,
        )