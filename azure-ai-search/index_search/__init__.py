import logging
from typing import Any, Dict
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


def transform(source_dict: Dict[str, Any], path_map: Dict[str, str]) -> Dict[str, Any]:
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


def search(
    query: str, client: SearchClient, search_params: dict, result_transform_map: dict
):
    if not query:
        logging.error("Empty search query received")
        raise EmptyQueryError("Search query cannot be empty")

    try:
        search_results = client.search(search_text=query, **search_params)
        transformed_results = [
            transform(result, result_transform_map) for result in search_results
        ]
        return transformed_results
    except AzureError as e:
        logging.error(f"Search operation failed: {e}", exc_info=True)
        raise SearchQueryError from e
