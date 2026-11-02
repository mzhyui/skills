#!/usr/bin/env python3
"""Bounded AutoDL Pro API calls with private credentials and redacted receipts."""
import argparse
import datetime
import json
import os
from pathlib import Path
import re
import stat
import sys
from typing import Any
import urllib.error
import urllib.parse
import urllib.request

HOST = "https://api.autodl.com"
PREFIX = "/api/v1/dev/instance/pro/"
SECRET_KEY = re.compile(r"password|token|secret|authorization|cookie|command", re.I)
JWT = re.compile(r"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+")


def redact(value: Any, token: str) -> Any:
    if isinstance(value, dict):
        return {k: "[REDACTED]" if SECRET_KEY.search(k) else redact(v, token)
                for k, v in value.items()}
    if isinstance(value, list):
        return [redact(v, token) for v in value]
    if isinstance(value, str):
        return JWT.sub("[REDACTED]", value.replace(token, "[REDACTED]"))
    return value


def credential() -> str:
    token = os.environ.get("AUTODL_TOKEN", "").strip()
    if not token:
        path = Path(os.environ.get("AUTODL_TOKEN_FILE", "~/.config/autodl/token")).expanduser()
        if stat.S_IMODE(path.stat().st_mode) & 0o077:
            raise ValueError("Credential file must be private (chmod 600)")
        token = path.read_text().strip()
    if not token or any(c.isspace() for c in token):
        raise ValueError("Missing or malformed AutoDL credential")
    return token


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None  # Never forward the credential to another endpoint.


def request(method: str, path: str, body: dict[str, Any], token: str,
            timeout: int = 30) -> dict[str, Any]:
    url = HOST + path
    headers = {"Authorization": token, "Content-Type": "application/json"}
    data = None
    if method == "GET":
        if body:
            url += "?" + urllib.parse.urlencode(body)
    else:
        data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    opener = urllib.request.build_opener(NoRedirect)
    try:
        with opener.open(req, timeout=timeout) as response:
            status, raw = response.status, response.read()
    except urllib.error.HTTPError as error:
        status, raw = error.code, error.read()
    try:
        payload = json.loads(raw)
    except (ValueError, UnicodeError):
        payload = {"code": "NonJSONResponse", "msg": "Response body omitted"}
    return {"observed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "http_status": status, "response": redact(payload, token)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=["balance", "images", "instances", "status", "snapshot", "create", "power-off"])
    parser.add_argument("--instance")
    parser.add_argument("--page", type=int, default=1)
    parser.add_argument("--page-size", type=int, default=100)
    parser.add_argument("--request-file", type=Path, help="Reviewed create-request JSON")
    parser.add_argument("--execute", action="store_true", help="Permit the explicitly authorized mutation")
    args = parser.parse_args()
    mutation = args.operation in {"create", "power-off"}
    if mutation and not args.execute:
        parser.error("Mutations require user authorization and --execute")
    if args.operation in {"status", "snapshot", "power-off"} and not args.instance:
        parser.error("--instance is required")
    if args.page < 1 or not 1 <= args.page_size <= 100:
        parser.error("Use page >= 1 and page-size between 1 and 100")
    method = "POST"
    body = {}
    if args.operation == "balance":
        path = "/api/v1/dev/wallet/balance"
    elif args.operation in {"images", "instances"}:
        path = PREFIX + ("image/private/list" if args.operation == "images" else "list")
        body = {"page_index": args.page, "page_size": args.page_size}
    elif args.operation in {"status", "snapshot", "power-off"}:
        path = PREFIX + args.operation.replace("-", "_")
        method = "POST" if mutation else "GET"
        body = {"instance_uuid": args.instance}
    else:
        if not args.request_file:
            parser.error("create requires --request-file")
        body = json.loads(args.request_file.read_text())
        required = {"req_gpu_amount", "expand_system_disk_by_gb", "gpu_spec_uuid", "image_uuid", "cuda_v_from"}
        if not isinstance(body, dict) or not required <= body.keys():
            parser.error("Create JSON must contain the five documented required fields")
        path = PREFIX + "create"
    try:
        result = request(method, path, body, credential(), timeout=45 if mutation else 30)
    except (OSError, ValueError) as error:
        # No raw exception text: it can include URLs or response contents.
        print(json.dumps({"error": type(error).__name__, "operation": args.operation,
                          "outcome": "unknown; reconcile instance list/status before any mutation retry" if mutation else "probe failed"}))
        return 3
    print(json.dumps(result, ensure_ascii=False, indent=2))
    payload = result["response"]
    return 0 if result["http_status"] == 200 and isinstance(payload, dict) and payload.get("code") == "Success" else 2


if __name__ == "__main__":
    sys.exit(main())
