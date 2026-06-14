from xrpl.clients import JsonRpcClient
from xrpl.utils import encode_mptoken_metadata, decode_mptoken_metadata
from xrpl.models.transactions import (
    MPTokenIssuanceCreate,
    MPTokenIssuanceCreateFlag
)
from xrpl.transaction import submit_and_wait
from xrpl.wallet import Wallet, generate_faucet_wallet
from xrpl.core import addresscodec
from xrpl.models.requests.account_info import AccountInfo
import json

# Connection to testnet ledger
JSON_RPC_URL = "https://s.altnet.rippletest.net:51234/"
client = JsonRpcClient(JSON_RPC_URL)

# Get account w money from faucet
print("\nMaking wallet to simulate company: \n")
company = generate_faucet_wallet(client, debug = True)
company_account = company.classic_address
print(f" https://testnet.xrpl.org/accounts/{company_account}") #to get account testnet explorer url

# Bitmasks, so I'm ORing each. Switches on a token's permissions. Immutable after creation. Clawback allows issuer to take back?
INVOICE_FLAGS = (
    MPTokenIssuanceCreateFlag.TF_MPT_CAN_TRANSFER
    | MPTokenIssuanceCreateFlag.TF_MPT_CAN_TRADE
    | MPTokenIssuanceCreateFlag.TF_MPT_CAN_CLAWBACK
)

# Metadata for an example token, note that it can't be updated after creation, and is all publicly visible. NOT FINALISED.
mpt_metadata = {
  "schema": "invoice/v1",
  "invoice_id": "INV-2026-0001",
  "debtor":    "rCompany...",
  "payee":     "rFreelancer...",
  "face_value": 2000,
  "currency":  "RLUSD",
  "issue_date":"2026-06-14",
  "due_date":  "2026-07-14",
  "asset_class": "rwa"     # real world asset
}

# Token fields
mpt_issuance_create = MPTokenIssuanceCreate(
    account=company.classic_address,   # WHO issues = the debtor company
    asset_scale=0,                     # decimal places: 0 → 1 unit = 1 whole RLUSD of claim
    maximum_amount="1",             # total units that can exist. Change to 2000 if we extend to make invoices divisible!
    transfer_fee=0,                    # issuer doesn't skim a cut on transfers
    flags = INVOICE_FLAGS,                      # the token's permanent permissions (below)
    mptoken_metadata = encode_mptoken_metadata(mpt_metadata),            # the invoice details, as hex-encoded JSON
)

# Sign and submit the transaction
print("\n=== Sending MPTokenIssuanceCreate transaction...===")
response = submit_and_wait(mpt_issuance_create, client, company, autofill=True)

# Check if it worked
print("\n=== Checking MPTokenIssuanceCreate results... ===")
result_code = response.result["meta"]["TransactionResult"]
if result_code != "tesSUCCESS":
    print(f"Transaction failed with result code {result_code}.")
    exit(1)

issuance_id = response.result["meta"]["mpt_issuance_id"]
print(f"\n- MPToken created successfully with issuance ID: {issuance_id}")
print(f"- Explorer URL: https://testnet.xrpl.org/mpt/{issuance_id}")