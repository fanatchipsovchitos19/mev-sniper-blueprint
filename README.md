# MEV Sniper Blueprint v1.0.0

A complete MEV bot framework for Solana and Ethereum. Sandwich attacks, arbitrage scanner, AI gas optimizer, Jito + Flashbots clients.

## Features

- **Sandwich Detector** — monitors Solana mempool for large swaps
- **Bundle Simulator** — tests bundles before submission
- **AI Gas Optimizer** — predicts optimal priority fees
- **Jito Client** — sends bundles via Jito Block Engine (Rust + Python)
- **Flashbots Client** — sends bundles on Ethereum
- **MEV Debugger** — analyzes failed transactions
- **Fork Simulator** — tests on a blockchain copy with real reserves

The bot starts in demo mode (simulated mempool). You'll see sandwich opportunities with real math.

Real Mempool
For live transactions, you need a paid RPC:

Helius ($49/mo) — https://helius.dev

QuickNode — https://quicknode.com

Triton — https://triton.one

Add your API key to config.yaml and set live_mode: true.

Requirements
Python 3.10+

2+ GB RAM

Rust (optional, for Jito client compilation)

Helius/QuickNode API key (for real mempool)
