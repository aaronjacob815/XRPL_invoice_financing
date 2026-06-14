from xrpl.models import VaultCreate
from xrpl.models.transactions.vault_create import WithdrawalPolicy
from xrpl.transaction import submit_and_wait

from demo_config import client, DEVNET
from utils import require_success, created_node


def create_xrp_vault(broker_wallet) -> dict:
    """Creates an XRP Single Asset Vault owned by the broker wallet."""
    print(f"\nCreating SAV (owner: {broker_wallet.address})...")

    tx = VaultCreate(
        account=broker_wallet.address,
        asset={"currency": "XRP"},
        assets_maximum="0",  # no cap
        withdrawal_policy=WithdrawalPolicy.VAULT_STRATEGY_FIRST_COME_FIRST_SERVE,
    )
    response = submit_and_wait(tx, client, broker_wallet, autofill=True)
    require_success(response, "VaultCreate")

    node = created_node(response, "Vault")
    vault_id = node["LedgerIndex"]
    share_mpt_id = node["NewFields"]["ShareMPTID"]

    print(f"  Vault ID     : {vault_id}")
    print(f"  Share MPT ID : {share_mpt_id}")
    print(f"  Explorer     : {DEVNET}/ledger-objects/{vault_id}")
    return {"vault_id": vault_id, "share_mpt_id": share_mpt_id}