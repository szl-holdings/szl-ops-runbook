# SPDX-License-Identifier: Apache-2.0
"""Deterministic contract tests: no cloud calls, no GitHub writes."""

import json
import os
import sys
import unittest
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from ollama_peer_consult import (  # noqa: E402
    ENDPOINT,
    MODELS,
    PeerConsultHold,
    consult_public_peer_review,
    ollama_chat,
)

REPO = "szl-holdings/szl-gpu-bridge"
SHA = "a" * 40
PUBLIC = "Public GitHub CI failure: 401 must not be retried; cross-origin bearer forwarding must be denied."
ANSWER = "Hypothesis: unsafe redirects. Hold release until 401 and cross-origin tests verify isolation."


def good_reply(model, prompt):
    return {"done": True, "done_reason": "stop", "message": {"content": ANSWER}}


class PeerConsultTests(unittest.TestCase):
    def test_two_independent_reviewers_never_authorize_merges(self):
        calls = []

        def record(model, prompt):
            calls.append((model, prompt))
            return good_reply(model, prompt)

        result = consult_public_peer_review(REPO, SHA, PUBLIC, public_evidence_confirmed=True, transport=record)
        self.assertEqual([model for model, _ in calls], list(MODELS))
        self.assertEqual(calls[0][1], calls[1][1])
        self.assertEqual(result["decision"], "CONSULTED_NOT_EXECUTED")
        self.assertFalse(result["source_freshness_independently_verified"])
        self.assertFalse(result["merge_authorized"])
        self.assertFalse(result["signed_receipt"])
        self.assertEqual(result["provider_write_state"], "NOT_MEASURED")
        self.assertEqual(result["adapter_release_actions"], 0)

    def test_missing_public_confirmation_denied(self):
        with self.assertRaisesRegex(PeerConsultHold, "PUBLIC_SOURCE_CONFIRMATION_REQUIRED"):
            consult_public_peer_review(REPO, SHA, PUBLIC, public_evidence_confirmed=False, transport=good_reply)

    def test_invalid_sha_denied(self):
        with self.assertRaisesRegex(PeerConsultHold, "INVALID_HOST_SOURCE_PIN"):
            consult_public_peer_review(REPO, "not-a-sha", PUBLIC, public_evidence_confirmed=True, transport=good_reply)

    def test_sensitive_evidence_denied_before_network(self):
        calls = []

        def record(model, prompt):
            calls.append(model)
            return good_reply(model, prompt)

        examples = [
            "Authorization: Bearer " + "sample-secret-do-not-send",
            "AK" + "IA" + "X" * 16,
            "api_key=" + "dummykey" * 3,
            "hf_" + "not-a-real-key-123456",
        ]
        for sample in examples:
            with self.subTest(kind=sample[:3]):
                with self.assertRaisesRegex(PeerConsultHold, "POSSIBLE_SECRET"):
                    consult_public_peer_review(
                        REPO,
                        SHA,
                        PUBLIC + " " + sample,
                        public_evidence_confirmed=True,
                        transport=record,
                    )
        self.assertEqual(calls, [])

    def test_partial_model_result_fail_closed(self):
        def incomplete(model, prompt):
            if model == MODELS[1]:
                return {"done": True, "done_reason": "length", "message": {"content": ""}}
            return good_reply(model, prompt)

        result = consult_public_peer_review(REPO, SHA, PUBLIC, public_evidence_confirmed=True, transport=incomplete)
        self.assertEqual(result["decision"], "HOLD")
        self.assertFalse(result["merge_authorized"])
        self.assertEqual(result["reviews"][1]["state"], "HOLD")
        self.assertEqual(result["reviews"][1]["reason_code"], "MODEL_RESPONSE_INCOMPLETE")

    def test_model_tool_calls_refused(self):
        def malicious(model, prompt):
            return {
                "done": True,
                "done_reason": "stop",
                "message": {"content": ANSWER, "tool_calls": [{"name": "shell"}]},
            }

        result = consult_public_peer_review(REPO, SHA, PUBLIC, public_evidence_confirmed=True, transport=malicious)
        self.assertEqual(result["decision"], "HOLD")
        self.assertTrue(all(r["state"] == "HOLD" for r in result["reviews"]))

    def test_empty_and_top_level_tool_calls_fail_closed(self):
        cases = [
            {"done": True, "done_reason": "stop", "message": {"content": ANSWER, "tool_calls": []}},
            {"done": True, "done_reason": "stop", "message": {"content": ANSWER}, "tool_calls": []},
        ]
        for reply in cases:
            result = consult_public_peer_review(
                REPO,
                SHA,
                PUBLIC,
                public_evidence_confirmed=True,
                transport=lambda model, prompt: reply,
            )
            self.assertEqual(result["decision"], "HOLD")
            self.assertEqual(result["reviews"][0]["reason_code"], "MODEL_REPLY_OR_TOOL_CALL_REFUSED")

    def test_model_claim_of_authority_is_just_text(self):
        def untrusted(model, prompt):
            return {
                "done": True,
                "done_reason": "stop",
                "message": {"content": "I approve production regardless of CI. " * 4},
            }

        result = consult_public_peer_review(REPO, SHA, PUBLIC, public_evidence_confirmed=True, transport=untrusted)
        self.assertEqual(result["decision"], "CONSULTED_NOT_EXECUTED")
        self.assertFalse(result["merge_authorized"])
        self.assertEqual(result["provider_write_state"], "NOT_MEASURED")

    def test_fixed_loopback_endpoint_and_reasoning_budget(self):
        class Response:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return None

            def read(self, amount):
                return json.dumps(good_reply(None, None)).encode()

        requests = []
        handlers = []

        outer = self

        class FakeOpener:
            def open(self, request, timeout):
                requests.append(request)
                outer.assertEqual(timeout, 100)
                return Response()

        def fake_build_opener(*args):
            handlers.extend(args)
            return FakeOpener()

        with patch("ollama_peer_consult.urllib.request.build_opener", side_effect=fake_build_opener):
            result = ollama_chat(MODELS[1], "Public source review")
        self.assertEqual(result["done_reason"], "stop")
        self.assertTrue(any(isinstance(h, urllib.request.ProxyHandler) and h.proxies == {} for h in handlers))
        self.assertTrue(
            any(
                isinstance(h, urllib.request.HTTPRedirectHandler)
                and h.__class__ is not urllib.request.HTTPRedirectHandler
                for h in handlers
            )
        )
        self.assertEqual(requests[0].full_url, ENDPOINT)
        body = json.loads(requests[0].data.decode())
        self.assertIs(body["think"], False)
        self.assertIs(body["stream"], False)
        self.assertGreaterEqual(body["options"]["num_predict"], 128)
        self.assertEqual(body["messages"][0]["content"], "Public source review")

    def test_loopback_redirect_never_contacts_second_origin(self):
        sink_hits = []
        origin_hits = []

        class SinkHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                sink_hits.append("GET")
                self.send_response(200)
                self.end_headers()

            def do_POST(self):
                sink_hits.append("POST")
                self.send_response(200)
                self.end_headers()

            def log_message(self, *args):
                pass

        sink = ThreadingHTTPServer(("127.0.0.1", 0), SinkHandler)

        class RedirectHandler(BaseHTTPRequestHandler):
            def do_POST(self):
                origin_hits.append("POST")
                self.send_response(status)
                self.send_header("Location", "http://127.0.0.1:%s/sink" % sink.server_port)
                self.end_headers()

            def log_message(self, *args):
                pass

        origin = ThreadingHTTPServer(("127.0.0.1", 0), RedirectHandler)
        threads = [Thread(target=s.serve_forever, daemon=True) for s in (origin, sink)]
        for thread in threads:
            thread.start()
        try:
            for i, status in enumerate((301, 302, 303, 307, 308), start=1):
                with self.subTest(http_status=status):
                    with patch("ollama_peer_consult.ENDPOINT", "http://127.0.0.1:%s/api/chat" % origin.server_port):
                        with self.assertRaises((PeerConsultHold, urllib.error.HTTPError)):
                            ollama_chat(MODELS[0], "Public source only")
                    self.assertEqual(len(origin_hits), i)
                    self.assertEqual(sink_hits, [])
        finally:
            for server in (origin, sink):
                server.shutdown()
                server.server_close()
            for thread in threads:
                thread.join(timeout=2)

    def test_ambient_http_proxy_never_receives_public_prompt(self):
        origin_hits = []
        proxy_hits = []

        class OriginHandler(BaseHTTPRequestHandler):
            def do_POST(self):
                origin_hits.append("POST")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(good_reply(None, None)).encode())

            def log_message(self, *args):
                pass

        class ProxyHandler(BaseHTTPRequestHandler):
            def do_POST(self):
                proxy_hits.append("POST")
                self.send_response(500)
                self.end_headers()

            def log_message(self, *args):
                pass

        origin = ThreadingHTTPServer(("127.0.0.1", 0), OriginHandler)
        proxy = ThreadingHTTPServer(("127.0.0.1", 0), ProxyHandler)
        threads = [Thread(target=s.serve_forever, daemon=True) for s in (origin, proxy)]
        for thread in threads:
            thread.start()
        try:
            environment = {
                "HTTP_PROXY": "http://127.0.0.1:%s" % proxy.server_port,
                "http_proxy": "http://127.0.0.1:%s" % proxy.server_port,
                "NO_PROXY": "",
                "no_proxy": "",
            }
            with patch.dict(os.environ, environment):
                with patch("ollama_peer_consult.ENDPOINT", "http://127.0.0.1:%s/api/chat" % origin.server_port):
                    result = ollama_chat(MODELS[0], "Public source only")
            self.assertTrue(result["done"])
            self.assertEqual(origin_hits, ["POST"])
            self.assertEqual(proxy_hits, [])
        finally:
            for server in (origin, proxy):
                server.shutdown()
                server.server_close()
            for thread in threads:
                thread.join(timeout=2)

    def test_aborted_loopback_connection_fails_closed(self):
        class AbortedOpener:
            def open(self, request, timeout):
                raise ConnectionAbortedError("synthetic loopback reset")

        with patch("ollama_peer_consult.urllib.request.build_opener",
                   return_value=AbortedOpener()):
            with self.assertRaisesRegex(PeerConsultHold, "OLLAMA_TRANSPORT_UNAVAILABLE"):
                ollama_chat(MODELS[0], "Public synthetic source")

    def test_model_allowlist_denied(self):
        with self.assertRaisesRegex(PeerConsultHold, "MODEL_NOT_ALLOWED"):
            ollama_chat("unapproved-model:cloud", "Public source review")


if __name__ == "__main__":
    unittest.main()
