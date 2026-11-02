"""Offline checks for credential custody and the AutoDL HTTP contract."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

spec = importlib.util.spec_from_file_location(
    "autodl_api", Path(__file__).parents[1] / "scripts/autodl_api.py")
api = importlib.util.module_from_spec(spec)
spec.loader.exec_module(api)


class AutoDLTests(unittest.TestCase):
    def response(self, body: bytes) -> Mock:
        response = Mock(status=200)
        response.read.return_value = body
        opener = Mock()
        opener.open.return_value.__enter__ = Mock(return_value=response)
        opener.open.return_value.__exit__ = Mock(return_value=False)
        return opener

    def test_get_uses_query_and_raw_authorization(self):
        opener = self.response(b'{"code":"Success","data":"shutdown"}')
        with patch.object(api.urllib.request, "build_opener", return_value=opener):
            result = api.request("GET", api.PREFIX + "status",
                                 {"instance_uuid": "pro-a+b"}, "dummy-credential")
        request = opener.open.call_args.args[0]
        self.assertTrue(request.full_url.endswith("?instance_uuid=pro-a%2Bb"))
        self.assertIsNone(request.data)
        self.assertEqual(request.get_header("Authorization"), "dummy-credential")
        self.assertEqual(result["response"]["data"], "shutdown")

    def test_post_keeps_exact_region_and_body(self):
        body = {"data_center_list": ["westDC3"], "image_uuid": "image-test"}
        opener = self.response(b'{"code":"Success","data":"pro-test"}')
        with patch.object(api.urllib.request, "build_opener", return_value=opener):
            api.request("POST", api.PREFIX + "create", body, "dummy-credential")
        request = opener.open.call_args.args[0]
        self.assertEqual(request.method, "POST")
        self.assertEqual(json.loads(request.data), body)
        self.assertEqual(opener.open.call_count, 1)

    def test_nested_credentials_and_echoed_token_are_redacted(self):
        data = {"root_password": "private", "nested": [{"jupyter_token": "private"}],
                "msg": "dummy-credential", "gpu": "v-32g-p"}
        result = api.redact(data, "dummy-credential")
        self.assertNotIn("private", json.dumps(result))
        self.assertNotIn("dummy-credential", json.dumps(result))
        self.assertEqual(result["gpu"], "v-32g-p")

    def test_redirect_never_forwards_credentials(self):
        self.assertIsNone(api.NoRedirect().redirect_request(
            None, None, 302, "", {}, "https://elsewhere.invalid"))

    def test_public_credential_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "token"
            path.write_text("dummy-credential\n")
            path.chmod(0o644)
            with patch.dict(os.environ, {"AUTODL_TOKEN_FILE": str(path)}, clear=True):
                with self.assertRaises(ValueError):
                    api.credential()
                path.chmod(0o600)
                self.assertEqual(api.credential(), "dummy-credential")

    def test_mutations_require_execute_before_loading_credentials(self):
        for operation in ("create", "power-off"):
            with self.subTest(operation=operation), patch.object(api.sys, "argv", ["api", operation]), \
                    patch.object(api, "credential") as credential, contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as error:
                    api.main()
                self.assertEqual(error.exception.code, 2)
                credential.assert_not_called()

    def test_http_200_api_rejection_is_failure(self):
        receipt = {"http_status": 200, "response": {"code": "TORealName", "data": None}}
        with patch.object(api.sys, "argv", ["api", "balance"]), \
                patch.object(api, "credential", return_value="dummy-credential"), \
                patch.object(api, "request", return_value=receipt), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(api.main(), 2)

    def test_uncertain_power_off_has_no_automatic_retry_or_exception_leak(self):
        output = io.StringIO()
        with patch.object(api.sys, "argv", ["api", "power-off", "--instance", "pro-test", "--execute"]), \
                patch.object(api, "credential", return_value="dummy-credential"), \
                patch.object(api, "request", side_effect=TimeoutError("dummy-credential")) as request, \
                contextlib.redirect_stdout(output):
            self.assertEqual(api.main(), 3)
        request.assert_called_once()
        self.assertNotIn("dummy-credential", output.getvalue())
        self.assertIn("reconcile", output.getvalue())

    def test_non_json_response_body_is_not_exposed(self):
        opener = self.response(b'<html>dummy-credential</html>')
        with patch.object(api.urllib.request, "build_opener", return_value=opener):
            result = api.request("GET", api.PREFIX + "status", {}, "dummy-credential")
        self.assertEqual(result["response"]["code"], "NonJSONResponse")
        self.assertNotIn("dummy-credential", json.dumps(result))


if __name__ == "__main__":
    unittest.main()
