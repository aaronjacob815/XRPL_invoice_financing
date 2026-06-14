from xrpl.utils import encode_mptoken_metadata
from xrpl.models.transactions import (
    MPTokenIssuanceCreate,
    MPTokenIssuanceCreateFlag
)
from xrpl.transaction import submit_and_wait
from xrpl.wallet import generate_faucet_wallet

from demo_config import client, DEVNET
from utils import require_success


# Bitmasks for token permissions — immutable after creation
INVOICE_FLAGS = (
    MPTokenIssuanceCreateFlag.TF_MPT_CAN_TRANSFER
    | MPTokenIssuanceCreateFlag.TF_MPT_CAN_TRADE
)


def create_invoice(company_wallet, invoice_data: dict) -> str:
    """
    Company mints an MPToken representing an unpaid invoice.

    invoice_data = {
        "invoice_id":  "INV-2026-0001",
        "face_value":  10000,
        "currency":    "RLUSD",
        "due_date":    "2026-09-01",
        "description": "Web development services"
    }

    Returns the mpt_issuance_id string.
    """
    print(f"\n=== Company minting invoice token ===")
    print(f"  Company  : {company_wallet.classic_address}")
    print(f"  Invoice  : {invoice_data['invoice_id']}")
    print(f"  Value    : {invoice_data['face_value']} {invoice_data['currency']}")
    print(f"  Due date : {invoice_data['due_date']}")

    # Build metadata — publicly visible on chain
    mpt_metadata = {
    "schema":       "invoice/v1",
    "n":            f"Invoice {invoice_data['invoice_id']}",  # name
    "t":            "INV",                                     # ticker
    "i":            "https://ukfinnovators.com/icon.png",      # icon
    "in":           "UKFinnovators Platform",                  # issuer_name
    "as":           "invoice",                                 # asset_subclass
    "invoice_id":   invoice_data["invoice_id"],
    "debtor":       company_wallet.classic_address,
    "face_value":   invoice_data["face_value"],
    "currency":     invoice_data["currency"],
    "issue_date":   invoice_data.get("issue_date", "2026-06-14"),
    "due_date":     invoice_data["due_date"],
    "description":  invoice_data.get("description", ""),
    "asset_class":  "rwa"
}
    tx = MPTokenIssuanceCreate(
        account=company_wallet.classic_address,
        asset_scale=0,        # 1 unit = 1 whole invoice claim
        maximum_amount="1",   # only 1 invoice token ever exists
        transfer_fee=0,       # no cut on transfers
        flags=INVOICE_FLAGS,
        mptoken_metadata=encode_mptoken_metadata(mpt_metadata),
    )

    print("\nSubmitting MPTokenIssuanceCreate...")
    response = submit_and_wait(tx, client, company_wallet, autofill=True)
    require_success(response, "MPTokenIssuanceCreate")

    issuance_id = response.result["meta"]["mpt_issuance_id"]

    print(f"\nInvoice token created successfully :: ")
    print(f"  MPTokenIssuanceID : {issuance_id}")
    print(f"  Explorer          : {DEVNET}/mpt/{issuance_id}")

    return issuance_id


# ── Standalone test ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Creating company wallet...")
    company = generate_faucet_wallet(client, debug=True)
    print(f"Company Address : {company.classic_address}")
    print(f"Company Seed    : {company.seed}")  # ADD THIS LINE
    print(f"Explorer: {DEVNET}/accounts/{company.classic_address}")

    invoice_data = {
        "invoice_id":  "INV-2026-0001",
        "face_value":  10000,
        "currency":    "RLUSD",
        "issue_date":  "2026-06-14",
        "due_date":    "2026-09-01",
        "description": "Web development services - UKFinnovator project"
    }

    mpt_id = create_invoice(company, invoice_data)
    print(f"\nMPTokenIssuanceID: {mpt_id}")
    print(f"Company seed: {company.seed}")  # AND THIS LINE
