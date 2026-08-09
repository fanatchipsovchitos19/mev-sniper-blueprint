/// Расчёт amount_out для Constant Product AMM (x * y = k)
/// amount_in — сколько токена A мы продаём
/// reserve_in — резерв токена A в пуле
/// reserve_out — резерв токена B в пуле
/// fee_rate — комиссия пула (0.0025 = 0.25%)
pub fn get_amount_out(amount_in: u64, reserve_in: u64, reserve_out: u64, fee_rate: f64) -> u64 {
    let amount_in_with_fee = (amount_in as f64 * (1.0 - fee_rate)) as u128;
    let numerator = amount_in_with_fee * reserve_out as u128;
    let denominator = reserve_in as u128 + amount_in_with_fee;
    (numerator / denominator) as u64
}