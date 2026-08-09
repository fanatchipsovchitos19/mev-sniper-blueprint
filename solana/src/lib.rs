use std::ffi::{CStr, CString};
use std::os::raw::c_char;

mod pool_fetcher;
mod quote;
mod pathfinder;

// --- hello_from_rust (уже работает) ---

#[no_mangle]
pub extern "C" fn hello_from_rust() -> *mut c_char {
    let msg = CString::new("MEV Sniper Solana engine is ready.").unwrap();
    msg.into_raw()
}

#[no_mangle]
pub extern "C" fn free_string(ptr: *mut c_char) {
    if ptr.is_null() {
        return;
    }
    unsafe {
        let _ = CString::from_raw(ptr);
    }
}

// --- find_arbitrage (новая функция) ---

#[no_mangle]
pub extern "C" fn find_arbitrage(
    rpc_url: *const c_char,
    amount_in_lamports: u64,
) -> *mut c_char {
    let rpc_str = unsafe { CStr::from_ptr(rpc_url) }.to_str().unwrap().to_string();
    let result = pathfinder::find_arbitrage(&rpc_str, amount_in_lamports);
    let json = serde_json::to_string(&result).unwrap();
    CString::new(json).unwrap().into_raw()
}