from xrpl.models.transactions import Payment, MPTokenAuthorize
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.models.amounts.mpt_amount import MPTAmount
from xrpl.transaction import submit_and_wait
from xrpl.models.requests import AccountLines


from demo_config import client, DEVNET
from utils import require_success

RLUSD_CURRENCY = "524C555344000000000000000000000000000000"


def broker_authorize_token(broker_wallet, mpt_issuance_id: str):
    """Broker opts in to hold the invoice token."""
    print(f"\nBroker authorizing invoice token...")
    auth_tx = MPTokenAuthorize(
        account=broker_wallet.classic_address,
        mptoken_issuance_id=mpt_issuance_id,
    )
    r = submit_and_wait(auth_tx, client, broker_wallet, autofill=True)
    require_success(r, "Broker MPTokenAuthorize")
    print(f"  Broker authorized: {DEVNET}/transactions/{r.result['hash']}")


def freelancer_sells_to_broker(
    freelancer_wallet,
    broker_wallet,
    mpt_issuance_id: str,
    face_value: float,
    issuer_address: str,
    discount_pct: float = 0.05
) -> str:
    """
    Marketplace swap:
    - Freelancer sends invoice token to broker
    - Broker sends RLUSD to freelancer instantly
    Returns RLUSD payment transaction hash.
    """
    loan_amount = face_value * (1 - discount_pct)

    print(f"\n=== Marketplace Swap ===")
    print(f"  Invoice face value : {face_value} RLUSD")
    print(f"  Discount           : {discount_pct * 100}%")
    print(f"  Freelancer gets    : {loan_amount} RLUSD now")

    # Step 1 — freelancer sends invoice token to broker
    print("\nFreelancer sending invoice token to broker...")
    token_payment = Payment(
        account=freelancer_wallet.classic_address,
        destination=broker_wallet.classic_address,
        amount=MPTAmount(
            mpt_issuance_id=mpt_issuance_id,
            value="1"
        )
    )
    r = submit_and_wait(token_payment, client, freelancer_wallet, autofill=True)
    require_success(r, "Token Transfer to Broker")
    print(f"  ✅ Invoice token sent to broker")
    print(f"  Explorer: {DEVNET}/transactions/{r.result['hash']}")

	# Debug — check balances before payment
    print("\nChecking balances...")
    check_rlusd_balance(broker_wallet.classic_address, "Broker", issuer_address)
    check_rlusd_balance(freelancer_wallet.classic_address, "Freelancer", issuer_address)
    print(f"\nDEBUG issuer_address passed in: {issuer_address}")

    # Step 2 — broker sends RLUSD to freelancer
    print("\nBroker paying freelancer in RLUSD...")
    rlusd_payment = Payment(
        account=broker_wallet.classic_address,
        destination=freelancer_wallet.classic_address,
        amount=IssuedCurrencyAmount(
            currency=RLUSD_CURRENCY,
            issuer=issuer_address,
            value=str(loan_amount)
        )
    )
    r = submit_and_wait(rlusd_payment, client, broker_wallet, autofill=True)
    require_success(r, "RLUSD Payment to Freelancer")

    tx_hash = r.result['hash']
    print(f"  ✅ Freelancer received {loan_amount} RLUSD instantly")
    print(f"  Explorer: {DEVNET}/transactions/{tx_hash}")

    return tx_hash


def company_pays_broker(
    company_wallet,
    broker_wallet,
    issuer_address: str,
    face_value: float
) -> str:
    """Company pays full invoice amount to broker at maturity."""
    print(f"\n=== Company Pays Broker at Maturity ===")

    final_payment = Payment(
        account=company_wallet.classic_address,
        destination=broker_wallet.classic_address,
        amount=IssuedCurrencyAmount(
            currency=RLUSD_CURRENCY,
            issuer=issuer_address,
            value=str(face_value)
        )
    )
    r = submit_and_wait(final_payment, client, company_wallet, autofill=True)
    require_success(r, "Company Final Payment")

    tx_hash = r.result['hash']
    print(f"  Broker received {face_value} RLUSD from company")
    print(f"  Explorer: {DEVNET}/transactions/{tx_hash}")

    return tx_hash


def check_rlusd_balance(address, name, issuer_address):
    request = AccountLines(account=address)
    response = client.request(request)
    lines = response.result.get("lines", [])
    found = False
    for line in lines:
        print(f"  {name} trust line → issuer: {line['account']} balance: {line['balance']}")
        if line["account"] == issuer_address:
            found = True
    if not found:
        print(f"  {name} has NO trust line to issuer {issuer_address}")