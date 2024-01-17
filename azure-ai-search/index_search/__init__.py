import logging
from dataclasses import dataclass, field
from urllib.parse import unquote

import dpath
from azure.core.exceptions import AzureError
from azure.search.documents import SearchClient


class AzureIndexSearchError(Exception):
    """Generic Azure Index Search error."""


class SearchQueryError(AzureIndexSearchError):
    """Raised when the search operation fails."""


class EmptyQueryError(AzureIndexSearchError):
    """Raised when the search query is empty."""


class DataTransformError(AzureIndexSearchError):
    """Raised when a data transformation fails."""


@dataclass
class AzureIndexSearchConfig:
    """
    Configuration class for Azure Index Search.

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
        result_transform_map (dict, optional): A dictionary defining the mapping for
        transforming the search results. Keys are new field names, and values are
        paths in the result dictionary.

    Example:
        config = AzureIndexSearchConfig(
            client=SearchClient(...),
            endpoint="https://your-service-name.search.windows.net/",
            api_key="your-api-key",
            index_name="your-index-name",
            highlight_fields="content",
            highlight_tag="strong",
            result_transform_map={
                "title": "metadata_storage_name",
                "content": "content"
                # More mappings...
            }
        )
    """

    client: SearchClient
    endpoint: str | None = None
    api_key: str | None = None
    index_name: str | None = None
    highlight_fields: str | None = None
    highlight_tag: str = "em"
    result_transform_map: dict = field(
        default_factory=lambda: {
            "id": "/id",
            "title": "/title",
            "score": "/@search.score",
            "subtitle": "/subtitle",
            "url": "/url",
            "content": "/@search.highlights/content/0",
            "last_updated": "/last_updated",
        }
    )


def transform(source_dict, path_map):
    if path_map is None:
        return {}

    transformed_dict = {}
    for new_key, path in path_map.items():
        try:
            value = dpath.get(source_dict, path)
        except (KeyError, ValueError) as e:
            logging.error(f"Data transformation failed: {e}", exc_info=True)
            raise DataTransformError from e
        # Title is currently URL-encoded to avoid errors in the blob storage
        if new_key == "title":
            value = unquote(value) if value is not None else value
        transformed_dict[new_key] = value

    return transformed_dict


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
        map = config.result_transform_map
        transformed_results = [transform(result, map) for result in search_results]
        return transformed_results
    except AzureError as e:
        logging.error(f"Search operation failed: {e}", exc_info=True)
        raise SearchQueryError from e
