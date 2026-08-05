
from __future__ import annotations

import email.message
import importlib.util
import sys
import urllib.request
from pathlib import Path
from typing import Any

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"


def _load(name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


issue_transport = _load("issue_transport")

TOKEN = "ghp_fake_token_for_this_test_only"
API_HOST = "api.github.com"
OTHER_HOST = "evil.example.com"
ISSUE_PATH = "repos/Tsadoq/claude-better-plan/issues/25"


class _FakeResponse:

    def __init__(self, status: int, payload: bytes = b"{}", location: str | None = None) -> None:
        self.code = status
        self.status = status
        self.msg = "Found" if location else "OK"
        self.headers = email.message.Message()
        if location is not None:
            self.headers["Location"] = location
        self._payload = payload

    def info(self) -> email.message.Message:
        return self.headers

    def read(self) -> bytes:
        return self._payload

    def close(self) -> None:
        return None


class _ReplayHandler(urllib.request.HTTPSHandler):

    def __init__(self, responses: list[_FakeResponse]) -> None:
        super().__init__()
        self._responses = list(responses)
        self.requests: list[urllib.request.Request] = []

    def https_open(self, request: urllib.request.Request) -> _FakeResponse:
        self.requests.append(request)
        assert self._responses, "the transport made more calls than the test queued responses"
        return self._responses.pop(0)


def _header(request: urllib.request.Request, name: str) -> str | None:
    wanted = name.lower()
    for key, value in request.header_items():
        if key.lower() == wanted:
            return str(value)
    return None


def _reissued_request(location: str) -> urllib.request.Request:
    handler = _ReplayHandler([_FakeResponse(302, location=location), _FakeResponse(200, b'{"number": 25}')])
    transport = issue_transport.RestTransport(
        env={"GH_TOKEN": TOKEN},
        opener=urllib.request.build_opener(issue_transport._NoRedirects, handler),
    )
    transport.run(
        issue_transport.Invocation(summary="read issue 25", method="GET", url=ISSUE_PATH)
    )

    assert len(handler.requests) == 2, f"expected an original and one re-issue, got {len(handler.requests)}"
    assert _header(handler.requests[0], "Authorization") == f"Bearer {TOKEN}", (
        "the original request must carry the token, or the test proves nothing about dropping it"
    )
    return handler.requests[1]


def test_rest_transport_drops_authorization_on_cross_host_redirect() -> None:
    cross_host = _reissued_request(f"https://{OTHER_HOST}/{ISSUE_PATH}")
    assert _header(cross_host, "Authorization") is None, (
        "the token was forwarded to a host other than the one it was issued for"
    )
    assert TOKEN not in "".join(value for _, value in cross_host.header_items()), (
        "the token survived under some other header name"
    )
    assert _header(cross_host, "Host") == OTHER_HOST, (
        "the re-issued request kept the first hop's Host header, so it names one host and asks for another"
    )

    same_host = _reissued_request(f"https://{API_HOST}/repositories/12345/issues/25")
    assert _header(same_host, "Authorization") == f"Bearer {TOKEN}", (
        "a same-host redirect must keep the token, or every Enterprise redirect 401s"
    )
