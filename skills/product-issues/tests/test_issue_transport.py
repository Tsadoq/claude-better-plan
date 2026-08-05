"""Unit test for issue_transport.py's manual redirect handling.

`RestTransport` carries a bearer token on every request, and the standard
library's `HTTPRedirectHandler` copies a request's headers across a redirect
untouched apart from `content-length` and `content-type` (verified against the
local stdlib source while this was planned). A redirect a repository owner can
influence would therefore hand the token to whatever host the `Location` names,
so the transport turns automatic redirects off and re-issues them itself. This
module pins that decision from both sides: dropped when the target host
differs, kept when it does not. Keeping it on the same host is half the test
rather than an afterthought -- a transport that dropped the header
unconditionally would pass a one-sided test while failing every Enterprise
deployment that redirects within its own host.

The fake stands in for the socket rather than for the opener, which is what
makes the test worth having. Everything above the socket runs for real: the
transport's own `_NoRedirects` handler, urllib's error processing, and the fact
that a refused redirect arrives as a raised `HTTPError` rather than as a
returned response. A fake that simply returned a 302 would leave the branch
production takes on every redirect -- the `except HTTPError` one -- unexercised,
and would pass just as happily if that branch did not exist.

No network is reached: the replay handler answers every request from a queue.

Runnable two ways:
    python3 -m pytest skills/product-issues/tests/test_issue_transport.py
    uv run pytest skills/product-issues/tests/test_issue_transport.py
"""

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
    # Registered before it is executed, unlike the sibling suites' loaders: a
    # module holding dataclasses with string annotations (which
    # `from __future__ import annotations` makes all of them) has `@dataclass`
    # resolve those names through `sys.modules[cls.__module__]`, and an
    # unregistered module makes that lookup return None mid-decoration.
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


issue_transport = _load("issue_transport")

TOKEN = "ghp_fake_token_for_this_test_only"
API_HOST = "api.github.com"
OTHER_HOST = "evil.example.com"
ISSUE_PATH = "repos/Tsadoq/claude-better-plan/issues/25"


class _FakeResponse:
    """The subset of `http.client.HTTPResponse` that urllib and the transport
    read between them. It answers to urllib first -- `HTTPErrorProcessor` takes
    `code`, `msg` and `info()` before the transport sees anything -- and only
    then to the transport, which reads `status`, `headers` and `read()`."""

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
    """Answers each request from a queue instead of opening a socket, and
    records the requests as urllib finally had them -- after `Host` and
    `Content-length` were filled in, which is where a header copied forward
    from the previous hop would show up."""

    def __init__(self, responses: list[_FakeResponse]) -> None:
        super().__init__()
        self._responses = list(responses)
        self.requests: list[urllib.request.Request] = []

    def https_open(self, request: urllib.request.Request) -> _FakeResponse:
        self.requests.append(request)
        assert self._responses, "the transport made more calls than the test queued responses"
        return self._responses.pop(0)


def _header(request: urllib.request.Request, name: str) -> str | None:
    """`request`'s header value under a case-insensitive name lookup, across
    both header sets urllib keeps. Case matters because urllib rewrites the
    keys it is given, and both sets matter because a leak into the
    unredirected half would count just the same."""
    wanted = name.lower()
    for key, value in request.header_items():
        if key.lower() == wanted:
            return str(value)
    return None


def _reissued_request(location: str) -> urllib.request.Request:
    """Run one GET answered with a 302 to `location` and then a 200, and return
    the request the transport built for the second hop."""
    handler = _ReplayHandler([_FakeResponse(302, location=location), _FakeResponse(200, b'{"number": 25}')])
    transport = issue_transport.RestTransport(
        env={"GH_TOKEN": TOKEN},
        # Production's own redirect refusal, wrapped around the fake socket, so
        # the 302 arrives here exactly as it arrives in production.
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
