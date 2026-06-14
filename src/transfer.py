from xrpl.models.transactions import MPTokenAuthorize, Payment
from xrpl.models.amounts.mpt_amount import MPTAmount
from xrpl.transaction import submit_and_wait
from xrpl.wallet import generate_faucet_wallet

from demo_config import client, DEVNET
from utils import require_success


def transfer_invoice_to_freelancer(
    company_wallet,
    freelancer_wallet,
    mpt_issuance_id: str
) -> str:
    """
    Step 1: Freelancer authorizes their wallet to hold the invoice token
    Step 2: Company sends the invoice token to the freelancer
    Returns transaction hash
    """
    print(f"\n=== Transferring invoice token to freelancer ===")
    print(f"  From     : {company_wallet.classic_address}")
    print(f"  To       : {freelancer_wallet.classic_address}")
    print(f"  Token ID : {mpt_issuance_id}")

    # Step 1 — freelancer opts in to hold this token
    print("\nFreelancer authorizing token hold...")
    auth_tx = MPTokenAuthorize(
        account=freelancer_wallet.classic_address,
        mptoken_issuance_id=mpt_issuance_id,
    )
    response = submit_and_wait(auth_tx, client, freelancer_wallet, autofill=True)
    require_success(response, "MPTokenAuthorize")
    print(f"  Authorized: {DEVNET}/transactions/{response.result['hash']}")

    # Step 2 — company sends invoice token to freelancer
    print("\nCompany sending invoice token...")
    payment_tx = Payment(
        account=company_wallet.classic_address,
        destination=freelancer_wallet.classic_address,
        amount=MPTAmount(
            mpt_issuance_id=mpt_issuance_id,
            value="1"
        )
    )
    response = submit_and_wait(payment_tx, client, company_wallet, autofill=True)
    require_success(response, "Payment")

    tx_hash = response.result['hash']
    print(f"  Token sent to freelancer")
    print(f"  Explorer: {DEVNET}/transactions/{tx_hash}")

    return tx_hash


# ── Standalone test ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    from invoice_token import create_invoice

    # Step 1 — create fresh company wallet
    print("Creating company wallet...")
    company_wallet = generate_faucet_wallet(client, debug=True)
    print(f"Company Address : {company_wallet.classic_address}")
    print(f"Company Seed    : {company_wallet.seed}")

    # Step 2 — mint invoice token with that wallet
    invoice_data = {
        "invoice_id":  "INV-2026-0001",
        "face_value":  10000,
        "currency":    "RLUSD",
        "issue_date":  "2026-06-14",
        "due_date":    "2026-09-01",
        "description": "Web development services"
    }
    mpt_id = create_invoice(company_wallet, invoice_data)

    # Step 3 — create freelancer wallet
    print("\nCreating freelancer wallet...")
    freelancer_wallet = generate_faucet_wallet(client, debug=True)
    print(f"Freelancer Address : {freelancer_wallet.classic_address}")
    print(f"Freelancer Seed    : {freelancer_wallet.seed}")

    # Step 4 — transfer token to freelancer
    tx_hash = transfer_invoice_to_freelancer(
        company_wallet,
        freelancer_wallet,
        mpt_id
    )

    print(f"\n✅ Transfer complete")
    print(f"Save these for next step:")
    print(f"  Freelancer seed : {freelancer_wallet.seed}")
    print(f"  MPTokenIssuanceID : {mpt_id}")