# AI Lab - Azure AI Search Package

## Overview

The `azure-ai-search` package facilitates querying Azure Search indices,
utilizing `SearchClient` from `azure.search.documents` with additional features
for error handling and result transformation.

## Installation

To install the package, run:

```shell
pip install git+https://github.com/ai-cfia/azure-db.git@main#subdirectory=azure-ai-search
```

## Configuration

Prepare `AzureIndexSearchConfig` with necessary Azure Search service details to
begin.

## Usage

Create an `AzureIndexSearchConfig` instance and utilize it with the `search`
function alongside your search query.

```python
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from azure_ai_search import search, AzureIndexSearchConfig

# Set up the SearchClient
client = SearchClient(
    endpoint="https://your-service-name.search.windows.net/",
    index_name="your-index-name",
    credential=AzureKeyCredential("your-api-key")
)

# Search configuration
config: AzureIndexSearchConfig = {
    "client": client,
    "search_params": {
        "highlight_fields": "content",
        "highlight_pre_tag": "<strong>",
        "highlight_post_tag": "</strong>",
        "skip": 0,
        "top": 10
    },
    "result_transform_map": {
        "id": "/id",
        "title": "/title",
        "score": "/@search.score",
        "subtitle": "/subtitle",
        "url": "/url",
        "content": "/content",
        "last_updated": "/last_updated",
    }
}

# Execute search
results = search("example query", config)
```

## Exceptions

- `AzureIndexSearchError`: A generic error for search-related issues.
- `SearchQueryError`: Triggered by failures during the search process.
- `EmptyQueryError`: Raised for empty search queries.
- `DataTransformError`: Occurs when transforming search results fails.

## Functions

- `transform`: Modifies search result data based on predefined mappings.
- `search`: Executes search queries against Azure Search indices.
