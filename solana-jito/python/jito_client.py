"""Python-обёртка для Jito-клиента."""
import ctypes
import os
import json


_lib_path = os.path.join(
    os.path.dirname(__file__), "..", "target", "release", "solana_jito.dll"
)
_lib = ctypes.CDLL(_lib_path)

# TODO: экспортировать функции из Rust через #[no_mangle]
# Пока используем прямые HTTP-запросы к Jito API


class JitoClient:
    """Клиент для отправки бандлов в Jito Block Engine."""
    
    JITO_MAINNET = "https://mainnet.block-engine.jito.wtf"
    
    def __init__(self, rpc_url: str = None):
        self.rpc_url = rpc_url or self.JITO_MAINNET
    
    def send_bundle(self, transactions: list, tip_lamports: int = 10_000_000) -> dict:
        """Отправить бандл в Jito."""
        import requests
        
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "sendBundle",
            "params": [transactions]
        }
        
        resp = requests.post(
            f"{self.rpc_url}/api/v1/bundles",
            json=payload,
            timeout=10
        )
        return resp.json()
    
    def get_bundle_status(self, bundle_id: str) -> dict:
        """Получить статус бандла."""
        import requests
        
        resp = requests.get(
            f"{self.rpc_url}/api/v1/bundles/bundle/{bundle_id}",
            timeout=10
        )
        return resp.json()