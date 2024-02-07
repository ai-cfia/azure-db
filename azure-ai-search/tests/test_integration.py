import os
import time
import unittest

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from dotenv import load_dotenv
from index_search import search


class AzureSearchIntegrationTest(unittest.TestCase):

    def setUp(self):
        load_dotenv()
        self.service_endpoint = os.getenv("FINESSE_BACKEND_AZURE_SEARCH_ENDPOINT")
        self.index_name = os.getenv("FINESSE_BACKEND_AZURE_SEARCH_INDEX_NAME")
        self.key = os.getenv("FINESSE_BACKEND_AZURE_SEARCH_API_KEY")
        self.client = SearchIndexClient(
            self.service_endpoint, AzureKeyCredential(self.key)
        )
        self.search_client = SearchClient(
            endpoint=self.service_endpoint,
            index_name=self.index_name,
            credential=AzureKeyCredential(self.key),
        )
        self.search_params = {
            "highlight_fields": "content",
            "highlight_pre_tag": "<strong>",
            "highlight_post_tag": "</strong>",
            "skip": 0,
            "top": 10,
        }
        self.result_transform_map = {
            "id": "/id",
            "title": "/title",
            "score": "/@search.score",
            "url": "/url",
            "content": "/@search.highlights/content/0",
            "last_updated": "/last_updated",
        }

    def test_index_existence(self):
        try:
            indexes = self.client.list_indexes()
            index_names = [index.name for index in indexes]
            self.assertIn(
                self.index_name,
                index_names,
                f"Index '{self.index_name}' should exist.",
            )
        except Exception as e:
            self.fail(f"Failed to connect or retrieve data: {e}")

    def test_search(self):
        query = "how to bring a pet to canada?"
        start_time = time.time()
        results = search(
            query, self.search_client, self.search_params, self.result_transform_map
        )
        end_time = time.time()
        duration = (end_time - start_time) * 1000

        self.assertTrue(duration < 500, f"Search operation took too long: {duration}ms")
        self.assertTrue(len(results) <= 10, "Search should return up to 10 results.")


if __name__ == "__main__":
    unittest.main()
