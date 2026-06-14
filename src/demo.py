from xrpl.wallet import generate_faucet_wallet

from demo_config import client, DEVNET
from vault import create_xrp_vault
from loan_broker import setup_loan_broker
from loan import issue_loan, repay_loan
from depositor import create_depositor, deposit_into_vault


if __name__ == "__main__":
    # TODO: Fix URLs

    # 1. Broker wallet owns and operates the vault
    print("=== Creating broker wallet ===")
    broker_wallet = generate_faucet_wallet(client, debug=True)
    print(f"Broker: {broker_wallet.address}")

    # 2. Create the SAV and register the loan broker
    vault = create_xrp_vault(broker_wallet)
    broker_id = setup_loan_broker(broker_wallet, vault["vault_id"])

    # 3. Fund the vault with multiple depositors
    print("\n=== Depositors funding vault ===")
    depositor_configs = [
        {"name": "Alice",   "deposit_xrp": 20.0},
        {"name": "Bob",     "deposit_xrp": 35.0},
        {"name": "Charlie", "deposit_xrp": 15.0},
    ]
    for cfg in depositor_configs:
        print(f"\n--- {cfg['name']} ---")
        d = create_depositor()
        d["name"] = cfg["name"]
        deposit_into_vault(d, vault["vault_id"], cfg["deposit_xrp"])

    # 4. Borrower (e.g., a company with an invoice) takes a loan
    print("\n=== Borrower taking loan ===")
    borrower_wallet = generate_faucet_wallet(client, debug=True)
    print(f"Borrower: {borrower_wallet.address}")

    loan_id = issue_loan(broker_id, broker_wallet, borrower_wallet, principal_xrp=70.0)

    # 5. Borrower repays
    print("\n=== Repayment ===")
    repay_loan(loan_id, borrower_wallet, amount_xrp=70.0)

    print("\n=== Summary ===")
    print(f"Vault   : {DEVNET}/vault/{vault['vault_id']}")
    print(f"Broker  : {DEVNET}/account/{broker_id}")
    print(f"Loan    : {DEVNET}/ledger-objects/{loan_id}")