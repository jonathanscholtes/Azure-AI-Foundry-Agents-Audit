#!/usr/bin/env python3
import random
from datetime import datetime, timedelta, timezone
from typing import List
from dotenv import load_dotenv

from cosmos_store import CosmosStore
from search_index import AuditPolicySearchIndex  # your new wrapper for AI Search

# -------------------------------------------------------------------
# ENV / SEED
# -------------------------------------------------------------------
load_dotenv()
random.seed(42)

# -------------------------------------------------------------------
# POLICY SNIPPET TEMPLATE (RAG DOCUMENT)
# -------------------------------------------------------------------
POLICY_TEMPLATE = """\
Policy: {policy_name}
Section: {section}
Effective Date: {effective_date}

{content}
"""

def generate_policy_doc(engagement_id: str, policy: dict) -> dict:
   
    section_key = str(policy["section_id"]).replace(".", "-")

    return {
        "id": f"doc-policy-{engagement_id}-{policy['policy_id']}-{section_key}",
        "doc_type": "policy_snippet",
        "engagement_id": engagement_id,
        "policy_id": policy["policy_id"],
        "section": policy["section_title"],  # keep human-readable title here
        "effective_date": policy["effective_date"],
        "content": POLICY_TEMPLATE.format(
            policy_name=policy["policy_name"],
            section=policy["section_title"],
            effective_date=policy["effective_date"],
            content=policy["text"],
        ),
    }

# -------------------------------------------------------------------
# STRUCTURED DATA GENERATORS (COSMOS)
# -------------------------------------------------------------------
def utc_iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

def generate_vendors(engagement_id: str, n: int) -> List[dict]:
    names = ["Acme Supply Co", "Northwind Parts", "Fabrikam Services", "Woodgrove Logistics", "Contoso Industrial"]
    vendors = []
    for i in range(n):
        vendor_id = f"VEN-{1000+i}"
        vendors.append({
            "id": f"{engagement_id}:{vendor_id}",
            "type": "vendor",
            "engagement_id": engagement_id,
            "vendor_id": vendor_id,
            "name": random.choice(names),
            "risk_tier": random.choice(["Low", "Medium", "High"]),
            "created_at": "2024-11-15",
            "bank_account_hash": f"ba_{random.randint(10000,99999)}",
        })
    return vendors

def generate_invoices(engagement_id: str, vendors: List[dict], n: int, start: datetime) -> List[dict]:
    invoices = []
    for i in range(n):
        vendor = random.choice(vendors)
        inv_id = f"INV-{7000+i}"

        inv_date = start + timedelta(days=random.randint(0, 92))  # ~Q3 window
        amount = float(random.choice([199.99, 487.50, 1250.00, 4999.99, 5050.00, 9900.00, random.randint(300, 15000)]))

        invoices.append({
            "id": f"{engagement_id}:{inv_id}",
            "type": "invoice",
            "engagement_id": engagement_id,
            "invoice_id": inv_id,
            "vendor_id": vendor["vendor_id"],
            "invoice_date": utc_iso(inv_date.replace(tzinfo=timezone.utc)),
            "amount": amount,
            "currency": "USD",
            "po_id": f"PO-{random.randint(8000, 8999)}" if random.random() < 0.75 else None,
            "receipt_id": f"RCPT-{random.randint(9000, 9999)}" if random.random() < 0.70 else None,
            "status": random.choice(["Open", "Paid"]),
        })
    return invoices

def generate_payments(engagement_id: str, invoices: List[dict], pay_rate: float = 0.70) -> List[dict]:
    payments = []
    for inv in invoices:
        if random.random() > pay_rate:
            continue

        pay_id = f"PAY-{inv['invoice_id']}"
        inv_dt = datetime.fromisoformat(inv["invoice_date"].replace("Z", "+00:00"))
        paid_at = inv_dt + timedelta(days=random.randint(1, 60))

        payments.append({
            "id": f"{engagement_id}:{pay_id}",
            "type": "payment",
            "engagement_id": engagement_id,
            "payment_id": pay_id,
            "invoice_id": inv["invoice_id"],
            "vendor_id": inv["vendor_id"],
            "paid_at": utc_iso(paid_at),
            "amount": inv["amount"],
            "method": random.choice(["ACH", "Wire", "Check"]),
        })
    return payments

# -------------------------------------------------------------------
# ANCHOR EXCEPTIONS (DEMO GUARANTEES)
# -------------------------------------------------------------------
def inject_anchor_exceptions(engagement_id: str, vendors: List[dict], invoices: List[dict], payments: List[dict]):
    """
    Guarantee:
      1) Duplicate invoice pair (same vendor + amount + close dates)
      2) Paid invoice missing PO (classic exception)
    """
    anchor_vendor = vendors[0]["vendor_id"]

    # 1) Duplicate pair
    inv_a = {
        "id": f"{engagement_id}:INV-ANCHOR-001",
        "type": "invoice",
        "engagement_id": engagement_id,
        "invoice_id": "INV-ANCHOR-001",
        "vendor_id": anchor_vendor,
        "invoice_date": "2025-08-12T00:00:00Z",
        "amount": 4875.33,
        "currency": "USD",
        "po_id": "PO-8123",
        "receipt_id": "RCPT-9451",
        "status": "Paid",
    }

    inv_b = {
        "id": f"{engagement_id}:INV-ANCHOR-002",
        "type": "invoice",
        "engagement_id": engagement_id,
        "invoice_id": "INV-ANCHOR-002",
        "vendor_id": anchor_vendor,
        "invoice_date": "2025-08-14T00:00:00Z",
        "amount": 4875.33,
        "currency": "USD",
        "po_id": "PO-8123",
        "receipt_id": "RCPT-9451",
        "status": "Paid",
    }

    invoices.insert(0, inv_a)
    invoices.insert(1, inv_b)

    # Ensure they are paid
    payments.append({
        "id": f"{engagement_id}:PAY-INV-ANCHOR-001",
        "type": "payment",
        "engagement_id": engagement_id,
        "payment_id": "PAY-INV-ANCHOR-001",
        "invoice_id": "INV-ANCHOR-001",
        "vendor_id": anchor_vendor,
        "paid_at": "2025-08-20T00:00:00Z",
        "amount": 4875.33,
        "method": "ACH",
    })
    payments.append({
        "id": f"{engagement_id}:PAY-INV-ANCHOR-002",
        "type": "payment",
        "engagement_id": engagement_id,
        "payment_id": "PAY-INV-ANCHOR-002",
        "invoice_id": "INV-ANCHOR-002",
        "vendor_id": anchor_vendor,
        "paid_at": "2025-08-22T00:00:00Z",
        "amount": 4875.33,
        "method": "ACH",
    })

    # 2) Paid invoice missing PO
    inv_no_po = {
        "id": f"{engagement_id}:INV-ANCHOR-NOPO",
        "type": "invoice",
        "engagement_id": engagement_id,
        "invoice_id": "INV-ANCHOR-NOPO",
        "vendor_id": vendors[1]["vendor_id"],
        "invoice_date": "2025-09-05T00:00:00Z",
        "amount": 9900.00,
        "currency": "USD",
        "po_id": None,
        "receipt_id": None,
        "status": "Paid",
    }
    invoices.insert(2, inv_no_po)
    payments.append({
        "id": f"{engagement_id}:PAY-INV-ANCHOR-NOPO",
        "type": "payment",
        "engagement_id": engagement_id,
        "payment_id": "PAY-INV-ANCHOR-NOPO",
        "invoice_id": "INV-ANCHOR-NOPO",
        "vendor_id": vendors[1]["vendor_id"],
        "paid_at": "2025-09-18T00:00:00Z",
        "amount": 9900.00,
        "method": "Wire",
    })

# -------------------------------------------------------------------
# POLICY SNIPPETS (NON-TEMPLATED RAG DOCS)
# -------------------------------------------------------------------
def generate_policy_snippets(engagement_id: str) -> List[dict]:
    policies = [
        {
            "policy_id": "AP-001",
            "policy_name": "Accounts Payable Policy",
            "section_id": "3.1",
            "section_title": "Three-Way Match",
            "effective_date": "2025-01-01",
            "text": "Invoices should be matched to an approved PO and receiving record prior to payment. Exceptions require documented justification.",
        },
        {
            "policy_id": "AP-001",
            "policy_name": "Accounts Payable Policy",
            "section_id": "4.2",
            "section_title": "Duplicate Invoice Prevention",
            "effective_date": "2025-01-01",
            "text": "AP must prevent duplicate payments by checking vendor, invoice number, invoice date, and amount prior to payment release.",
        },
        {
            "policy_id": "AP-002",
            "policy_name": "Vendor Master Governance",
            "section_id": "2.3",
            "section_title": "High Risk Vendor Review",
            "effective_date": "2025-01-01",
            "text": "Vendors classified as High risk require periodic review, including validation of bank account changes and business purpose.",
        },
    ]
    return [generate_policy_doc(engagement_id, p) for p in policies]

# -------------------------------------------------------------------
# MAIN
# -------------------------------------------------------------------
def main():
    engagement_id = "eng-001"

    # One store per container (since CosmosStore is container-bound)
    vendors_store  = CosmosStore(container_name="vendors",  partition_key="/engagement_id")
    invoices_store = CosmosStore(container_name="invoices", partition_key="/engagement_id")
    payments_store = CosmosStore(container_name="payments", partition_key="/engagement_id")

    search = AuditPolicySearchIndex()

    print(" Ensuring Azure AI Search index exists...")
    search.create_index_if_not_exists()

    print(" Generating structured data...")
    start_date = datetime(2025, 7, 1, tzinfo=timezone.utc)

    vendors = generate_vendors(engagement_id, 50)
    invoices = generate_invoices(engagement_id, vendors, 400, start_date)
    payments = generate_payments(engagement_id, invoices, pay_rate=0.7)

    inject_anchor_exceptions(engagement_id, vendors, invoices, payments)

    print("⬆ Writing structured data to Cosmos DB...")
    #vendors_store.upsert_items(vendors)
    #invoices_store.upsert_items(invoices)
    #payments_store.upsert_items(payments)

    print(" Generating policy snippets (RAG docs)...")
    rag_docs = generate_policy_snippets(engagement_id)

    print(f"⬆ Indexing {len(rag_docs)} policy documents into Azure AI Search...")
    search.upload_documents(rag_docs)

    print(" Generation complete")
    print(f"Vendors: {len(vendors)}")
    print(f"Invoices: {len(invoices)}")
    print(f"Payments: {len(payments)}")
    print(f"Policy Snippets Indexed: {len(rag_docs)}")


if __name__ == "__main__":
    main()
