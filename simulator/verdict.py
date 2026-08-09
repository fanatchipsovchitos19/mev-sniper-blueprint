"""Форматирование вердикта симуляции."""


def render_verdict(result) -> str:
    verdict_icon = {
        "Отправлять": "✅",
        "Не отправлять": "⚠️",
        "Убыточно": "❌"
    }

    icon = verdict_icon.get(result.verdict, "?")

    return f"""
╔══════════════════════════════╗
║     MEV BUNDLE SIMULATION    ║
╠══════════════════════════════╣
║  Путь:      {" → ".join(result.path):<18} ║
║  Вход:      {result.amount_in_sol:>10.4f} SOL ║
║  Выход:     {result.amount_out_sol:>10.4f} SOL ║
║  Прибыль:   ${result.profit_usd:>10.2f}  ║
║  Комиссии:  ${result.fees_usd:>10.2f}  ║
║  ─────────────────────────  ║
║  ЧИСТАЯ:    ${result.net_usd:>10.2f}  ║
╠══════════════════════════════╣
║  ВЕРДИКТ: {icon} {result.verdict:<17} ║
╚══════════════════════════════╝
"""