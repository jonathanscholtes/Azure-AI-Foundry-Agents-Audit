# src/MCP/audit/audit_operations_store.py

import os
from typing import Any, Dict, List, Optional

from azure.cosmos.aio import CosmosClient
from azure.identity.aio import DefaultAzureCredential
from dotenv import load_dotenv

load_dotenv(override=True)


class AuditOperationsStore:
    """
    Async Cosmos store supporting multiple containers.
    Intended containers (COSMOS_DATABASE = audit-poc):
      - vendors
      - invoices
      - payments
      - auditTrail (optional later)
    """

    def __init__(self):
        self._endpoint = os.getenv("COSMOS_ENDPOINT")
        self._db_name = os.getenv("COSMOS_DATABASE")

        # Optional fallback default (for backwards compatibility)
        self._default_container_name = os.getenv("COSMOS_CONTAINER")

        if not self._endpoint or not self._db_name:
            missing = [
                name
                for name, value in [
                    ("COSMOS_ENDPOINT", self._endpoint),
                    ("COSMOS_DATABASE", self._db_name),
                ]
                if not value
            ]
            raise ValueError(f"Missing environment variables: {', '.join(missing)}")

        self._client: Optional[CosmosClient] = None
        self._credential: Optional[DefaultAzureCredential] = None
        self._database = None

        # Cache container clients by name
        self._containers: Dict[str, Any] = {}

    async def _ensure_client(self):
        if self._client is None:
            self._credential = DefaultAzureCredential()
            self._client = CosmosClient(self._endpoint, credential=self._credential)
            self._database = self._client.get_database_client(self._db_name)

    async def _get_container(self, container_name: Optional[str]):
        """
        Return an async container client, cached by name.
        If container_name is None, fall back to COSMOS_CONTAINER.
        """
        await self._ensure_client()

        name = container_name or self._default_container_name
        if not name:
            raise ValueError(
                "Container name not provided and COSMOS_CONTAINER is not set. "
                "Pass container_name explicitly (e.g., 'invoices')."
            )

        if name not in self._containers:
            self._containers[name] = self._database.get_container_client(name)

        return self._containers[name]



    async def get_invoice(self, engagement_id: str, invoice_id: str) -> Optional[Dict[str, Any]]:
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

    async def get_vendor(self, engagement_id: str, vendor_id: str) -> Optional[Dict[str, Any]]:
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

    async def get_payment(self, engagement_id: str, payment_id: str) -> Optional[Dict[str, Any]]:
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

    async def get_payments_for_invoice(self, engagement_id: str, invoice_id: str) -> List[Dict[str, Any]]:
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

        results: List[Dict[str, Any]] = []
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
    ) -> List[Dict[str, Any]]:
        container = await self._get_container("invoices")

        where = ["c.engagement_id = @engagement_id"]
        params = [{"name": "@engagement_id", "value": engagement_id}]

        if date_from:
            where.append("c.invoice_date >= @date_from")
            params.append({"name": "@date_from", "value": date_from})
        if date_to:
            where.append("c.invoice_date <= @date_to")
            params.append({"name": "@date_to", "value": date_to})
        if vendor_id:
            where.append("c.vendor_id = @vendor_id")
            params.append({"name": "@vendor_id", "value": vendor_id})
        if status:
            where.append("c.status = @status")
            params.append({"name": "@status", "value": status})
        if min_amount is not None:
            where.append("c.amount >= @min_amount")
            params.append({"name": "@min_amount", "value": min_amount})
        if max_amount is not None:
            where.append("c.amount <= @max_amount")
            params.append({"name": "@max_amount", "value": max_amount})

        query = f"""
        SELECT * FROM c
        WHERE {' AND '.join(where)}
        OFFSET 0 LIMIT {int(limit)}
        """

        results: List[Dict[str, Any]] = []
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
    ) -> List[Dict[str, Any]]:
        container = await self._get_container("payments")

        where = ["c.engagement_id = @engagement_id"]
        params = [{"name": "@engagement_id", "value": engagement_id}]

        if date_from:
            where.append("c.paid_at >= @date_from")
            params.append({"name": "@date_from", "value": date_from})
        if date_to:
            where.append("c.paid_at <= @date_to")
            params.append({"name": "@date_to", "value": date_to})
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

        results: List[Dict[str, Any]] = []
        async for item in container.query_items(query=query, parameters=params):
            results.append(item)
        return results
