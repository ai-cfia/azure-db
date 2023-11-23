import unittest
from dataclasses import dataclass
from unittest.mock import Mock, patch

from index_search import (
    AzureIndexSearchQueryError,
    EmptyQueryError,
    search,
    transform_result,
)


@dataclass
class TestAzureSearchConfig:
    client = Mock()
    highlight_fields = "content"
    highlight_tag = "em"


class TestAzureSearch(unittest.TestCase):
    def setUp(self):
        self.config = TestAzureSearchConfig()
        self.config.client.search = Mock()

    def test_transform_result(self):
        mock_result = {
            "id": "123",
            "url": "http://example.com",
            "@search.score": 1.23,
            "metadata_storage_name": "Example Title",
            "@search.highlights": {"content": ["Highlighted content"]},
            "subtitle": "Example Subtitle",
            "metadata_last_modified": "2023-01-01T00:00:00Z",
        }
        expected_output = {
            "id": "123",
            "url": "http://example.com",
            "score": 1.23,
            "title": "Example Title",
            "content": "Highlighted content",
            "subtitle": "Example Subtitle",
            "last_updated": "2023-01-01T00:00:00Z",
        }
        transformed_result = transform_result(mock_result)
        self.assertEqual(transformed_result, expected_output)

    def test_transform_result_no_highlights(self):
        mock_result_no_highlights = {
            "id": "123",
            "url": "http://example.com",
            "@search.score": 1.23,
            "metadata_storage_name": "Example Title",
            "@search.highlights": None,
            "subtitle": "Example Subtitle",
            "metadata_last_modified": "2023-01-01T00:00:00Z",
        }
        expected_output_no_highlights = {
            "id": "123",
            "url": "http://example.com",
            "score": 1.23,
            "title": "Example Title",
            "content": "No content available",  # Expected default content
            "subtitle": "Example Subtitle",
            "last_updated": "2023-01-01T00:00:00Z",
        }
        transformed_result_no_highlights = transform_result(mock_result_no_highlights)
        self.assertEqual(transformed_result_no_highlights, expected_output_no_highlights)

    def test_search_documents_empty_query(self):
        with self.assertRaises(EmptyQueryError):
            search("", self.config)

    @patch("index_search.logging")
    def test_search_documents_query_error(self, mock_logging):
        self.config.client.search.side_effect = Exception("Search failed")
        with self.assertRaises(AzureIndexSearchQueryError):
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
        self.config.client.search.return_value = iter(mock_search_results)
        self.config.highlight_fields = "content"
        results = search("valid_query", self.config)
        expected_output = [transform_result(result) for result in mock_search_results]
        self.assertEqual(results, expected_output)


if __name__ == "__main__":
    unittest.main()
