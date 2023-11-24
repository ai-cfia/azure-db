import logging
from dataclasses import dataclass

from azure.core.exceptions import AzureError
from azure.search.documents import SearchClient


class AzureIndexSearchQueryError(Exception):
    """Raised when the search operation fails."""


class EmptyQueryError(Exception):
    """Raised when the search query is empty."""


@dataclass
class AzureIndexSearchConfig:
    """
    Configuration class for Azure Index Search.

    This class holds the necessary configuration details required for setting up
    and executing search queries against an Azure Cognitive Search index.

    Attributes:
        client (SearchClient): An instance of `SearchClient` from the
        `azure.search.documents` package. This is the only mandatory field.
        endpoint (str, optional): The endpoint URL of the Azure Search service.
        api_key (str, optional): The API key for authenticating requests to the Azure
        Search service.
        index_name (str, optional): The name of the Azure Search index to query.
        highlight_fields (str, optional): A comma-separated string of field names on
        which to perform hit highlighting.
        highlight_tag (str): The HTML tag used to highlight search hits in the
        result snippets. If not provided, defaults to 'em'.

    Example:
        config = AzureIndexSearchConfig(
            client=SearchClient(...),
            endpoint="https://your-service-name.search.windows.net/",
            api_key="your-api-key",
            index_name="your-index-name",
            highlight_fields="content",
            highlight_tag="strong"
        )
    """

    client: SearchClient
    endpoint: str | None = None
    api_key: str | None = None
    index_name: str | None = None
    highlight_fields: str | None = None
    highlight_tag: str = "em"


def transform_result(result):
    content_highlights = (result["@search.highlights"] or {}).get(
        "content", ["No content available"]
    )
    return {
        "id": result.get("id"),
        "url": result.get("url"),
        "score": result.get("@search.score"),
        "title": result.get("metadata_storage_name"),
        "content": content_highlights[0],
        "subtitle": result.get("subtitle"),
        "last_updated": result.get("metadata_last_modified"),
    }


def search(query, config: AzureIndexSearchConfig):
    if not query:
        logging.error("Empty search query received")
        raise EmptyQueryError("Search query cannot be empty")

    try:
        search_results = config.client.search(
            search_text=query,
            highlight_fields=config.highlight_fields,
            highlight_pre_tag=f"<{config.highlight_tag}>",
            highlight_post_tag=f"</{config.highlight_tag}>",
        )
        transformed_results = [transform_result(result) for result in search_results]
        return transformed_results
    except AzureError as e:
        logging.error(f"Search operation failed: {e}", exc_info=True)
        raise AzureIndexSearchQueryError from e
