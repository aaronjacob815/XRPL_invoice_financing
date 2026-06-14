from xrpl.wallet import generate_faucet_wallet
from xrpl.models import VaultDeposit
from xrpl.models.requests import AccountInfo
from xrpl.transaction import submit_and_wait
from xrpl.utils import xrp_to_drops

from demo_config import client, DEVNET
from utils import require_success


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
    print(f"  Explorer: https://devnet.xrpl.org/accounts/{wallet.classic_address}")

    return {
        "wallet": wallet,
        "address": wallet.classic_address,
        "balance_xrp": actual_balance_xrp,
        "balance_drops": actual_balance_drops,
    }

def deposit_into_vault(depositor: dict, vault_id: str, amount_xrp: float):
    """Sends XRP from a depositor into the vault; depositor receives vault share MPTs."""
    print(f"  {depositor['address']}  →  {amount_xrp} XRP")

    tx = VaultDeposit(
        account=depositor["address"],
        vault_id=vault_id,
        amount=xrp_to_drops(amount_xrp),
    )
    response = submit_and_wait(tx, client, depositor["wallet"], autofill=True)
    require_success(response, "VaultDeposit")

    print(f"    tx: {DEVNET}/transactions/{response.result['hash']}")


if __name__ == "__main__":
    depositor = create_depositor(funding_xrp=500.0)
    print(f"\nDepositor ready: {depositor['address']} ({depositor['balance_xrp']} XRP)")
