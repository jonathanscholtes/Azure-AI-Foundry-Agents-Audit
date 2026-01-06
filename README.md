> ⚠️  
> **This project is currently in active development and may contain breaking changes.**  
> Updates and modifications are being made frequently, which may impact stability or functionality. This notice will be removed once development is complete and the project reaches a stable release.  

# Microsoft Foundry Audit Agentic Solution

An Microsoft Foundry demo illustrating how intelligent agents can automate key Accounts Payable audit procedures by combining enterprise data, audit policy guidance, and transparent AI reasoning to accelerate audit insight generation.

## Overview

This application enables intelligent transport management through:
- **AI-powered optimization** leveraging Microsoft Foundry and agents
- **Agentic knowledge with RAG** through Azure AI Search integration providing retrieval-augmented generation capabilities
- **Scalable MCP server** with Azure Container Apps
- **Enterprise-grade infrastructure** deployed on Azure


### Features

#### AI Agent Orchestration
- Microsoft Foundry Agent Service for intelligent decision-making
- Dynamic tool calling with MCP (Model Context Protocol) remote servers
- Multi-turn conversation management
- Audit Operations MCP server for domain-specific tooling

#### Data Management
- Real-time data ingestion and processing
- Cosmos DB for distributed data storage
- Azure Storage for scalable blob and table storage
- Azure AI Search for retrieval-augmented generation (RAG) providing agentic knowledge context

#### API Services
- FastMCP server providing dynamic tool definitions
- Container-based deployment on Azure Container Apps
- MCP protocol for agent tool integration

#### Monitoring & Observability
- Application Insights integration
- Log Analytics for centralized logging
- Performance monitoring and diagnostics
- Comprehensive audit trails

---

## 📐 Architecture

![design](/media/design.png)
---


The solution is organized into modular components deployed via Infrastructure as Code (Bicep):

### Components

- **MCP Server**: FastMCP-based Transportation Operations server running on Container Apps
- **AI Services**: Microsoft Foundry Agent Service with Azure OpenAI and Azure AI Search (RAG) for agentic knowledge
- **Data Storage**: Azure Cosmos DB and Azure Storage for persistent data
- **Container Infrastructure**: Azure Container Apps for scalable deployment
- **Monitoring**: Application Insights and Log Analytics for observability
- **Security**: Azure Key Vault for secrets management and managed identities

---

## 🛠️ **Core Steps for Solution Implementation**

Follow these key steps to successfully deploy and configure the solution:

### 1️⃣ [**Deploy the Solution**](docs/deployment.md)
- Detailed instructions for deploying the solution, including prerequisites, configuration steps, and setup validation.

---

## Repo Layout (where to look)

- `infra/` — Bicep modules to provision core cloud resources (AI Foundry, search, storage, container apps, monitoring)
- `src/MCP/` — MCP server implementation for transportation operations with dynamic tool definitions
- `src/data_generator/` — Data generation and indexing utilities for Azure Cosmos DB and AI Search
- `src/Notebooks/` — Jupyter notebooks for Foundry SDK examples
- `scripts/` — Helper scripts for packaging and deployment automation
- `docs/` — Documentation and deployment guides

---

## Sample Agent Prompts

- Identify potential duplicate invoices in Q3 2025 where the same vendor_id and amount occur within 7 days

- List invoices paid to high-risk vendors in Q3 2025 and summarize why these vendors require additional scrutiny based on audit policy. Please cite the audit policy.

- Show me the full details for invoice INV-ANCHOR-001, including any related payments.

- Identify paid invoices in Q3 2025 that are missing a PO or receipt. Cite the invoice_ids.

- Which audit policy governs three-way matching, (cite the policy) and are there any paid invoices in Q3 2025 that do not meet this requirement?

- What audit policy governs validation of bank account changes (cite the policy), and which vendors are classified as high risk?

- Summarize any notable Accounts Payable findings in Q3 2025, including evidence and relevant policy references

---

## ♻️ **Clean-Up**

After completing testing or when no longer needed, ensure you delete any unused Azure resources or remove the entire Resource Group to avoid additional charges.

---

## 📜 License  
This project is licensed under the [MIT License](LICENSE.md), granting permission for commercial and non-commercial use with proper attribution.

---

## Disclaimer  
This project and demo application are intended for educational and demonstration purposes. It is provided "as-is" without any warranties, and users assume all responsibility for its use.
