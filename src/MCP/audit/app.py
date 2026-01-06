# src/MCP/audit/app.py

from mcp.server.fastmcp import FastMCP
import logging
from typing import List, Dict, Optional
from os import environ
from dotenv import load_dotenv

from audit_operations_store import AuditOperationsStore  


load_dotenv(override=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastMCP(
    name="Financial Audit MCP Server",
    host="0.0.0.0",
    port=int(environ.get("MCP_PORT", 80)),
)

store = AuditOperationsStore()



@app.tool()
async def get_invoice(invoice_id: str, engagement_id: str) -> Dict:
    """
    Retrieve a SINGLE, SPECIFIC invoice by ID.

    IMPORTANT USAGE RULES:
    - Use this tool ONLY when the user/agent provides a concrete invoice ID
      (e.g., "INV-ANCHOR-001").
    - invoice_id MUST be an exact known invoice identifier.
    - Do NOT pass descriptive terms like "duplicates", "high value",
      "missing PO", or "Q3" as invoice_id.

    Returns:
    - Invoice document (structured)

    Does NOT return:
    - Lists, filtered results, or discovery/search output
    """
    logger.info(f"[get_invoice] engagement_id={engagement_id} invoice_id={invoice_id}")
    try:
        result = await store.get_invoice(engagement_id=engagement_id, invoice_id=invoice_id)
        return result or {}
    except Exception as exc:
        logger.error(
            "[get_invoice] Error | "
            f"engagement_id={engagement_id} | invoice_id={invoice_id} | "
            f"error_type={type(exc).__name__} | error_message={str(exc)}"
        )
        logger.exception("[get_invoice] Stack trace follows")
        return {}


@app.tool()
async def get_vendor(vendor_id: str, engagement_id: str) -> Dict:
    """
    Retrieve a SINGLE, SPECIFIC vendor by ID.

    IMPORTANT USAGE RULES:
    - Use ONLY when vendor_id is known (e.g., "VEN-1001").
    - Do NOT use to search vendors by name, risk tier, etc.

    Returns:
    - Vendor document (structured)
    """
    logger.info(f"[get_vendor] engagement_id={engagement_id} vendor_id={vendor_id}")
    try:
        result = await store.get_vendor(engagement_id=engagement_id, vendor_id=vendor_id)
        return result or {}
    except Exception as exc:
        logger.error(
            "[get_vendor] Error | "
            f"engagement_id={engagement_id} | vendor_id={vendor_id} | "
            f"error_type={type(exc).__name__} | error_message={str(exc)}"
        )
        logger.exception("[get_vendor] Stack trace follows")
        return {}


@app.tool()
async def get_payment(payment_id: str, engagement_id: str) -> Dict:
    """
    Retrieve a SINGLE, SPECIFIC payment by ID.

    IMPORTANT USAGE RULES:
    - Use ONLY when payment_id is known (e.g., "PAY-INV-ANCHOR-001").
    - Do NOT use for discovery ("all payments in Q3").

    Returns:
    - Payment document (structured)
    """
    logger.info(f"[get_payment] engagement_id={engagement_id} payment_id={payment_id}")
    try:
        result = await store.get_payment(engagement_id=engagement_id, payment_id=payment_id)
        return result or {}
    except Exception as exc:
        logger.error(
            "[get_payment] Error | "
            f"engagement_id={engagement_id} | payment_id={payment_id} | "
            f"error_type={type(exc).__name__} | error_message={str(exc)}"
        )
        logger.exception("[get_payment] Stack trace follows")
        return {}


@app.tool()
async def get_payments_for_invoice(invoice_id: str, engagement_id: str) -> List[Dict]:
    """
    Retrieve payment record(s) for a SINGLE, SPECIFIC invoice.

    IMPORTANT USAGE RULES:
    - Use ONLY when invoice_id is known.
    - Do NOT use to find invoices that were paid.

    Returns:
    - List of matching payment documents
    """
    logger.info(f"[get_payments_for_invoice] engagement_id={engagement_id} invoice_id={invoice_id}")
    try:
        results = await store.get_payments_for_invoice(engagement_id=engagement_id, invoice_id=invoice_id)
        return results or []
    except Exception as exc:
        logger.error(
            "[get_payments_for_invoice] Error | "
            f"engagement_id={engagement_id} | invoice_id={invoice_id} | "
            f"error_type={type(exc).__name__} | error_message={str(exc)}"
        )
        logger.exception("[get_payments_for_invoice] Stack trace follows")
        return []



@app.tool()
async def query_invoices(
    engagement_id: str,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    vendor_id: Optional[str] = None,
    status: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    limit: int = 200
) -> List[Dict]:
    """
    Search/filter invoices (DISCOVERY tool).

    Use this tool when:
    - You need to list invoices by period (e.g., Q3), vendor, status, amount range.
    - You are performing substantive tests (duplicates, missing PO/receipt, etc.)

    IMPORTANT USAGE RULES:
    - engagement_id is REQUIRED.
    - date_from/date_to should be ISO strings (e.g., "2025-07-01", "2025-09-30")
    - limit keeps the demo fast.

    Returns:
    - List of invoice documents
    """
    logger.info(
        "[query_invoices] "
        f"engagement_id={engagement_id} date_from={date_from} date_to={date_to} "
        f"vendor_id={vendor_id} status={status} min_amount={min_amount} max_amount={max_amount} limit={limit}"
    )
    try:
        results = await store.query_invoices(
            engagement_id=engagement_id,
            date_from=date_from,
            date_to=date_to,
            vendor_id=vendor_id,
            status=status,
            min_amount=min_amount,
            max_amount=max_amount,
            limit=limit,
        )
        logger.info(f"[query_invoices] Returned {len(results)} invoice(s)")
        return results or []
    except Exception as exc:
        logger.error(
            "[query_invoices] Error | "
            f"engagement_id={engagement_id} | error_type={type(exc).__name__} | error_message={str(exc)}"
        )
        logger.exception("[query_invoices] Stack trace follows")
        return []


@app.tool()
async def query_payments(
    engagement_id: str,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    vendor_id: Optional[str] = None,
    invoice_id: Optional[str] = None,
    limit: int = 200
) -> List[Dict]:
    """
    Search/filter payments (DISCOVERY tool).

    Use when you need payments by period/vendor or to reconcile payments to invoices.

    Returns:
    - List of payment documents
    """
    logger.info(
        "[query_payments] "
        f"engagement_id={engagement_id} date_from={date_from} date_to={date_to} "
        f"vendor_id={vendor_id} invoice_id={invoice_id} limit={limit}"
    )
    try:
        results = await store.query_payments(
            engagement_id=engagement_id,
            date_from=date_from,
            date_to=date_to,
            vendor_id=vendor_id,
            invoice_id=invoice_id,
            limit=limit,
        )
        logger.info(f"[query_payments] Returned {len(results)} payment(s)")
        return results or []
    except Exception as exc:
        logger.error(
            "[query_payments] Error | "
            f"engagement_id={engagement_id} | error_type={type(exc).__name__} | error_message={str(exc)}"
        )
        logger.exception("[query_payments] Stack trace follows")
        return []





if __name__ == "__main__":
    logger.info("Starting Financial Audit MCP Server...")
    logger.info(f"Service name: {environ.get('SERVICE_NAME', 'unknown')}")
    app.run(transport="streamable-http")
