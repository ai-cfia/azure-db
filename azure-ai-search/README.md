# AI Lab - Azure AI Search Package

## Overview

The `azure-ai-search` package facilitates querying Azure Search indices, 
utilizing
`SearchClient` from `azure.search.documents` with additional features for error
handling and result transformation.

## Installation

To install the package, run:

```shell
pip install git+https://github.com/ai-cfia/azure-db.git@main#subdirectory=azure-ai-search
```

## Configuration

Set up `AzureIndexSearchConfig` with your Azure Search service parameters.

## Usage

Instantiate `AzureIndexSearchConfig` and pass it to the `search` function with 
your query.

```python
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from azure_ai_search import search, AzureIndexSearchConfig

# Initialize SearchClient
client = SearchClient(
    endpoint="https://your-service-name.search.windows.net/",
    index_name="your-index-name",
    credential=AzureKeyCredential("your-api-key")
)

# Configure search
config = AzureIndexSearchConfig(
    client=client,
    highlight_fields="content",
    highlight_tag="strong"
)

# Perform search
results = search("example query", config)
```

## Exceptions

- `AzureIndexSearchQueryError`
- `EmptyQueryError`

## Functions

- `transform_result`
- `search`

