use crate::pool_fetcher::{fetch_pools, Pool};
use crate::quote::get_amount_out;
use serde::Serialize;
use solana_client::rpc_client::RpcClient;

#[derive(Debug, Serialize)]
pub struct ArbitrageResult {
    pub found: bool,
    pub path: Vec<String>,
    pub amount_in_lamports: u64,
    pub amount_out_lamports: u64,
    pub profit_lamports: u64,
    pub profit_usd: f64,
    pub fees_lamports: u64,
    pub net_lamports: i64,
    pub verdict: String,
}

pub fn find_arbitrage(rpc_url: &str, amount_in: u64) -> ArbitrageResult {
    let rpc = RpcClient::new(rpc_url.to_string());
    let pools = fetch_pools(&rpc).unwrap_or_default();

    let sol_price_usd = 150.0;

    // Перебираем все возможные пары пулов для арбитража
    let mut best: Option<ArbitrageResult> = None;

    // Циклы длины 2: A→B→A (разные пулы)
    // Циклы длины 2: A→B→A (через разные пулы или обратный своп)
    for pool1 in &pools {
        for pool2 in &pools {
            if pool1.address == pool2.address {
                continue;
            }

            // Вариант 1: оба в одном направлении (SOL→USDC в pool1, SOL→USDC в pool2)
            if pool1.token_a == pool2.token_a && pool1.token_b == pool2.token_b {
                let mid = get_amount_out(amount_in, pool1.reserve_a, pool1.reserve_b, pool1.fee_rate);
                let out = get_amount_out(mid, pool2.reserve_b, pool2.reserve_a, pool2.fee_rate);
                evaluate_path(
                    &mut best, amount_in, out,
                    vec![pool1.token_a.clone(), pool1.token_b.clone(), pool2.token_a.clone()],
                    sol_price_usd,
                );
            }

            // Вариант 2: pool1 A→B, pool2 B→A (обратный своп)
            if pool1.token_b == pool2.token_a && pool1.token_a == pool2.token_b {
                let mid = get_amount_out(amount_in, pool1.reserve_a, pool1.reserve_b, pool1.fee_rate);
                let out = get_amount_out(mid, pool2.reserve_a, pool2.reserve_b, pool2.fee_rate);
                evaluate_path(
                    &mut best, amount_in, out,
                    vec![pool1.token_a.clone(), pool1.token_b.clone(), pool2.token_b.clone()],
                    sol_price_usd,
                );
            }
        }
    }

    // Циклы длины 3: A→B→C→A
    for p1 in &pools {
        for p2 in &pools {
            if p1.address == p2.address { continue; }
            if p1.token_b != p2.token_a { continue; }
            for p3 in &pools {
                if p2.address == p3.address || p1.address == p3.address { continue; }
                if p2.token_b != p3.token_a { continue; }
                if p3.token_b != p1.token_a { continue; }

                let mid1 = get_amount_out(amount_in, p1.reserve_a, p1.reserve_b, p1.fee_rate);
                let mid2 = get_amount_out(mid1, p2.reserve_a, p2.reserve_b, p2.fee_rate);
                let out = get_amount_out(mid2, p3.reserve_a, p3.reserve_b, p3.fee_rate);
                evaluate_path(
                    &mut best,
                    amount_in,
                    out,
                    vec![p1.token_a.clone(), p1.token_b.clone(), p2.token_b.clone(), p3.token_b.clone()],
                    sol_price_usd,
                );
            }
        }
    }

    match best {
        Some(b) => b,
        None => ArbitrageResult {
            found: false,
            path: vec![],
            amount_in_lamports: amount_in,
            amount_out_lamports: 0,
            profit_lamports: 0,
            profit_usd: 0.0,
            fees_lamports: 5_000_000,
            net_lamports: -5_000_000,
            verdict: "Убыточно".to_string(),
        },
    }
}

fn evaluate_path(
    best: &mut Option<ArbitrageResult>,
    amount_in: u64,
    amount_out: u64,
    path: Vec<String>,
    sol_price: f64,
) {
    let fees = 5_000_000; // ~0.005 SOL gas
    let profit = if amount_out > amount_in { amount_out - amount_in } else { 0 };
    let net = profit as i64 - fees as i64;
    let profit_usd = profit as f64 / 1_000_000_000.0 * sol_price;

    let verdict = if net > 0 {
        "Отправлять"
    } else if profit > 0 {
        "Не отправлять"
    } else {
        "Убыточно"
    };

    let result = ArbitrageResult {
        found: profit > 0,
        path,
        amount_in_lamports: amount_in,
        amount_out_lamports: amount_out,
        profit_lamports: profit,
        profit_usd,
        fees_lamports: fees,
        net_lamports: net,
        verdict: verdict.to_string(),
    };

    match best {
        None => *best = Some(result),
        Some(ref b) if net > b.net_lamports => *best = Some(result),
        _ => {}
    }
}