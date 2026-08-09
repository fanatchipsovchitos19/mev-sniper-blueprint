"""Python-обёртка для mev_sniper_solana."""
import ctypes
import json
import os

_lib_path = os.path.join(
    os.path.dirname(__file__), "..", "target", "release", "libmev_sniper_solana.so"
)
_lib = ctypes.CDLL(_lib_path)

# hello_from_rust
_lib.hello_from_rust.restype = ctypes.c_void_p

# find_arbitrage
_lib.find_arbitrage.argtypes = [ctypes.c_char_p, ctypes.c_uint64]
_lib.find_arbitrage.restype = ctypes.c_void_p

# free_string
_lib.free_string.argtypes = [ctypes.c_void_p]


def hello_from_rust() -> str:
    ptr = _lib.hello_from_rust()
    result = ctypes.cast(ptr, ctypes.c_char_p).value.decode("utf-8")
    _lib.free_string(ptr)
    return result


def find_arbitrage(rpc_url: str, amount_in_lamports: int) -> dict:
    ptr = _lib.find_arbitrage(rpc_url.encode("utf-8"), amount_in_lamports)
    json_str = ctypes.cast(ptr, ctypes.c_char_p).value.decode("utf-8")
    _lib.free_string(ptr)
    return json.loads(json_str)