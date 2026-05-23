import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(__file__))

import hermes_tweet


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload
        self.status_checked = False

    def raise_for_status(self):
        self.status_checked = True

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def get(self, url, headers, timeout):
        self.calls.append({"url": url, "headers": headers, "timeout": timeout})
        return FakeResponse(self.payload)


class HermesTweetTests(unittest.TestCase):
    def test_backend_aliases(self):
        self.assertEqual(hermes_tweet.normalize_backend("xquik"), "hermes-tweet")
        self.assertEqual(hermes_tweet.normalize_backend("hermes_tweet"), "hermes-tweet")
        self.assertEqual(hermes_tweet.normalize_backend("jina"), "jina")

    def test_backend_enabled_reads_environment(self):
        with mock.patch.dict(os.environ, {"X_MONITOR_BACKEND": "hermes-tweet"}):
            self.assertTrue(hermes_tweet.backend_enabled())

    def test_build_headers_supports_xquik_and_bearer_keys(self):
        self.assertEqual(hermes_tweet.build_headers("xq_test")["x-api-key"], "xq_test")
        self.assertEqual(hermes_tweet.build_headers("token")["Authorization"], "Bearer token")

    def test_build_url_encodes_username_and_limit(self):
        url = hermes_tweet.build_url("@Open AI", limit=3, base_url="https://xquik.test/")
        self.assertEqual(url, "https://xquik.test/api/v1/x/users/Open%20AI/tweets?limit=3")

    def test_extract_items_from_nested_payload(self):
        items = hermes_tweet.extract_items({"data": {"tweets": [{"id": "1"}, {"id": "2"}]}})
        self.assertEqual(items, [{"id": "1"}, {"id": "2"}])

    def test_fetch_account_tweets_normalizes_payload(self):
        session = FakeSession(
            {
                "data": [
                    {
                        "id": "42",
                        "text": "Hermes Tweet gives this monitor structured X reads.",
                        "created_at": "2026-05-23T14:00:00Z",
                    }
                ]
            }
        )

        tweets = hermes_tweet.fetch_account_tweets(
            "openai",
            limit=2,
            api_key="xq_test",
            base_url="https://xquik.test",
            session=session,
        )

        self.assertEqual(len(tweets), 1)
        self.assertEqual(tweets[0]["id"], "42")
        self.assertEqual(tweets[0]["raw_content"], "Hermes Tweet gives this monitor structured X reads.")
        self.assertEqual(session.calls[0]["headers"]["x-api-key"], "xq_test")
        self.assertEqual(session.calls[0]["timeout"], 30)


if __name__ == "__main__":
    unittest.main()
