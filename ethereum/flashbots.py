"""Ethereum Flashbots клиент для MEV-бандлов."""
import requests
import time
from dataclasses import dataclass
from typing import List, Optional


FLASHBOTS_RELAY = "https://relay.flashbots.net"


@dataclass
class EthBundleResult:
    success: bool
    bundle_hash: Optional[str] = None
    error: Optional[str] = None
    included_block: Optional[int] = None


class FlashbotsClient:
    """Клиент для отправки бандлов через Flashbots Protect."""

    def __init__(self, rpc_url: str = FLASHBOTS_RELAY):
        self.rpc_url = rpc_url
        self.session = requests.Session()

    def send_bundle(
        self,
        signed_transactions: List[str],
        target_block: int,
        auth_signer: str = None,
    ) -> EthBundleResult:
        """Отправить бандл в Flashbots relay."""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "eth_sendBundle",
            "params": [{
                "txs": signed_transactions,
                "blockNumber": hex(target_block),
                "minTimestamp": 0,
                "maxTimestamp": int(time.time()) + 300,
            }]
        }

        try:
            resp = self.session.post(self.rpc_url, json=payload, timeout=10)
            data = resp.json()

            if "error" in data:
                return EthBundleResult(
                    success=False,
                    error=data["error"].get("message", "Unknown error")
                )

            return EthBundleResult(
                success=True,
                bundle_hash=data.get("result"),
                included_block=target_block,
            )
        except Exception as e:
            return EthBundleResult(success=False, error=str(e))

    def simulate_bundle(
        self,
        signed_transactions: List[str],
        parent_block: str = "latest",
    ) -> dict:
        """Симуляция бандла перед отправкой."""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "eth_callBundle",
            "params": [{
                "txs": signed_transactions,
                "blockNumber": parent_block,
                "stateBlockNumber": parent_block,
            }]
        }

        try:
            resp = self.session.post(self.rpc_url, json=payload, timeout=10)
            return resp.json()
        except Exception as e:
            return {"error": str(e)}

    def get_bundle_status(self, bundle_hash: str) -> dict:
        """Проверить статус бандла."""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "flashbots_getBundleStats",
            "params": [{"bundleHash": bundle_hash}]
        }

        try:
            resp = self.session.post(self.rpc_url, json=payload, timeout=10)
            return resp.json()
        except Exception as e:
            return {"error": str(e)}