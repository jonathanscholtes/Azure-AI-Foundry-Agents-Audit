from mcp.server.fastmcp import FastMCP
import logging
from typing import List, Dict
from os import environ
from dotenv import load_dotenv

from audit_operations_store import AuditOperationsStore

load_dotenv(override=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_ENGAGEMENT_ID = environ.get("DEFAULT_ENGAGEMENT_ID", "eng-001")

app = FastMCP(
    name="Financial Audit MCP Server",
    host="0.0.0.0",
    port=int(environ.get("MCP_PORT", 80)),
)

store = AuditOperationsStore()


@app.tool(name="get_invoice")
async def get_invoice(invoice_id: str, engagement_id: str = DEFAULT_ENGAGEMENT_ID) -> Dict:
    """Retrieve a SINGLE, SPECIFIC invoice by invoice_id."""
    logger.info(f"[get_invoice] engagement_id={engagement_id} invoice_id={invoice_id}")
    try:
        result = await store.get_invoice(engagement_id=engagement_id, invoice_id=invoice_id)
        return result or {}
    except Exception as exc:
        logger.error(
            "[get_invoice] Error | "
            f"engagement_id={engagement_id} invoice_id={invoice_id} "
            f"error_type={type(exc).__name__} error_message={str(exc)}"
        )
        logger.exception("[get_invoice] Stack trace follows")
        return {}


@app.tool(name="get_vendor")
async def get_vendor(vendor_id: str, engagement_id: str = DEFAULT_ENGAGEMENT_ID) -> Dict:
    """Retrieve a SINGLE, SPECIFIC vendor by vendor_id."""
    logger.info(f"[get_vendor] engagement_id={engagement_id} vendor_id={vendor_id}")
    try:
        result = await store.get_vendor(engagement_id=engagement_id, vendor_id=vendor_id)
        return result or {}
    except Exception as exc:
        logger.error(
            "[get_vendor] Error | "
            f"engagement_id={engagement_id} vendor_id={vendor_id} "
            f"error_type={type(exc).__name__} error_message={str(exc)}"
        )
        logger.exception("[get_vendor] Stack trace follows")
        return {}


@app.tool(name="get_payment")
async def get_payment(payment_id: str, engagement_id: str = DEFAULT_ENGAGEMENT_ID) -> Dict:
    """Retrieve a SINGLE, SPECIFIC payment by payment_id."""
    logger.info(f"[get_payment] engagement_id={engagement_id} payment_id={payment_id}")
    try:
        result = await store.get_payment(engagement_id=engagement_id, payment_id=payment_id)
        return result or {}
    except Exception as exc:
        logger.error(
            "[get_payment] Error | "
            f"engagement_id={engagement_id} payment_id={payment_id} "
            f"error_type={type(exc).__name__} error_message={str(exc)}"
        )
        logger.exception("[get_payment] Stack trace follows")
        return {}


@app.tool(name="get_payments_for_invoice")
async def get_payments_for_invoice(invoice_id: str, engagement_id: str = DEFAULT_ENGAGEMENT_ID) -> List[Dict]:
    """Retrieve payment record(s) for a SINGLE invoice."""
    logger.info(f"[get_payments_for_invoice] engagement_id={engagement_id} invoice_id={invoice_id}")
    try:
        results = await store.get_payments_for_invoice(engagement_id=engagement_id, invoice_id=invoice_id)
        return results or []
    except Exception as exc:
        logger.error(
            "[get_payments_for_invoice] Error | "
            f"engagement_id={engagement_id} invoice_id={invoice_id} "
            f"error_type={type(exc).__name__} error_message={str(exc)}"
        )
        logger.exception("[get_payments_for_invoice] Stack trace follows")
        return []


@app.tool(name="query_invoices")
async def query_invoices(
    date_from: str = "",
    date_to: str = "",
    vendor_id: str = "",
    status: str = "",
    min_amount: float = -1.0,
    max_amount: float = -1.0,
    limit: int = 200,
    engagement_id: str = DEFAULT_ENGAGEMENT_ID,
) -> List[Dict]:
    """Search and filter invoices for audit analysis."""
    logger.info(
        "[query_invoices] "
        f"engagement_id={engagement_id} date_from={date_from} date_to={date_to} "
        f"vendor_id={vendor_id} status={status} "
        f"min_amount={min_amount} max_amount={max_amount} limit={limit}"
    )
    try:
        results = await store.query_invoices(
            engagement_id=engagement_id,
            date_from=date_from or None,
            date_to=date_to or None,
            vendor_id=vendor_id or None,
            status=status or None,
            min_amount=None if min_amount < 0 else min_amount,
            max_amount=None if max_amount < 0 else max_amount,
            limit=limit,
        )
        return results or []
    except Exception as exc:
        logger.error(
            "[query_invoices] Error | "
            f"engagement_id={engagement_id} "
            f"error_type={type(exc).__name__} error_message={str(exc)}"
        )
        logger.exception("[query_invoices] Stack trace follows")
        return []


@app.tool(name="query_payments")
async def query_payments(
    date_from: str = "",
    date_to: str = "",
    vendor_id: str = "",
    invoice_id: str = "",
    limit: int = 200,
    engagement_id: str = DEFAULT_ENGAGEMENT_ID,
) -> List[Dict]:
    """Search and filter payments for audit procedures."""
    logger.info(
        "[query_payments] "
        f"engagement_id={engagement_id} date_from={date_from} date_to={date_to} "
        f"vendor_id={vendor_id} invoice_id={invoice_id} limit={limit}"
    )
    try:
        results = await store.query_payments(
            engagement_id=engagement_id,
            date_from=date_from or None,
            date_to=date_to or None,
            vendor_id=vendor_id or None,
            invoice_id=invoice_id or None,
            limit=limit,
        )
        return results or []
    except Exception as exc:
        logger.error(
            "[query_payments] Error | "
            f"engagement_id={engagement_id} "
            f"error_type={type(exc).__name__} error_message={str(exc)}"
        )
        logger.exception("[query_payments] Stack trace follows")
        return []



@app.tool(name="query_vendors")
async def query_vendors(
    risk_tier: str = "",
    limit: int = 200,
    engagement_id: str = DEFAULT_ENGAGEMENT_ID,
) -> List[Dict]:
    """
    Search/filter vendors.

    Use this tool to list vendors by risk tier.
    risk_tier, if provided, should be one of: Low, Medium, High.
    """
    logger.info(
        "[query_vendors] "
        f"engagement_id={engagement_id} risk_tier={risk_tier} limit={limit}"
    )
    try:
        results = await store.query_vendors(
            engagement_id=engagement_id,
            risk_tier=risk_tier,
            limit=limit,
        )
        return results or []
    except Exception as exc:
        logger.error(
            "[query_vendors] Error | "
            f"engagement_id={engagement_id} "
            f"error_type={type(exc).__name__} error_message={str(exc)}"
        )
        logger.exception("[query_vendors] Stack trace follows")
        return []


if __name__ == "__main__": 
    logger.info("Starting Financial Audit MCP Server...") 
    logger.info(f"Service name: {environ.get('SERVICE_NAME', 'unknown')}") 
    logger.info(f"Default engagement_id: {DEFAULT_ENGAGEMENT_ID}")
    app.run(transport="streamable-http")


