import logging
from dataclasses import dataclass

from azure.search.documents import SearchClient


class AzureIndexSearchQueryError(Exception):
    """Raised when the search operation fails."""


class EmptyQueryError(Exception):
    """Raised when the search query is empty."""


@dataclass
class AzureIndexSearchConfig:
    endpoint: str
    api_key: str
    index_name: str
    client: SearchClient


def transform_result(result):
    return {
        "id": result.get("id"),
        "url": result.get("url"),
        "score": result.get("@search.score"),
        "title": result.get("title"),
        "content": result.get("content"),
        "subtitle": result.get("subtitle"),
        "last_updated": result.get("metadata_last_modified"),
    }


def search(query, config: AzureIndexSearchConfig):
    if not query:
        logging.error("Empty search query received")
        raise EmptyQueryError("Search query cannot be empty")
    try:
        search_results = config.client.search(search_text=query)
        transformed_results = [transform_result(result) for result in search_results]
        return transformed_results
    except Exception as e:
        logging.error(f"Search operation failed: {e}", exc_info=True)
        raise AzureIndexSearchQueryError from e
