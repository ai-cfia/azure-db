import unittest
from unittest.mock import Mock, patch

from index_search import (
    AzureError,
    AzureIndexSearchConfig,
    DataTransformError,
    EmptyQueryError,
    SearchQueryError,
    search,
    transform,
)


class TestAzureSearch(unittest.TestCase):
    def setUp(self):
        client = Mock()
        client.search = Mock()
        self.config: AzureIndexSearchConfig = {
            "client": client,
            "search_params": {},
            "result_transform_map": {
                "new_id": "/id",
                "title": "/metadata_storage_name",
                "score": "/@search.score",
                "content_highlight": "/@search.highlights/content/0",
                "last_updated": "/metadata_last_modified",
            },
        }

    def test_transform(self):
        source_dict = {
            "id": "123",
            "nested": {"key": "value", "list": [1, 2, 3]},
            "list": ["a", "b", "c"],
        }
        path_map = {
            "new_id": "/id",
            "nested_value": "/nested/key",
            "first_list_item": "/list/0",
        }
        expected_dict = {
            "new_id": "123",
            "nested_value": "value",
            "first_list_item": "a",
        }
        self.assertEqual(transform(source_dict, path_map), expected_dict)

    def test_transform_decodes_title_field(self):
        source_dict = {
            "id": "123",
            "metadata_storage_name": "Example%20Title%201",
            "@search.score": 2.1,
        }
        path_map = {
            "new_id": "/id",
            "title": "/metadata_storage_name",
            "score": "/@search.score",
        }
        expected_dict = {
            "new_id": "123",
            "title": "Example Title 1",
            "score": 2.1,
        }
        self.assertEqual(transform(source_dict, path_map), expected_dict)

    def test_transform_with_empty_path_map(self):
        source_dict = {"id": "123", "nested": {"key": "value"}}
        empty_path_map = {}
        self.assertEqual(transform(source_dict, empty_path_map), source_dict)

    def test_transform_with_none_path_map(self):
        source_dict = {"id": "123", "nested": {"key": "value"}}
        self.assertEqual(transform(source_dict, None), source_dict)

    def test_transform_raises_data_transform_error(self):
        source_dict = {"id": "123"}
        invalid_path_map = {"invalid_key": "/nonexistent/path"}

        with self.assertRaises(DataTransformError):
            transform(source_dict, invalid_path_map)

    def test_search_documents_empty_query(self):
        with self.assertRaises(EmptyQueryError):
            search("", self.config)

    @patch("index_search.logging")
    def test_search_documents_query_error(self, mock_logging):
        self.config["client"].search.side_effect = AzureError("Search failed")
        with self.assertRaises(SearchQueryError):
            search("test_query", self.config)
        mock_logging.error.assert_called()

    def test_search_documents_success(self):
        mock_search_results = [
            {
                "id": "1",
                "url": "http://example.com/1",
                "@search.score": 2.1,
                "metadata_storage_name": "Example Title 1",
                "@search.highlights": {"content": ["Highlighted Content 1"]},
                "subtitle": "Example Subtitle 1",
                "metadata_last_modified": "2023-01-01T00:00:00Z",
            },
        ]
        self.config["client"].search.return_value = iter(mock_search_results)
        self.config["search_params"][
            "highlight_fields"
        ] = "content"  # Adjust to actual usage if necessary
        results = search("valid_query", self.config)
        expected_output = [
            {
                "new_id": "1",
                "title": "Example Title 1",
                "score": 2.1,
                "content_highlight": "Highlighted Content 1",
                "last_updated": "2023-01-01T00:00:00Z",
            }
        ]
        self.assertEqual(results, expected_output)
