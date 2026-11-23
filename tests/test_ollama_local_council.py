"""Synthetic, no-network tests for the local SZL three-agent council."""
from __future__ import annotations
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import urllib.request

spec=importlib.util.spec_from_file_location("szl_team",Path(__file__).resolve().parents[1] / "tools" / "ollama_local_council.py")
team=importlib.util.module_from_spec(spec)
spec.loader.exec_module(team)

GOOD={"verdict":"HOLD",
      "finding":"The explicit owner admission hold remains binding.",
      "next_test":"Verify the exact GitHub head and required checks again."}


def reply(content=None,done_reason="stop",tool_calls=False):
    message={"content":json.dumps(content or GOOD)}
    if tool_calls:
        message["tool_calls"]=[]
    return {"done":True,"done_reason":done_reason,"message":message}


class TeamTests(unittest.TestCase):
    def test_gateway_duplicate_fields_fail_closed(self):
        for body in ('{"a":1,"a":1}','{"msg":{"a":1,"a":2}}'):
            with self.subTest(body=body),self.assertRaisesRegex(team.Hold,"DUPLICATE_JSON_KEY"):
                team.strict_loads(body)

    def test_nonfinite_and_overflow_denied(self):
        for body in ('{"x":NaN}','{"x":Infinity}','{"x":-Infinity}','{"x":1e9999}'):
            with self.subTest(body=body),self.assertRaisesRegex(team.Hold,"NONFINITE_JSON"):
                team.strict_loads(body)

    def test_malformed_denied(self):
        with self.assertRaisesRegex(team.Hold,"INVALID_JSON"):
            team.strict_loads('{"a":2,,}')

    def test_valid_reply_is_only_advisory(self):
        result=team.parse_reply(reply())
        self.assertEqual(result["verdict"],"HOLD")
        self.assertEqual(len(result["content_sha256"]),64)

    def test_untrusted_tool_calls_and_early_stop_denied(self):
        for case in (reply(tool_calls=True),reply(done_reason="length"),{"done":True,"done_reason":"stop","tool_calls":[],"message":{"content":json.dumps(GOOD)}}):
            with self.subTest(case=case),self.assertRaises(team.Hold):
                team.parse_reply(case)

    def test_false_positive_merge_authority_denied(self):
        for verdict in ("APPROVE","MERGE","GO","ALLOW"):
            with self.subTest(verdict=verdict),self.assertRaisesRegex(team.Hold,"MODEL_AUTHORITY_REFUSED"):
                team.parse_reply(reply({**GOOD,"verdict":verdict}))

    def test_response_schema_guard(self):
        with self.assertRaisesRegex(team.Hold,"RESPONSE_SCHEMA_INVALID"):
            team.parse_reply(reply({**GOOD,"secret":"do-not-include"}))

    def test_no_origin_redirect_accepted(self):
        with self.assertRaisesRegex(team.Hold,"REDIRECT_REFUSED"):
            team.NoRedirect().redirect_request(None,None,302,"",{},"https://example.org/")

    def test_proxy_is_not_inherited(self):
        op=team.opener()
        handlers=[h for h in op.handlers if isinstance(h,urllib.request.ProxyHandler)]
        self.assertTrue(all(not h.proxies for h in handlers))

    def test_public_input_has_an_explicit_merge_hold(self):
        brief = {"schema": "szl.public-peer-brief/v1",
                 "repo": "szl-holdings/szl-ops-runbook", "head": "a" * 40,
                 "draft": True, "body_hold": "DRAFT / HOLD / DO NOT MERGE",
                 "source_change": "Synthetic public Python source review for parser hardening.",
                 "public_source_confirmed": True}
        self.assertTrue(team.public_brief(brief)["draft"])
        self.assertIn("DO NOT MERGE", team.public_brief(brief)["body_hold"])
        for field, invalid in (("public_source_confirmed", False),
                               ("head", "main"),
                               ("repo", "outside/private"),
                               ("source_change", "Authorization: Bearer dummy-not-real-token-123456789")):
            with self.subTest(field=field), self.assertRaises(team.Hold):
                team.public_brief({**brief, field: invalid})

    def test_local_model_digests_are_pinned(self):
        self.assertEqual({name for _, name in team.MODELS}, set(team.EXPECTED_DIGESTS))
        self.assertTrue(all(team.SHA.fullmatch(d) for d in team.EXPECTED_DIGESTS.values()))

    def test_unpaired_unicode_refused_in_nested_json(self):
        for raw in ('{"x":"\\ud800"}', '{"x":{"nested":"\\udc00"}}'):
            with self.assertRaisesRegex(team.Hold, "UNPAIRED_UNICODE"):
                team.strict_loads(raw)

    def test_main_writes_private_advisory_receipt_and_cannot_merge(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "brief.json"
            receipt = root / "receipt.json"
            brief = {"schema": "szl.public-peer-brief/v1",
                     "repo": "szl-holdings/szl-ops-runbook", "head": "b" * 40,
                     "draft": True, "body_hold": "DRAFT / HOLD / DO NOT MERGE",
                     "source_change": "A synthetic, public fixture verifying strict Ollama response JSON only.",
                     "public_source_confirmed": True}
            source.write_text(json.dumps(brief))
            valid = {"status": "VALID_ADVISORY", "verdict": "HOLD",
                     "finding": "Explicit hold is still active; do not merge.",
                     "next_test": "Check current head and required CI status."}
            with patch.object(team, "local_models", return_value=team.EXPECTED_DIGESTS):
                with patch.object(team, "ask", return_value=valid) as consultant:
                    self.assertEqual(0, team.main(["--public-brief", str(source),
                                                  "--receipt", str(receipt)]))
            self.assertEqual(3, consultant.call_count)
            saved = json.loads(receipt.read_text())
            self.assertTrue(saved["all_three_valid"])
            self.assertFalse(saved["merge_authorized"])
            self.assertFalse(saved["deployment_authorized"])
            self.assertFalse(saved["signed_receipt"])
            self.assertEqual(0o600, receipt.stat().st_mode & 0o777)
            with patch.object(team, "local_models", side_effect=AssertionError("MUST_NOT_RUN")):
                self.assertEqual(2, team.main(["--public-brief", str(source),
                                              "--receipt", str(receipt)]))

    def test_main_denies_missing_model_pin_before_inference(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "brief.json"
            brief = {"schema": "szl.public-peer-brief/v1",
                     "repo": "szl-holdings/szl-ops-runbook", "head": "c" * 40,
                     "draft": False, "body_hold": "",
                     "source_change": "A synthetic, public source contract with an otherwise clean check.",
                     "public_source_confirmed": True}
            source.write_text(json.dumps(brief))
            with patch.object(team, "local_models", return_value={"mistral:7b": "bad-digest"}):
                with patch.object(team, "ask", side_effect=AssertionError("MUST_NOT_RUN")):
                    self.assertEqual(2, team.main(["--public-brief", str(source),
                                                  "--receipt", str(root / "receipt.json")]))
            self.assertFalse((root / "receipt.json").exists())


if __name__=="__main__":
    unittest.main()
