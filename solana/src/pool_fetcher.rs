use anyhow::Result;
use serde::Serialize;
use solana_client::rpc_client::RpcClient;
use solana_sdk::pubkey::Pubkey;
use std::str::FromStr;

#[derive(Debug, Clone, Serialize)]
pub struct Pool {
    pub address: String,
    pub token_a: String,
    pub token_b: String,
    pub reserve_a: u64,
    pub reserve_b: u64,
    pub fee_rate: f64,
}

pub fn fetch_pools(_rpc: &RpcClient) -> Result<Vec<Pool>> {
    let pool_configs = vec![
        // === RAYDIUM STANDARD (AMM) ===
        // SOL pairs
        ("58oQChx4yWmvKdwLLZzBi4ChoCc2fqCUWBkwMihLYQo2", "SOL", "USDC"),
        ("8BnEgHoWFysVcuFFX7QztDmzuH8r5zfvyktX4rB5L7Xr", "SOL", "USDT"),
        ("2TfKqJEJFJkLcZ8kL6HvPYvL7nFTxKxR5jHtpH9J9Rk2", "RAY", "SOL"),
        ("6UmmXiYxPh8GjxJhJDCG8wFcYL9dDJjV3HJJqVH8RAmD", "ORCA", "SOL"),
        ("2ZnVuidgmJ4Dm4TKGhkLgN1WJtQvFAvm9Py9oDEpJtNX", "MNGO", "SOL"),
        ("H3h36mSbf9bMYkJFUHJGkxLBgKnn5x7cGzTiCJQ3AqFy", "SRM", "SOL"),
        ("BbJgLbX8j1VqVQQqLQSRs8tKCyzMNEqPzYHfHqLzXRpJ", "BONK", "SOL"),
        ("DRsaj4CrjcoM5z6Jd6KvFhNzgFjHqPkHG9n5KqjHFQiR", "JTO", "SOL"),
        
        // USDC pairs
        ("3NnxQvDcZXvRZXzM8yEwPEn8rK8VnJpF7J7J1JKJoNQq", "RAY", "USDC"),
        ("2p7nYbtgPC3A2gJxkFJV7qVZxPvJqJzJmH9DqH9xVyRA", "ORCA", "USDC"),
        ("9B1LK6zq4aQjTZHYLGk6JkPZxNqLPFUHkWuNXHqHZgfn", "MNGO", "USDC"),
        ("BEb2dDSfVkNVXQc4hdNy5JYLrJwkH7MbEoDLKmKwzKcT", "BONK", "USDC"),
        ("5ZgmkKvkJqRzUEvukHUHqJDKTqxBU1pXrHekyhmfEWLA", "JTO", "USDC"),
        ("27vYQcEGf6MsLGxLRPo7f7JchcCGRfhUEJXLkVBRJXhF", "WIF", "USDC"),
        
        // USDT pairs
        ("4JpVfqAqSYcGLHhYDqNqSH8hKsMqTnUqFfXkLxYhLgQa", "RAY", "USDT"),
        ("3kLSaXwLeGsFmvRBpJEjZcq4XFRhFUGgzXKeoHCykGyB", "BONK", "USDT"),
    ];

    let mut pools = Vec::new();
    for (addr_str, token_a, token_b) in pool_configs {
        let pubkey = match Pubkey::from_str(addr_str) {
            Ok(pk) => pk,
            Err(_) => continue,
        };
        match _rpc.get_account(&pubkey) {
            Ok(account) => {
                let data_len = account.data.len();
                let has_reserves = data_len >= 256;
                let pool = parse_pool(addr_str, token_a, token_b, &account.data);
                eprintln!("Pool {} ({}/{}): data_len={}, has_reserves={}, parsed={}",
                    addr_str, token_a, token_b, data_len, has_reserves, pool.is_some());
                if let Some(ref p) = pool {
                    eprintln!("  -> reserve_a={}, reserve_b={}", p.reserve_a, p.reserve_b);
                    pools.push(p.clone());
                }
            }
            Err(e) => {
                eprintln!("Pool {} ({}/{}): RPC error: {}", addr_str, token_a, token_b, e);
            }
        }
    }
    eprintln!("Total pools loaded: {}", pools.len());
    Ok(pools)
}

fn parse_pool(address: &str, token_a: &str, token_b: &str, data: &[u8]) -> Option<Pool> {
    if data.len() < 256 {
        return None;
    }

    let mut reserves: Vec<(usize, u64)> = Vec::new();
    for i in (0..data.len() - 8).step_by(8) {
        if let Ok(bytes) = data[i..i + 8].try_into() {
            let val = u64::from_le_bytes(bytes);
            if val > 1_000_000_000_000 {
                reserves.push((i, val));
            }
        }
    }

    if reserves.len() >= 2 {
        return Some(Pool {
            address: address.to_string(),
            token_a: token_a.to_string(),
            token_b: token_b.to_string(),
            reserve_a: reserves[0].1,
            reserve_b: reserves[1].1,
            fee_rate: 0.0025,
        });
    }

    None
}