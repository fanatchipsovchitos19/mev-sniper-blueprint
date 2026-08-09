"""AI-дебаггер: анализ ошибок MEV-бандлов."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class DebugReport:
    error_type: str
    explanation: str
    solution: str
    confidence: float


class MEVDebugger:
    """Анализатор ошибок MEV-транзакций."""

    ERROR_DB = {
        "Outrun by another searcher": {
            "explanation": "Ваш бандл был опережён другим MEV-ботом. Конкурент заплатил больше за газ или отправил бандл раньше.",
            "solution": "1. Увеличьте priority fee до 1M+ lamports\n2. Используйте Jito tip для приоритета\n3. Подключитесь к ноде ближе к валидаторам (Frankfurt/Amsterdam)",
        },
        "Slippage exceeded — price moved": {
            "explanation": "Цена токена изменилась между симуляцией и включением в блок. Проскальзывание превысило допустимое.",
            "solution": "1. Увеличьте slippage до 1-2%\n2. Разбейте сделку на меньшие части\n3. Используйте TWAP вместо рыночного ордера",
        },
        "Insufficient balance": {
            "explanation": "Недостаточно средств на кошельке для оплаты газа или свопа.",
            "solution": "1. Пополните кошелёк SOL/ETH\n2. Проверьте, что токены не заблокированы в стейкинге\n3. Оставьте резерв 0.01 SOL на газ",
        },
        "Blockhash expired": {
            "explanation": "Бандл не был включён в блок до истечения blockhash. Сеть перегружена или gas слишком низкий.",
            "solution": "1. Увеличьте priority fee\n2. Отправляйте бандлы с target_block = текущий + 2\n3. Используйте быструю ноду (Helius/Triton)",
        },
        "Already processed": {
            "explanation": "Транзакция уже была обработана в предыдущем блоке. Дубликат.",
            "solution": "1. Обновите nonce транзакции\n2. Используйте уникальный bundle hash",
        },
    }

    def debug(self, error_message: str) -> DebugReport:
        """Проанализировать ошибку и дать рекомендацию."""
        for pattern, info in self.ERROR_DB.items():
            if pattern.lower() in error_message.lower():
                return DebugReport(
                    error_type=pattern,
                    explanation=info["explanation"],
                    solution=info["solution"],
                    confidence=0.85,
                )

        return DebugReport(
            error_type="Unknown",
            explanation="Неизвестная ошибка. Проверьте логи ноды и параметры транзакции.",
            solution="1. Проверьте RPC-соединение\n2. Проверьте формат транзакции\n3. Попробуйте симулятор перед отправкой",
            confidence=0.3,
        )