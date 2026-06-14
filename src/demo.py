from xrpl.wallet import generate_faucet_wallet
from xrpl.models.transactions import Payment, TrustSet
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.transaction import submit_and_wait
from xrpl.models.transactions import Payment, TrustSet, AccountSet, AccountSetAsfFlag

from demo_config import client, DEVNET
from utils import require_success
from vault import create_xrp_vault
from loan_broker import setup_loan_broker
from depositor import create_depositor, deposit_into_vault
from invoice_token import create_invoice
from transfer import transfer_invoice_to_freelancer
from marketplace import (
    broker_authorize_token,
    freelancer_sells_to_broker,
    company_pays_broker
)

RLUSD_CURRENCY = "524C555344000000000000000000000000000000"
FACE_VALUE     = 10000
DISCOUNT_PCT   = 0.05


if __name__ == "__main__":

    # ── STEP 1: BROKER CREATES VAULT ────────────────────────────────────────
    print("\n" + "="*50)
    print("STEP 1: BROKER CREATES VAULT")
    print("="*50)

    broker_wallet = generate_faucet_wallet(client, debug=False)
    print(f"  Broker   : {broker_wallet.classic_address}")
    print(f"  Explorer : {DEVNET}/accounts/{broker_wallet.classic_address}")

    vault     = create_xrp_vault(broker_wallet)
    broker_id = setup_loan_broker(broker_wallet, vault["vault_id"])

    # ── STEP 2: DEPOSITORS FUND VAULT ───────────────────────────────────────
    print("\n" + "="*50)
    print("STEP 2: DEPOSITORS FUND VAULT")
    print("="*50)

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

    # ── STEP 3: CREATE COMPANY + FREELANCER ─────────────────────────────────
    print("\n" + "="*50)
    print("STEP 3: CREATING COMPANY + FREELANCER")
    print("="*50)

    company_wallet = generate_faucet_wallet(client, debug=False)
    print(f"  Company    : {company_wallet.classic_address}")

    freelancer_wallet = generate_faucet_wallet(client, debug=False)
    print(f"  Freelancer : {freelancer_wallet.classic_address}")

    # ── STEP 4: MINT RLUSD ──────────────────────────────────────────────────
    print("\n" + "="*50)
    print("STEP 4: MINTING RLUSD")
    print("="*50)

    issuer_wallet = generate_faucet_wallet(client, debug=False)
    print(f"  Issuer : {issuer_wallet.classic_address}")

    # --- Enable Default Ripple on the Issuer ---
    print("\nEnabling Default Ripple on Issuer...")
    r_ripple = submit_and_wait(AccountSet(
        account=issuer_wallet.classic_address,
        set_flag=AccountSetAsfFlag.ASF_DEFAULT_RIPPLE
    ), client, issuer_wallet, autofill=True)
    require_success(r_ripple, "AccountSet Default Ripple")
    print("  ✅ Issuer rippling enabled")
    # -----------------------------------------------------

    # Set trust lines for ALL parties including freelancer
    for wallet, name in [
        (company_wallet,    "Company"),
        (freelancer_wallet, "Freelancer"),
        (broker_wallet,     "Broker"),
    ]:
        r = submit_and_wait(TrustSet(
            account=wallet.classic_address,
            limit_amount=IssuedCurrencyAmount(
                currency=RLUSD_CURRENCY,
                issuer=issuer_wallet.classic_address,
                value="1000000"
            )
        ), client, wallet, autofill=True)
        require_success(r, f"TrustSet {name}")
        print(f"  ✅ {name} trust line set")

    # Mint RLUSD to broker and company only
    for wallet, name, amount in [
        (broker_wallet,  "Broker",  10000),
        (company_wallet, "Company", 10000),
    ]:
        r = submit_and_wait(Payment(
            account=issuer_wallet.classic_address,
            destination=wallet.classic_address,
            amount=IssuedCurrencyAmount(
                currency=RLUSD_CURRENCY,
                issuer=issuer_wallet.classic_address,
                value=str(amount)
            )
        ), client, issuer_wallet, autofill=True)
        require_success(r, f"Mint RLUSD to {name}")
        print(f"  ✅ {name} funded with {amount} RLUSD")

    # ── STEP 5: COMPANY MINTS INVOICE TOKEN ─────────────────────────────────
    print("\n" + "="*50)
    print("STEP 5: COMPANY MINTS INVOICE TOKEN")
    print("="*50)

    invoice_data = {
        "invoice_id":  "INV-2026-0001",
        "face_value":  FACE_VALUE,
        "currency":    "RLUSD",
        "issue_date":  "2026-06-14",
        "due_date":    "2026-09-01",
        "description": "Web development services"
    }
    mpt_id = create_invoice(company_wallet, invoice_data)

    # ── STEP 6: TRANSFER TOKEN TO FREELANCER ────────────────────────────────
    print("\n" + "="*50)
    print("STEP 6: INVOICE TOKEN SENT TO FREELANCER")
    print("="*50)

    transfer_invoice_to_freelancer(company_wallet, freelancer_wallet, mpt_id)

    # ── STEP 7: MARKETPLACE SWAP ─────────────────────────────────────────────
    # ── PAUSE DEMO FOR LIVE INTERACTION ─────────────────────────────────────
    print("\n" + "="*50)
    print("DEMO PAUSED: READY FOR MARKETPLACE NEGOTIATION")
    print("="*50)

    # 1. Ask for dynamic discount rate
    while True:
        try:
            user_input = input(f"\n[DEMO] Enter Interest rate (e.g., 5 for 5%): ").strip()
            dynamic_rate = float(user_input)
            if 0 <= dynamic_rate <= 100:
                break
            else:
                print("Please enter a valid percentage between 0 and 100.")
        except ValueError:
            print("Invalid input. Please enter a number.")

    dynamic_discount_pct = dynamic_rate / 100.0
    payout_amount = FACE_VALUE * (1 - dynamic_discount_pct)
    profit_amount = FACE_VALUE * dynamic_discount_pct

    # 2. Show the deal terms
    print("\n--- Proposed Deal Summary ---")
    print(f"  Invoice Face Value : {FACE_VALUE} RLUSD")
    print(f"  Interest Rate      : {dynamic_rate}%")
    print(f"  Freelancer Gets    : {payout_amount} RLUSD instantly")
    print(f"  Broker Profit      : {profit_amount} RLUSD at maturity")

    # 3. Confirm the deal
    confirm = input("\n[DEMO] Does the Freelancer accept this deal? (Y/N): ").strip().upper()

    if confirm == 'Y':
        # ── STEP 7: MARKETPLACE SWAP ─────────────────────────────────────────────
        print("\n" + "="*50)
        print("STEP 7: EXECUTING MARKETPLACE SWAP")
        print("="*50)

        broker_authorize_token(broker_wallet, mpt_id)

        freelancer_sells_to_broker(
            freelancer_wallet=freelancer_wallet,
            broker_wallet=broker_wallet,
            mpt_issuance_id=mpt_id,
            face_value=FACE_VALUE,
            issuer_address=issuer_wallet.classic_address,
            discount_pct=dynamic_discount_pct  # Using the live input here!
        )

        # ── STEP 8: COMPANY PAYS BROKER AT MATURITY ─────────────────────────────
        print("\n" + "="*50)
        print("STEP 8: FAST FORWARD TO MATURITY")
        print("="*50)

        # Add a dramatic pause for the presentation
        input("\n[DEMO] Press ENTER to simulate 90 days passing and the Company settling the invoice...")

        company_pays_broker(
            company_wallet=company_wallet,
            broker_wallet=broker_wallet,
            issuer_address=issuer_wallet.classic_address,
            face_value=FACE_VALUE
        )

        # ── SUMMARY ──────────────────────────────────────────────────────────────
        print("\n" + "="*50)
        print("DEMO COMPLETE — FINAL SUMMARY")
        print("="*50)
        print(f"\n  Vault      : {DEVNET}/ledger-objects/{vault['vault_id']}")
        print(f"  Broker     : {DEVNET}/accounts/{broker_wallet.classic_address}")
        print(f"  Company    : {DEVNET}/accounts/{company_wallet.classic_address}")
        print(f"  Freelancer : {DEVNET}/accounts/{freelancer_wallet.classic_address}")
        print(f"  Invoice    : {DEVNET}/mpt/{mpt_id}")
        print(f"\n  Freelancer received : {payout_amount} RLUSD instantly")
        print(f"  Broker profit       : {profit_amount} RLUSD")
        print(f"  Invoice settled     : {FACE_VALUE} RLUSD")

    else:
        print("\n[DEMO] Deal rejected by Freelancer. Terminating script.")
