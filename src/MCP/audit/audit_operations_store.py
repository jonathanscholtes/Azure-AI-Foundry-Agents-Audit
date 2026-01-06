import os
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta, timezone

from azure.cosmos.aio import CosmosClient
from azure.identity.aio import DefaultAzureCredential
from dotenv import load_dotenv

load_dotenv(override=True)



def _normalize_start_iso(d: Optional[str]) -> Optional[str]:
    """
    Accepts:
      - None / ""
      - "YYYY-MM-DD"
      - "YYYY-MM-DDTHH:MM:SSZ"
    Returns:
      - ISO UTC string with 'Z'
    """
    if not d:
        return None
    if "T" in d:
        return d.replace("+00:00", "Z")
    return f"{d}T00:00:00Z"


def _normalize_end_exclusive_iso(d: Optional[str]) -> Optional[str]:
    """
    Accepts:
      - None / ""
      - "YYYY-MM-DD"  -> next day midnight (exclusive)
      - full ISO      -> used as-is (assumed exclusive)
    """
    if not d:
        return None
    if "T" in d:
        return d.replace("+00:00", "Z")

    dt = datetime.fromisoformat(d).replace(tzinfo=timezone.utc) + timedelta(days=1)
    return dt.isoformat().replace("+00:00", "Z")



class AuditOperationsStore:
    """
    Async Cosmos store for the audit PoC.

    Containers:
      - vendors
      - invoices
      - payments
    """

    def __init__(self):
        self._endpoint = os.getenv("COSMOS_ENDPOINT")
        self._db_name = os.getenv("COSMOS_DATABASE")

        if not self._endpoint or not self._db_name:
            raise ValueError("COSMOS_ENDPOINT and COSMOS_DATABASE must be set")

        self._client: Optional[CosmosClient] = None
        self._credential: Optional[DefaultAzureCredential] = None
        self._database = None
        self._containers: Dict[str, Any] = {}

    async def _ensure_client(self):
        if self._client is None:
            self._credential = DefaultAzureCredential()
            self._client = CosmosClient(self._endpoint, credential=self._credential)
            self._database = self._client.get_database_client(self._db_name)

    async def _get_container(self, name: str):
        await self._ensure_client()
        if name not in self._containers:
            self._containers[name] = self._database.get_container_client(name)
        return self._containers[name]


    async def get_invoice(self, engagement_id: str, invoice_id: str) -> Optional[Dict]:
        container = await self._get_container("invoices")

        query = """
        SELECT TOP 1 * FROM c
        WHERE c.engagement_id = @engagement_id
          AND c.invoice_id = @invoice_id
        """
        params = [
            {"name": "@engagement_id", "value": engagement_id},
            {"name": "@invoice_id", "value": invoice_id},
        ]

        async for item in container.query_items(query=query, parameters=params):
            return item
        return None

    async def get_vendor(self, engagement_id: str, vendor_id: str) -> Optional[Dict]:
        container = await self._get_container("vendors")

        query = """
        SELECT TOP 1 * FROM c
        WHERE c.engagement_id = @engagement_id
          AND c.vendor_id = @vendor_id
        """
        params = [
            {"name": "@engagement_id", "value": engagement_id},
            {"name": "@vendor_id", "value": vendor_id},
        ]

        async for item in container.query_items(query=query, parameters=params):
            return item
        return None

    async def get_payment(self, engagement_id: str, payment_id: str) -> Optional[Dict]:
        container = await self._get_container("payments")

        query = """
        SELECT TOP 1 * FROM c
        WHERE c.engagement_id = @engagement_id
          AND c.payment_id = @payment_id
        """
        params = [
            {"name": "@engagement_id", "value": engagement_id},
            {"name": "@payment_id", "value": payment_id},
        ]

        async for item in container.query_items(query=query, parameters=params):
            return item
        return None

    async def get_payments_for_invoice(
        self, engagement_id: str, invoice_id: str
    ) -> List[Dict]:
        container = await self._get_container("payments")

        query = """
        SELECT * FROM c
        WHERE c.engagement_id = @engagement_id
          AND c.invoice_id = @invoice_id
        """
        params = [
            {"name": "@engagement_id", "value": engagement_id},
            {"name": "@invoice_id", "value": invoice_id},
        ]

        results: List[Dict] = []
        async for item in container.query_items(query=query, parameters=params):
            results.append(item)
        return results


    async def query_invoices(
        self,
        engagement_id: str,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        vendor_id: Optional[str] = None,
        status: Optional[str] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        limit: int = 200,
    ) -> List[Dict]:
        container = await self._get_container("invoices")

        df = _normalize_start_iso(date_from)
        dt = _normalize_end_exclusive_iso(date_to)

        where = ["c.engagement_id = @engagement_id"]
        params = [{"name": "@engagement_id", "value": engagement_id}]

        if df:
            where.append("c.invoice_date >= @date_from")
            params.append({"name": "@date_from", "value": df})

        if dt:
            where.append("c.invoice_date < @date_to")
            params.append({"name": "@date_to", "value": dt})

        if vendor_id:
            where.append("c.vendor_id = @vendor_id")
            params.append({"name": "@vendor_id", "value": vendor_id})

        if status:
            where.append("c.status = @status")
            params.append({"name": "@status", "value": status})

        if min_amount is not None:
            where.append("c.amount >= @min_amount")
            params.append({"name": "@min_amount", "value": float(min_amount)})

        if max_amount is not None:
            where.append("c.amount <= @max_amount")
            params.append({"name": "@max_amount", "value": float(max_amount)})

        query = f"""
        SELECT * FROM c
        WHERE {' AND '.join(where)}
        OFFSET 0 LIMIT {int(limit)}
        """

        results: List[Dict] = []
        async for item in container.query_items(query=query, parameters=params):
            results.append(item)
        return results

    async def query_payments(
        self,
        engagement_id: str,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        vendor_id: Optional[str] = None,
        invoice_id: Optional[str] = None,
        limit: int = 200,
    ) -> List[Dict]:
        container = await self._get_container("payments")

        df = _normalize_start_iso(date_from)
        dt = _normalize_end_exclusive_iso(date_to)

        where = ["c.engagement_id = @engagement_id"]
        params = [{"name": "@engagement_id", "value": engagement_id}]

        if df:
            where.append("c.paid_at >= @date_from")
            params.append({"name": "@date_from", "value": df})

        if dt:
            where.append("c.paid_at < @date_to")
            params.append({"name": "@date_to", "value": dt})

        if vendor_id:
            where.append("c.vendor_id = @vendor_id")
            params.append({"name": "@vendor_id", "value": vendor_id})

        if invoice_id:
            where.append("c.invoice_id = @invoice_id")
            params.append({"name": "@invoice_id", "value": invoice_id})

        query = f"""
        SELECT * FROM c
        WHERE {' AND '.join(where)}
        OFFSET 0 LIMIT {int(limit)}
        """

        results: List[Dict] = []
        async for item in container.query_items(query=query, parameters=params):
            results.append(item)
        return results

    async def query_vendors(
        self,
        engagement_id: str,
        risk_tier: str = "",
        limit: int = 200,
    ) -> List[Dict[str, Any]]:
        container = await self._get_container("vendors")

        where = ["c.engagement_id = @engagement_id"]
        params = [{"name": "@engagement_id", "value": engagement_id}]

        if risk_tier:
            where.append("c.risk_tier = @risk_tier")
            params.append({"name": "@risk_tier", "value": risk_tier})

        query = f"""
        SELECT * FROM c
        WHERE {' AND '.join(where)}
        OFFSET 0 LIMIT {int(limit)}
        """

        results: List[Dict[str, Any]] = []
        async for item in container.query_items(query=query, parameters=params):
            results.append(item)
        return results