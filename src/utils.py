import sys


def require_success(response, label: str):
    result = response.result["meta"]["TransactionResult"]
    if result != "tesSUCCESS":
        print(f"Error: {label} failed with {result}", file=sys.stderr)
        sys.exit(1)


def created_node(response, ledger_entry_type: str) -> dict:
    return next(
        node["CreatedNode"]
        for node in response.result["meta"]["AffectedNodes"]
        if "CreatedNode" in node
        and node["CreatedNode"]["LedgerEntryType"] == ledger_entry_type
    )