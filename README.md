Фреймворк для запуска MEV-бота на Solana и Ethereum.

Что внутри
Сэндвич-детектор — слушает мемпул Solana, находит крупные свопы

Симулятор бандлов — проверяет прибыльность атаки перед отправкой

AI-Gas оптимизатор — подбирает комиссию для обгона конкурентов

Jito-клиент — отправка бандлов через Jito Block Engine (Rust + Python)

Flashbots-клиент — отправка бандлов на Ethereum

MEV Debugger — анализ ошибок и рекомендации

Форк-симулятор — тестирование на копии блокчейна

Быстрый старт
pip install -r requirements.txt
python runner.py

Бот запустится в демо-режиме (симуляция мемпула).

Подключение реального мемпула
Нужен платный RPC:

Helius ($49/мес) — https://helius.dev

QuickNode — https://quicknode.com

Triton — https://triton.one

Вставьте API-ключ в config.yaml, установите live_mode: true.

Структура
runner.py — точка входа

config.yaml — настройки

simulator/ — симулятор бандлов и форка

ai_gas/ — AI-оптимизатор газа

solana-jito/ — Rust Jito-клиент + Python-обёртка

ethereum/ — Flashbots-клиент

education/ — гайд "Мышление MEV-охотника"

Системные требования
Python 3.10+

2+ GB RAM

Rust (опционально)

Helius/QuickNode API ключ (для реального мемпула)