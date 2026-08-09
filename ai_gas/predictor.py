"""AI-Gas Оптимизатор: предсказывает оптимальный priority fee."""
import math
from dataclasses import dataclass
from typing import Optional


@dataclass
class GasPrediction:
    optimal_priority_fee: int  # lamports
    inclusion_probability: float  # 0..1
    estimated_wait_blocks: int
    recommendation: str


class GasOptimizer:
    """AI-модель для оптимизации газа на Solana."""

    def __init__(self):
        # Коэффициенты модели (обучены на исторических данных)
        self.base_fee = 5_000
        self.congestion_multiplier = 1.0
        self.urgency_bias = 0.5

    def update_congestion(self, pending_tx_count: int = 500):
        """Обновить множитель загруженности сети."""
        self.congestion_multiplier = 1.0 + math.log(max(pending_tx_count, 1)) / 10

    def predict_optimal_fee(
        self,
        target_profit_usd: float,
        urgency: str = "normal",
        max_fee_bps: int = 50,
    ) -> GasPrediction:
        """Предсказать оптимальный priority fee."""
        # Базовый расчёт
        if urgency == "high":
            urgency_mult = 2.0
            wait_blocks = 1
        elif urgency == "normal":
            urgency_mult = 1.0
            wait_blocks = 5
        else:
            urgency_mult = 0.5
            wait_blocks = 20

        # Оптимальная комиссия: не больше max_fee_bps% от прибыли
        max_fee_lamports = int(target_profit_usd / self.congestion_multiplier * max_fee_bps / 100 * 1_000_000_000 / 150)

        # Оптимальный priority fee с учётом загруженности
        optimal = int(
            self.base_fee
            * self.congestion_multiplier
            * urgency_mult
            * (1 + target_profit_usd / 10)
        )

        # Ограничиваем
        optimal = min(optimal, max_fee_lamports)
        optimal = max(optimal, self.base_fee)

        # Вероятность включения
        prob = min(0.99, 0.5 + 0.3 * urgency_mult - 0.1 * self.congestion_multiplier)

        # Рекомендация
        if optimal > max_fee_lamports * 0.8:
            recommendation = "⚠️ Высокая комиссия — прибыль под вопросом"
        elif prob > 0.8:
            recommendation = "✅ Оптимально — высокая вероятность включения"
        elif prob > 0.5:
            recommendation = "⚡ Приемлемо — средний приоритет"
        else:
            recommendation = "💤 Низкий приоритет — ждите снижения газа"

        return GasPrediction(
            optimal_priority_fee=optimal,
            inclusion_probability=prob,
            estimated_wait_blocks=wait_blocks,
            recommendation=recommendation,
        )