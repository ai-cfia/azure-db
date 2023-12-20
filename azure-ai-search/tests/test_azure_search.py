import unittest
from dataclasses import dataclass, field
from unittest.mock import Mock, patch

from index_search import (
    AzureError,
    AzureIndexSearchQueryError,
    EmptyQueryError,
    get_value_by_nested_path,
    search,
    transform,
)


@dataclass
class TestAzureSearchConfig:
    client: Mock = Mock()
    highlight_fields: str = "content"
    highlight_tag: str = "em"
    result_transform_map: dict = field(
        default_factory=lambda: {
            "new_id": "/id",
            "title": "/metadata_storage_name",
            "score": "/@search.score",
            "content_highlight": "/@search.highlights/content/0",
            "last_updated": "/metadata_last_modified",
        }
    )


class TestAzureSearch(unittest.TestCase):
    def setUp(self):
        self.config = TestAzureSearchConfig()
        self.config.client.search = Mock()

    def test_get_value_by_nested_path(self):
        data = {
            "level1": {
                "level2": {"key": "value"},
                "list": [1, 2, {"nested_key": "nested_value"}],
                "empty_list": [],
            },
            "empty": {},
            "none": None,
            "": {"key": "root level key"},
        }
        # Testing valid nested key access
        self.assertEqual(get_value_by_nested_path(data, "/level1/level2/key"), "value")
        # Testing valid access to a nested key in a list
        self.assertEqual(
            get_value_by_nested_path(data, "/level1/list/2/nested_key"), "nested_value"
        )
        # Testing a path leading to a missing key
        self.assertIsNone(get_value_by_nested_path(data, "/level1/missing"))
        # Testing a path leading to a missing key in an empty dict
        self.assertIsNone(get_value_by_nested_path(data, "/empty/missing"))
        # Testing a path leading to a missing key in a None value
        self.assertIsNone(get_value_by_nested_path(data, "/none/missing"))
        # Testing access to the first element in a list
        self.assertEqual(get_value_by_nested_path(data, "/level1/list/0"), 1)
        # Testing access to a non-existent index in a list
        self.assertIsNone(get_value_by_nested_path(data, "/level1/list/10"))
        # Testing path leading directly to a list
        self.assertEqual(
            get_value_by_nested_path(data, "/level1/list"),
            [1, 2, {"nested_key": "nested_value"}],
        )
        # Testing a non-digit character in list index
        self.assertIsNone(get_value_by_nested_path(data, "/level1/list/a"))
        # Testing path leading to an empty list then attempting to access an index
        self.assertIsNone(get_value_by_nested_path(data, "/level1/empty_list/0"))
        # Testing paths with unnecessary leading or trailing delimiters
        self.assertEqual(get_value_by_nested_path(data, "/level1/level2/key/"), "value")
        # Testing path with consecutive delimiters without a key in between
        self.assertIsNone(get_value_by_nested_path(data, "/level1//key"))
        # Testing list as the first argument
        self.assertEqual(get_value_by_nested_path(["not", "a", "dict"], "0"), "not")
        # Testing path leading to the root of the data
        self.assertEqual(get_value_by_nested_path(data, "/"), data)
        self.assertEqual(get_value_by_nested_path(data, ""), data)
        self.assertEqual(get_value_by_nested_path(data, "//"), data)
        # Testing None as data
        self.assertIsNone(get_value_by_nested_path(None, "/level1//key"))

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
            "missing": "/nested/missing",
        }
        expected_dict = {
            "new_id": "123",
            "nested_value": "value",
            "first_list_item": "a",
            "missing": None,
        }
        self.assertEqual(transform(source_dict, path_map), expected_dict)

    def test_transform_with_empty_path_map(self):
        source_dict = {"id": "123", "nested": {"key": "value"}}
        empty_path_map = {}
        self.assertEqual(transform(source_dict, empty_path_map), {})

    def test_transform_with_none_path_map(self):
        source_dict = {"id": "123", "nested": {"key": "value"}}
        self.assertEqual(transform(source_dict, None), {})

    def test_transform_with_empty_source_dict(self):
        path_map = {"new_id": "/id", "nested_value": "/nested/key"}
        self.assertEqual(
            transform({}, path_map), {"new_id": None, "nested_value": None}
        )

    def test_transform_with_none_source_dict(self):
        path_map = {"new_id": "/id", "nested_value": "/nested/key"}
        self.assertEqual(
            transform(None, path_map), {"new_id": None, "nested_value": None}
        )

    def test_search_documents_empty_query(self):
        with self.assertRaises(EmptyQueryError):
            search("", self.config)

    @patch("index_search.logging")
    def test_search_documents_query_error(self, mock_logging):
        self.config.client.search.side_effect = AzureError("Search failed")
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


if __name__ == "__main__":
    unittest.main()
