# data_generator/search_index.py

import os
from typing import List, Optional, Dict, Any

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchField,
    SearchableField,
    VectorSearch,
    VectorSearchProfile,
    HnswAlgorithmConfiguration,
    VectorSearchAlgorithmKind,
    VectorSearchAlgorithmMetric,
    AzureOpenAIVectorizer,
    AzureOpenAIVectorizerParameters,
    SearchIndexerDataUserAssignedIdentity,
)

from openai import AzureOpenAI


# ============================================================
# Embedding Client (Azure OpenAI) – App-side vectors
# ============================================================

class EmbeddingClient:
    """
    Thin wrapper around Azure OpenAI embeddings.

    Pattern:
    - App-generated embeddings (stored in Azure AI Search as content_vector)
    - Server-side vectorizer configured (my-vectorizer) for query-time vectorization if desired
    """

    def __init__(self):
        self.client = AzureOpenAI(
            azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
            api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
            api_key=os.environ["AZURE_OPENAI_API_KEY"],
        )
        self.deployment = os.environ["AZURE_OPENAI_EMBEDDING_DEPLOYMENT"]

    def embed(self, texts: List[str]) -> List[List[float]]:
        response = self.client.embeddings.create(
            model=self.deployment,
            input=texts,
        )
        return [item.embedding for item in response.data]


# ============================================================
# Azure AI Search Index Wrapper (Audit Policy Snippets)
# ============================================================

class AuditPolicySearchIndex:
    """
    Azure AI Search wrapper supporting:
    - Hybrid (keyword + vector) search
    - Explicit embeddings (app-side) stored in content_vector
    - ALSO configures AzureOpenAIVectorizer ("my-vectorizer") for server-side query vectorization
    """

    # Default: text-embedding-3-large dimensions
    VECTOR_DIMENSIONS = int(os.environ.get("SEARCH_VECTOR_DIMENSIONS", "3072"))

    def __init__(self):
        self.endpoint = os.environ["SEARCH_ENDPOINT"]
        self.index_name = os.environ["SEARCH_INDEX"]
        self.api_key = os.environ["SEARCH_API_KEY"]

        credential = AzureKeyCredential(self.api_key)

        self.index_client = SearchIndexClient(
            endpoint=self.endpoint,
            credential=credential,
        )

        self.search_client = SearchClient(
            endpoint=self.endpoint,
            index_name=self.index_name,
            credential=credential,
        )

        # App-side embedder (for storing vectors with docs)
        self.embedder = EmbeddingClient()

    # --------------------------------------------------------
    # Index Management
    # --------------------------------------------------------

    def create_index_if_not_exists(self) -> None:
        existing_indexes = [idx.name for idx in self.index_client.list_indexes()]
        if self.index_name in existing_indexes:
            print(f"ℹ️ Search index '{self.index_name}' already exists")
            return

        fields = [
            SimpleField(name="id", type="Edm.String", key=True),

            # Filters / scope
            SimpleField(name="doc_type", type="Edm.String", filterable=True, sortable=True),
            SimpleField(name="engagement_id", type="Edm.String", filterable=True),

            # Policy metadata for citations
            SimpleField(name="policy_id", type="Edm.String", filterable=True),
            SimpleField(name="section", type="Edm.String", filterable=True),
            SimpleField(name="effective_date", type="Edm.String", filterable=True, sortable=True),

            # Content + vector
            SearchableField(name="content", type="Edm.String", analyzer_name="en.lucene"),
            SearchField(
                name="content_vector",
                type="Collection(Edm.Single)",
                vector_search_dimensions=self.VECTOR_DIMENSIONS,
                vector_search_profile_name="vector-profile",
            ),
        ]

        vector_search = VectorSearch(
            algorithms=[
                HnswAlgorithmConfiguration(
                    name="hnsw-config",
                    kind=VectorSearchAlgorithmKind.HNSW,
                    metric=VectorSearchAlgorithmMetric.COSINE,
                )
            ],
            profiles=[
                VectorSearchProfile(
                    name="vector-profile",
                    algorithm_configuration_name="hnsw-config",
                    # IMPORTANT: Keep this so server-side vectorization is enabled
                    vectorizer_name="my-vectorizer",
                )
            ],
            # ✅ DO NOT REMOVE: server-side vectorizer definition
            vectorizers=[
                AzureOpenAIVectorizer(
                    vectorizer_name="my-vectorizer",
                    kind="azureOpenAI",
                    parameters=AzureOpenAIVectorizerParameters(
                        resource_url=os.environ["AZURE_OPENAI_ENDPOINT"],
                        deployment_name=os.environ["AZURE_OPENAI_EMBEDDING_DEPLOYMENT"],
                        model_name=os.environ["AZURE_OPENAI_EMBEDDING_DEPLOYMENT"],
                        auth_identity=SearchIndexerDataUserAssignedIdentity(
                            odata_type="#Microsoft.Azure.Search.DataUserAssignedIdentity",
                            resource_id=str(os.environ["AZURE_CLIENT_RESOURCE_ID"]),
                        ),
                    ),
                )
            ],
        )

        index = SearchIndex(
            name=self.index_name,
            fields=fields,
            vector_search=vector_search,
        )

        self.index_client.create_index(index)
        print(f"✅ Created Azure AI Search index '{self.index_name}'")

    # --------------------------------------------------------
    # Document Ingestion (App-side vectors)
    # --------------------------------------------------------

    def upload_documents(self, documents: List[Dict[str, Any]]) -> None:
        """
        Upload policy snippet documents to the search index with embeddings.

        Expected document format:
        {
            "id": str,
            "doc_type": "policy_snippet",
            "engagement_id": str,
            "policy_id": str,
            "section": str,
            "effective_date": str,
            "content": str
        }
        """
        if not documents:
            return

        texts = [doc["content"] for doc in documents]
        embeddings = self.embedder.embed(texts)

        enriched_docs = [
            {
                "id": doc["id"],
                "doc_type": doc.get("doc_type", "policy_snippet"),
                "engagement_id": doc["engagement_id"],
                "policy_id": doc.get("policy_id"),
                "section": doc.get("section"),
                "effective_date": doc.get("effective_date"),
                "content": doc["content"],
                # App-side vectors stored explicitly
                "content_vector": vector,
            }
            for doc, vector in zip(documents, embeddings)
        ]

        result = self.search_client.upload_documents(documents=enriched_docs)

        failed = [r for r in result if not r.succeeded]
        if failed:
            raise RuntimeError(f"❌ Failed to index {len(failed)} documents")

        print(f"✅ Indexed {len(enriched_docs)} documents into '{self.index_name}'")

    # --------------------------------------------------------
    # Hybrid Search (Query-time vectorization options)
    # --------------------------------------------------------

    def search(
        self,
        query: str,
        engagement_id: Optional[str] = None,
        top: int = 5,
        use_server_vectorizer: bool = True,
    ) -> List[dict]:
        """
        Perform hybrid keyword + vector search.

        Two modes:
        - use_server_vectorizer=True:
            Uses the server-side AzureOpenAIVectorizer ("my-vectorizer") to embed the query.
            Your stored document vectors (content_vector) are still used for ANN matching.
        - use_server_vectorizer=False:
            App generates the query embedding using EmbeddingClient.embed().

        NOTE:
        - Server-side vectorizer requires a compatible azure-search-documents SDK that supports
          VectorizableTextQuery. If not available in your environment, set use_server_vectorizer=False.
        """
        filter_expr = f"engagement_id eq '{engagement_id}'" if engagement_id else None

        # Prefer server-side vectorizer (query-time embedding done by Search)
        if use_server_vectorizer:
            try:
                from azure.search.documents.models import VectorizableTextQuery

                vector_queries = [
                    VectorizableTextQuery(
                        text=query,
                        k=top,
                        fields="content_vector",
                        vectorizer="my-vectorizer",
                    )
                ]
            except Exception:
                # Fall back to app-side if SDK doesn't support VectorizableTextQuery
                use_server_vectorizer = False

        if not use_server_vectorizer:
            query_vector = self.embedder.embed([query])[0]
            vector_queries = [
                {
                    "vector": query_vector,
                    "k": top,
                    "fields": "content_vector",
                }
            ]

        results = self.search_client.search(
            search_text=query,
            filter=filter_expr,
            vector_queries=vector_queries,
            top=top,
        )

        return [
            {
                "id": r.get("id"),
                "doc_type": r.get("doc_type"),
                "engagement_id": r.get("engagement_id"),
                "policy_id": r.get("policy_id"),
                "section": r.get("section"),
                "effective_date": r.get("effective_date"),
                "content": r.get("content"),
                "score": r.get("@search.score"),
            }
            for r in results
        ]
