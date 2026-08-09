pub mod jito_client {
    tonic::include_proto!("jito");
}

use anyhow::Result;
use jito_client::mempool_stream_client::MempoolStreamClient;
use jito_client::MempoolRequest;
use serde::{Deserialize, Serialize};
use solana_sdk::{
    pubkey::Pubkey,
    signature::Signature,
    transaction::Transaction,
};
use std::str::FromStr;
use tokio::sync::mpsc;
use tonic::transport::Channel;

const JITO_GRPC_ENDPOINT: &str = "https://mainnet.block-engine.jito.wtf:443";

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MempoolTx {
    pub signature: String,
    pub slot: u64,
    pub priority_fee: f64,
    pub instructions: Vec<TxInstruction>,
    pub signer: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TxInstruction {
    pub program_id: String,
    pub data: String,
    pub accounts: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SandwichOpportunity {
    pub target_tx: MempoolTx,
    pub token_in: String,
    pub token_out: String,
    pub amount_in: u64,
    pub amount_out: u64,
    pub expected_profit_lamports: u64,
    pub pool_address: String,
}

/// Классификатор крупных свопов
pub fn detect_sandwich_opportunity(tx: &MempoolTx) -> Option<SandwichOpportunity> {
    // Ищем инструкции свопа в Raydium/Orca/Jupiter
    let swap_programs = [
        "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8", // Raydium
        "JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4", // Jupiter
        "whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc", // Orca
    ];

    let mut has_swap = false;
    for inst in &tx.instructions {
        if swap_programs.contains(&inst.program_id.as_str()) {
            has_swap = true;
            break;
        }
    }

    if !has_swap || tx.priority_fee < 10_000.0 {
        return None;
    }

    // Упрощённо: считаем что любая высокоприоритетная swap-транзакция — это цель
    Some(SandwichOpportunity {
        target_tx: tx.clone(),
        token_in: "SOL".to_string(),
        token_out: "USDC".to_string(),
        amount_in: 0,
        amount_out: 0,
        expected_profit_lamports: (tx.priority_fee * 0.5) as u64,
        pool_address: String::new(),
    })
}

/// Подключение к Jito gRPC мемпул-стриму
pub async fn start_mempool_stream(
    tx_sender: mpsc::UnboundedSender<MempoolTx>,
) -> Result<()> {
    println!("[MEMPOOL] Connecting to Jito gRPC...");

    let channel = Channel::from_static(JITO_GRPC_ENDPOINT)
        .connect()
        .await?;

    let mut client = MempoolStreamClient::new(channel);

    let request = tonic::Request::new(MempoolRequest {
        client_id: "mev-sniper-v0.2".to_string(),
    });

    let mut stream = client
        .subscribe_mempool(request)
        .await?
        .into_inner();

    println!("[MEMPOOL] Connected! Listening for transactions...");

    while let Some(update) = stream.message().await? {
        let tx = MempoolTx {
            signature: update.tx_signature,
            slot: update.slot,
            priority_fee: update.priority_fee,
            instructions: parse_instructions(&update.tx_data),
            signer: extract_signer(&update.tx_data),
        };

        if tx_sender.send(tx).is_err() {
            break; // канал закрыт
        }
    }

    Ok(())
}

fn parse_instructions(tx_data: &[u8]) -> Vec<TxInstruction> {
    // Упрощённый парсер — в реальности нужно десериализовать Transaction
    let mut instructions = Vec::new();

    if let Ok(tx) = bincode::deserialize::<Transaction>(tx_data) {
        for (i, inst) in tx.message().instructions().enumerate() {
            instructions.push(TxInstruction {
                program_id: tx.message().account_keys()[inst.program_id_index as usize].to_string(),
                data: hex::encode(&inst.data),
                accounts: inst
                    .accounts
                    .iter()
                    .map(|idx| tx.message().account_keys()[*idx as usize].to_string())
                    .collect(),
            });
        }
    }

    instructions
}

fn extract_signer(tx_data: &[u8]) -> String {
    if let Ok(tx) = bincode::deserialize::<Transaction>(tx_data) {
        if let Some(sig) = tx.signatures.first() {
            return sig.to_string();
        }
    }
    String::new()
}