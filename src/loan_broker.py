import sys
import time

from xrpl.core.binarycodec import encode_for_signing, encode
from xrpl.core.keypairs import sign as keypairs_sign
from xrpl.models import LoanBrokerSet, LoanSet, LoanPay
from xrpl.models.requests import Submit, Tx
from xrpl.transaction import submit_and_wait, autofill, sign, sign_loan_set_by_counterparty
from xrpl.utils import xrp_to_drops

from demo_config import client, DEVNET
from utils import require_success, created_node

def setup_loan_broker(broker_wallet, vault_id: str) -> str:
    """
    Registers a LoanBroker on-chain, linked to the given vault.
    Only the vault owner can call this.
    Returns the loan_broker_id.
    """
    print(f"\nRegistering LoanBroker for vault {vault_id}...")

    tx = LoanBrokerSet(
        account=broker_wallet.address,
        vault_id=vault_id,
    )
    response = submit_and_wait(tx, client, broker_wallet, autofill=True)
    require_success(response, "LoanBrokerSet")

    broker_id = created_node(response, "LoanBroker")["LedgerIndex"]
    print(f"  LoanBroker ID : {broker_id}")
    print(f"  Explorer      : {DEVNET}/ledger-objects/{broker_id}")
    return broker_id

