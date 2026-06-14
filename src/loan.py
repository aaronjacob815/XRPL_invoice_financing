import sys
import time

from xrpl.clients import JsonRpcClient
from xrpl.core.binarycodec import encode_for_signing, encode
from xrpl.core.keypairs import sign as keypairs_sign
from xrpl.models import VaultCreate, VaultDeposit, LoanBrokerSet, LoanSet, LoanPay
from xrpl.models.requests import Submit, Tx
from xrpl.models.transactions.vault_create import WithdrawalPolicy
from xrpl.transaction import submit_and_wait, autofill, sign, sign_loan_set_by_counterparty
from xrpl.utils import xrp_to_drops
from xrpl.wallet import generate_faucet_wallet

from depositor import create_depositor

from utils import require_success, created_node

from demo_config import client, DEVNET

def issue_loan(broker_id: str, broker_wallet, borrower_wallet, principal_xrp: float) -> str:
    """
    Creates a LoanSet with CounterpartySignature two-party signing.
    Both borrower and broker sign the same unsigned transaction bytes independently.
    The borrower's sig goes in SigningPubKey/TxnSignature; the broker's in CounterpartySignature.
    Returns the loan_id.
    """
    print(f"\nIssuing loan: {principal_xrp} XRP → {borrower_wallet.address}")

    tx = LoanSet(
        account=broker_wallet.address,
        loan_broker_id=broker_id,
        principal_requested=xrp_to_drops(principal_xrp),
        counterparty=borrower_wallet.address,
    )

    filled = autofill(tx, client)
    # tx_dict = filled.to_xrpl()

    print("\n=== Adding loan broker signature ===\n")
    loan_broker_signed = sign(filled, broker_wallet)

    print("\n=== Adding borrower signature ===\n")
    fully_signed = sign_loan_set_by_counterparty(borrower_wallet, loan_broker_signed)

    response = submit_and_wait(fully_signed.tx, client)
    require_success(response, "LoanSet")

    loan_id = created_node(response, "Loan")["LedgerIndex"]
    print("\n=== Created loan ===\n")
    print(f"  Loan ID  : {loan_id}")
    print(f"  Explorer : {DEVNET}/transactions/{loan_id}")
    return loan_id


def repay_loan(loan_id: str, borrower_wallet, amount_xrp: float):
    """Borrower repays some or all of an active loan."""
    print(f"\nRepaying {amount_xrp} XRP on loan {loan_id}...")

    tx = LoanPay(
        account=borrower_wallet.address,
        loan_id=loan_id,
        amount=xrp_to_drops(amount_xrp),
    )
    response = submit_and_wait(tx, client, borrower_wallet, autofill=True)
    require_success(response, "LoanPay")

    print(f"  Repayment tx : {DEVNET}/transactions/{response.result['hash']}")