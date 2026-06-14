from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet, generate_faucet_wallet
from xrpl.models.requests import AccountInfo
from xrpl.utils import xrp_to_drops

JSON_RPC_URL = "https://s.devnet.rippletest.net:51234"
client = JsonRpcClient(JSON_RPC_URL)


def create_depositor(funding_xrp: float = 1000.0) -> dict:
    """
    Creates a testnet depositor wallet funded via the faucet.
    funding_xrp is informational — the faucet always grants its default amount (~1000 XRP).
    Returns wallet metadata for use in subsequent vault deposit transactions.
    """
    print(f"\nCreating depositor wallet (requested funding: {funding_xrp} XRP)...")
    wallet = generate_faucet_wallet(client, debug=True)

    account_info = client.request(AccountInfo(account=wallet.classic_address))
    actual_balance_drops = int(account_info.result["account_data"]["Balance"])
    actual_balance_xrp = actual_balance_drops / 1_000_000

    print(f"\nDepositor account created:")
    print(f"  Address : {wallet.classic_address}")
    print(f"  Balance : {actual_balance_xrp:.2f} XRP")
    print(f"  Explorer: https://testnet.xrpl.org/accounts/{wallet.classic_address}")

    return {
        "wallet": wallet,
        "address": wallet.classic_address,
        "balance_xrp": actual_balance_xrp,
        "balance_drops": actual_balance_drops,
    }


if __name__ == "__main__":
    depositor = create_depositor(funding_xrp=500.0)
    print(f"\nDepositor ready: {depositor['address']} ({depositor['balance_xrp']} XRP)")
