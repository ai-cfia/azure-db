import logging
from typing import TypedDict
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


class AzureIndexSearchConfig(TypedDict):
    """
    TypedDict for Azure Search Index configuration.

    Attributes:
        client: `SearchClient` instance for query execution.
        search_params: Dict with search parameters.
        result_transform_map: Dict for transforming search results using dpath.

    Example:
        config = AzureIndexSearchConfig(
            client=SearchClient(...),
            search_params={
                "highlight_fields": "content",
                "highlight_pre_tag": "<em>",
                "highlight_post_tag": "</em>",
                "skip": 0,
                "top": 10
            },
            result_transform_map={
                "id": "/id",
                "title": "/title",
                "score": "/@search.score",
                "subtitle": "/subtitle",
                "url": "/url",
                "content": "/content",
                "last_updated": "/last_updated",
            }
        )
    """

    client: SearchClient
    search_params: dict
    result_transform_map: dict


def transform(source_dict, path_map):
    if not path_map:
        return source_dict

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
        client: SearchClient = config["client"]
        map = config["result_transform_map"]
        search_results = client.search(search_text=query, **config["search_params"])
        transformed_results = [transform(result, map) for result in search_results]
        return transformed_results
    except AzureError as e:
        logging.error(f"Search operation failed: {e}", exc_info=True)
        raise SearchQueryError from e
