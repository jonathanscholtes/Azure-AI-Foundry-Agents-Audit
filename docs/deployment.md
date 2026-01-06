## Deployment: Microsoft Foundry and Dependencies

### **Prerequisites**
Ensure you have the following before deploying the solution:
- ✅ **Azure Subscription:** Active subscription with sufficient privileges to create and manage resources.  
- ✅ **Azure CLI:** Install the [Azure CLI](https://learn.microsoft.com/en-us/cli/azure/get-started-with-azure-cli) for managing Azure resources.  
- ✅ **IDE with Bicep & PowerShell Support:** Use [VS Code](https://code.visualstudio.com/download) with the **Bicep extension** for development and validation.  

---

### **1. Clone the Repository**
Clone the project repository to your local machine:

```bash
git clone https://github.com/jonathanscholtes/Azure-AI-Foundry-Agents-Audit
cd Azure-AI-Foundry-Agents-Audit

```


### 2. Deploy the Solution  

Use the following PowerShell command to deploy the solution. Be sure to replace the placeholders with your actual subscription name and Azure region.

To test AI Preview features that may have limited region access use  the `AILocation` flag, otherwise `Location` is used for all resources.


```powershell
.\deploy.ps1 -Subscription '[Your Subscription Name]' -Location 'eastus2' -AILocation [Optional flag]  'westus
```

✅ This script provisions all required Azure resources based on the specified parameters. The deployment may take up to **30 minutes** to complete.



### 3. Generate and Index Audit Data

Navigate to the data generator directory and run the data generation script to populate Azure Cosmos DB and create search indexes in Azure AI Search:

```bash
cd src/data_generator
python generate.py
```

This script will:
- Generate audit  data
- Populate Azure Cosmos DB 
- Create and index documents in Azure AI Search for RAG knowledge retrieval





  