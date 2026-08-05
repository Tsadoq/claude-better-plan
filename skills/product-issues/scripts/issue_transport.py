
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, Protocol, TextIO

API_VERSION = "2026-03-10"

USER_AGENT = "claude-better-plan-product-issues"

GITHUB_API_BASE = "https://api.github.com"

DEFAULT_TIMEOUT = 30.0

MAX_REDIRECTS = 5

CONTENT_CREATIONS_PER_MINUTE = 80
_CREATE_INTERVAL = 60.0 / CONTENT_CREATIONS_PER_MINUTE

_THROTTLED = frozenset({403, 429})
_MAX_RETRIES = 3

_MAX_RETRY_SLEEP = 60.0

_REDIRECT_STATUSES = frozenset({301, 302, 303, 307, 308})

DRY_RUN_URL_SCHEME = "dry-run"


class TransportError(RuntimeError):
    """Base for every failure this module raises, so a caller can catch the
    family without naming each member."""


class MissingToken(TransportError):
    """Neither `GH_TOKEN` nor `GITHUB_TOKEN` is set, so the REST path has no
    credential. Raised at construction: a transport that cannot authenticate is
    better refused before a batch starts than in the middle of one."""


class UnsupportedInvocation(TransportError):
    """An invocation spelled for a transport that cannot execute it -- a
    subprocess call handed to `RestTransport`, which speaks only HTTP."""


class TooManyRedirects(TransportError):
    """A redirect chain longer than `MAX_REDIRECTS`, which is a loop rather
    than a route."""


class CallFailed(TransportError):
    """One outbound call that did not succeed, carrying the summary of what was
    being attempted so the message reads as an action rather than a status."""

    def __init__(self, summary: str, status: int | None, detail: str) -> None:
        self.summary = summary
        self.status = status
        self.detail = detail
        where = f" (status {status})" if status is not None else ""
        super().__init__(f"{summary} failed{where}: {detail}")


@dataclass(frozen=True)
class Invocation:
    """One outbound call, described once and spelled either way.

    A call is written either as `argv`, for something only a CLI can do, or as
    `method`/`url`/`body` for an API call. `url` is an API *path* relative to
    the host's REST base (`repos/owner/name/issues`), not an absolute URL:
    `RestTransport` joins it to its base and `GhTransport` hands it to
    `gh api`, so the same invocation runs on either path.

    `summary` is a human sentence saying what the call does. It is what the dry
    run prints and what a failure names, which is why it is required rather
    than derived: a generated summary would describe the spelling, and a reader
    of a dry run needs to know what is about to happen to their repository.
    """

    summary: str
    argv: tuple[str, ...] = ()
    method: str = ""
    url: str = ""
    body: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        spelled_as_api = bool(self.method and self.url)
        if bool(self.argv) == spelled_as_api:
            raise ValueError(
                f"{self.summary!r} must be spelled either as argv or as method and url, not both or neither"
            )


@dataclass(frozen=True)
class Result:
    """What a successful call returned.

    `json` is the decoded response body, or None when there was none -- a 204,
    or a CLI call whose stdout is not JSON. `stdout` is the raw text a
    subprocess printed and is empty for an API call. `status` is the HTTP
    status, or 0 for a subprocess call, and is informational: a failure raises
    `CallFailed`, so a `Result` in hand already means success and no caller
    needs to branch on it.
    """

    status: int
    json: Any = None
    stdout: str = ""


@dataclass(frozen=True)
class Filed:
    """An issue that now exists, in the three terms the rest of the beat uses.

    `id` is the internal database id and `number` is the issue number a person
    reads; they are unrelated values (5046900288 against 25 on a captured real
    issue). The distinction is load-bearing because the sub-issue and
    dependency endpoints accept only the id, so keeping both here is what stops
    a caller reaching for whichever integer is nearest.
    """

    number: int
    id: int
    url: str


class Transport(Protocol):
    """What every implementation offers and the whole of what callers may use."""

    def run(self, invocation: Invocation) -> Result:
        """Carry out `invocation` and return what it produced. Raises
        `TransportError` on any failure."""
        ...

    def create_issue(self, repo: str, title: str, body: str) -> Filed:
        """Create an issue in `repo` (`owner/name`) and return it normalised,
        whatever the underlying path had to do to learn its database id."""
        ...


def _create_summary(repo: str, title: str) -> str:
    """The one sentence every path uses for a create, so that what a dry run
    prints and what a failure names are the same words."""
    return f"create issue in {repo}: {title}"


def _create_issue_call(repo: str, title: str, body: str) -> Invocation:
    """The single description of what creating an issue is.

    Held here rather than written out inside each implementation: the dry run
    and the REST path both send exactly this, so a field the endpoint gains
    cannot be added to one and forgotten in the other, which is how a dry run
    starts previewing a call nobody makes. `GhTransport` spells its create as a
    CLI command instead and so builds its own argv, but takes its summary from
    `_create_summary` for the same reason.
    """
    return Invocation(
        summary=_create_summary(repo, title),
        method="POST",
        url=f"repos/{repo}/issues",
        body={"title": title, "body": body},
    )


class GhTransport:
    """Shells out to `gh`, which owns the credential.

    Delegating authentication is the whole reason to prefer this path: no token
    is read here and none is ever placed on a command line, where it would be
    visible to every process listing on the machine.

    API-shaped invocations run through `gh api`, so a caller writes a call once
    and it works on both paths. Unlike `RestTransport` this path does not retry
    a throttled call: `gh api` reports the failure without the response headers
    a retry would have to honour, so it fails loudly and the create pacing below
    is what keeps a batch under the limit in the first place.
    """

    def __init__(
        self,
        *,
        timeout: float = DEFAULT_TIMEOUT,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._timeout = timeout
        self._pacer = _CreatePacer(sleep=sleep)

    def run(self, invocation: Invocation) -> Result:
        """Run `invocation`, as a direct `gh` command when it carries argv and
        through `gh api` when it is spelled as an API call."""
        if invocation.argv:
            return self._shell(list(invocation.argv), None, invocation.summary)

        argv = [
            "gh",
            "api",
            "--method",
            invocation.method.upper(),
            "-H",
            f"X-GitHub-Api-Version: {API_VERSION}",
            invocation.url.lstrip("/"),
        ]
        stdin = None
        if invocation.body is not None:
            argv += ["--input", "-"]
            stdin = json.dumps(invocation.body)
        return self._shell(argv, stdin, invocation.summary)

    def create_issue(self, repo: str, title: str, body: str) -> Filed:
        """Create the issue, then read it back for its database id.

        The second call is not redundant: `gh issue create` prints only the new
        issue's URL and has no `--json` flag, so the id the linking endpoints
        require cannot be had from the create itself.
        """
        self._pacer.wait()
        created = self.run(
            Invocation(
                summary=_create_summary(repo, title),
                argv=("gh", "issue", "create", "--repo", repo, "--title", title, "--body", body),
            )
        )
        number = _number_from_url(_issue_url(created.stdout, title), title)
        fetched = self.run(
            Invocation(
                summary=f"read issue {number} in {repo} for its database id",
                method="GET",
                url=f"repos/{repo}/issues/{number}",
            )
        )
        return _filed(fetched.json, f"read issue {number} in {repo} for its database id")

    def _shell(self, argv: list[str], stdin: str | None, summary: str) -> Result:
        try:
            completed = subprocess.run(  # noqa: S603 -- argv list, never a shell string
                argv,
                input=stdin,
                capture_output=True,
                text=True,
                timeout=self._timeout,
                check=False,
            )
        except FileNotFoundError as err:
            raise CallFailed(summary, None, f"{argv[0]} is not on PATH") from err
        except subprocess.TimeoutExpired as err:
            raise CallFailed(summary, None, f"no answer within {self._timeout:g}s") from err

        if completed.returncode != 0:
            raise CallFailed(summary, completed.returncode, completed.stderr.strip() or "no stderr")
        return Result(status=0, json=_decode(completed.stdout), stdout=completed.stdout)


class RestTransport:
    """Talks to the REST API directly, for machines with no `gh` installed.

    Reads `GH_TOKEN` then `GITHUB_TOKEN`, the same order and the same names
    `gh` itself reads, so a user who has already authenticated is not asked for
    a second credential.

    Redirects are followed by hand rather than by the stdlib -- see the module
    docstring. `opener` is injectable for the tests that pin that handling;
    production passes nothing and gets an opener with redirects disabled.
    """

    def __init__(
        self,
        base_url: str = GITHUB_API_BASE,
        *,
        env: Mapping[str, str] | None = None,
        opener: _Opener | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._base = base_url.rstrip("/")
        self._token = _read_token(os.environ if env is None else env)
        self._opener = _non_redirecting_opener() if opener is None else opener
        self._timeout = timeout
        self._sleep = sleep
        self._pacer = _CreatePacer(sleep=sleep)

    def run(self, invocation: Invocation) -> Result:
        """Issue `invocation` as an HTTP request, retrying while GitHub says it
        is throttling and raising `CallFailed` on any other non-2xx."""
        if invocation.argv:
            raise UnsupportedInvocation(
                f"{invocation.summary!r} is spelled as a subprocess call, which the REST path cannot run"
            )

        attempt = 0
        while True:
            status, headers, payload = self._send(invocation)
            if 200 <= status < 300:
                return Result(status=status, json=_decode(payload.decode("utf-8", errors="replace")))

            delay = _throttle_delay(headers, time.time()) if status in _THROTTLED else None
            if delay is None or delay > _MAX_RETRY_SLEEP or attempt >= _MAX_RETRIES:
                raise CallFailed(invocation.summary, status, _api_message(payload))
            attempt += 1
            self._sleep(delay)

    def create_issue(self, repo: str, title: str, body: str) -> Filed:
        """Create the issue. The 201 carries both `id` and `number`, so unlike
        the CLI path this needs no follow-up read."""
        self._pacer.wait()
        call = _create_issue_call(repo, title, body)
        return _filed(self.run(call).json, call.summary)

    def _send(self, invocation: Invocation) -> tuple[int, Mapping[str, str], bytes]:
        """One request and its redirect chain, returning the first response
        that is not a redirect."""
        request = self._build(invocation.method, self._absolute(invocation.url), invocation.body)
        for _ in range(MAX_REDIRECTS):
            status, headers, payload = self._open(request, invocation.summary)
            location = headers.get("Location")
            if status not in _REDIRECT_STATUSES or not location:
                return status, headers, payload
            request = _redirected(request, urllib.parse.urljoin(request.full_url, location))
        raise TooManyRedirects(f"{invocation.summary}: more than {MAX_REDIRECTS} redirects")

    def _open(self, request: urllib.request.Request, summary: str) -> tuple[int, Mapping[str, str], bytes]:
        try:
            response = self._opener.open(request, timeout=self._timeout)
        except urllib.error.HTTPError as err:
            return int(err.status or err.code), err.headers, err.read()
        except OSError as err:
            raise CallFailed(summary, None, str(err)) from err

        try:
            return int(response.status), response.headers, response.read()
        finally:
            response.close()

    def _build(self, method: str, url: str, body: dict[str, Any] | None) -> urllib.request.Request:
        data = None if body is None else json.dumps(body).encode("utf-8")
        request = urllib.request.Request(url, data=data, method=method.upper())
        request.add_header("Authorization", f"Bearer {self._token}")
        request.add_header("Accept", "application/vnd.github+json")
        request.add_header("X-GitHub-Api-Version", API_VERSION)
        request.add_header("User-Agent", USER_AGENT)
        if data is not None:
            request.add_header("Content-Type", "application/json")
        return request

    def _absolute(self, path: str) -> str:
        return f"{self._base}/{path.lstrip('/')}"


class DryRunTransport:
    """Describes the calls a real transport would make, and makes none.

    Every invocation is recorded and its summary printed, and `create_issue`
    hands back a placeholder so that the caller's create-then-link sequence
    runs to the end: a dry run that stopped at the first create would not
    exercise the linking it exists to preview.

    It cannot answer a read. Nothing here knows what a repository currently
    contains, so `run` returns an empty body, and a caller that must read live
    state -- the pre-flight ceiling checks -- has to do so through a real
    transport before the dry run begins planning.
    """

    def __init__(self, stream: TextIO | None = None) -> None:
        self.invocations: list[Invocation] = []
        self._stream = sys.stdout if stream is None else stream
        self._created = 0

    def run(self, invocation: Invocation) -> Result:
        """Record and print `invocation`, and return an empty success."""
        self._record(invocation)
        return Result(status=200)

    def create_issue(self, repo: str, title: str, body: str) -> Filed:
        """Record the create that would have happened and return a placeholder.

        The placeholder number and id are negative and distinct per create, so
        a link built on one is traceable to the create it came from and can
        never collide with a real issue.
        """
        self._record(_create_issue_call(repo, title, body))
        self._created += 1
        return Filed(
            number=-self._created,
            id=-self._created,
            url=f"{DRY_RUN_URL_SCHEME}://{repo}/issues/{self._created}",
        )

    def _record(self, invocation: Invocation) -> None:
        self.invocations.append(invocation)
        print(invocation.summary, file=self._stream)


class _Opener(Protocol):
    """The one method `RestTransport` needs from an opener, named so that the
    test fake and `urllib.request.OpenerDirector` are interchangeable."""

    def open(self, request: urllib.request.Request, timeout: float) -> Any: ...


class _NoRedirects(urllib.request.HTTPRedirectHandler):
    """Refuses every redirect, which makes the stdlib raise it as an
    `HTTPError` that `RestTransport` then re-issues under its own rules."""

    def redirect_request(self, *args: Any, **kwargs: Any) -> None:
        return None


def _non_redirecting_opener() -> _Opener:
    opener: Any = urllib.request.build_opener(_NoRedirects)
    return opener


class _CreatePacer:
    """Keeps successive creates at least `_CREATE_INTERVAL` apart.

    Spacing beforehand rather than retrying afterwards is deliberate: a tripped
    secondary limit is answered with a 403 that looks like a permission
    failure, and a batch that trips one has already filed part of itself.
    """

    def __init__(
        self,
        *,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._sleep = sleep
        self._clock = clock
        self._last: float | None = None

    def wait(self) -> None:
        """Block until the next create may go out."""
        if self._last is not None:
            remaining = _CREATE_INTERVAL - (self._clock() - self._last)
            if remaining > 0:
                self._sleep(remaining)
        self._last = self._clock()


def _read_token(env: Mapping[str, str]) -> str:
    for name in ("GH_TOKEN", "GITHUB_TOKEN"):
        token = env.get(name, "").strip()
        if token:
            return token
    raise MissingToken("set GH_TOKEN or GITHUB_TOKEN, or install gh, to reach the GitHub API")


def _origin(url: str) -> tuple[str, str]:
    """Scheme and host, lowercased. A scheme change counts as an origin change
    for the same reason a host change does: an https token must not travel over
    plain http, even to the host that issued it."""
    parts = urllib.parse.urlsplit(url)
    return parts.scheme.lower(), parts.netloc.lower()


def _redirected(request: urllib.request.Request, target: str) -> urllib.request.Request:
    """`request` re-aimed at `target`, carrying `Authorization` only when the
    origin is unchanged.

    Only `request.headers` is copied, never `header_items()`, which would also
    return the unredirected headers. Those are the ones urllib computes per
    target -- `Host` above all -- and copying them forward would send the new
    host a `Host` naming the old one. The stdlib's own `redirect_request` reads
    the same half for the same reason; leaving them out is what lets urllib
    recompute them for `target`.
    """
    keep_token = _origin(target) == _origin(request.full_url)
    redirected = urllib.request.Request(target, data=request.data, method=request.get_method())
    for key, value in request.headers.items():
        if not keep_token and key.lower() == "authorization":
            continue
        redirected.add_header(key, value)
    return redirected


def _throttle_delay(headers: Mapping[str, str], now: float) -> float | None:
    """Seconds to wait before retrying, or None when the response carries no
    rate-limit hint and so is a real failure rather than a throttle.

    `Retry-After` is honoured first because GitHub sends it only when it has an
    answer; `x-ratelimit-reset` is the fallback and means something only once
    the remaining count has reached zero.
    """
    after = _as_int(headers.get("Retry-After"))
    if after is not None:
        return max(0.0, float(after))

    if (headers.get("x-ratelimit-remaining") or "").strip() == "0":
        reset = _as_int(headers.get("x-ratelimit-reset"))
        if reset is not None:
            return max(0.0, reset - now)
    return None


def _as_int(raw: str | None) -> int | None:
    try:
        return int((raw or "").strip())
    except ValueError:
        return None


def _decode(text: str) -> Any:
    """The decoded JSON body, or None when there is none to decode."""
    stripped = text.strip()
    if not stripped:
        return None
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        return None


def _api_message(payload: bytes) -> str:
    """GitHub's own explanation of a failure, which is far more useful than the
    status alone: 404 covers both a missing repository and one the token cannot
    see, and 410 is issues being disabled."""
    decoded = _decode(payload.decode("utf-8", errors="replace"))
    if isinstance(decoded, dict):
        message = decoded.get("message")
        if isinstance(message, str) and message:
            return message
    return payload.decode("utf-8", errors="replace").strip() or "no response body"


def _issue_url(stdout: str, title: str) -> str:
    """The issue URL `gh issue create` printed. It prints progress lines too,
    so the last line that looks like a URL is the answer rather than the last
    line."""
    for line in reversed(stdout.splitlines()):
        candidate = line.strip()
        if candidate.startswith("http"):
            return candidate
    raise CallFailed(f"create issue: {title}", None, f"gh printed no issue URL: {stdout.strip()!r}")


def _number_from_url(url: str, title: str) -> int:
    number = _as_int(url.rstrip("/").rsplit("/", 1)[-1])
    if number is None:
        raise CallFailed(f"create issue: {title}", None, f"no issue number in {url!r}")
    return number


def _filed(payload: Any, summary: str) -> Filed:
    """An issue payload turned into `Filed`, refusing a response that is
    missing any of the three fields rather than defaulting one."""
    if not isinstance(payload, dict):
        raise CallFailed(summary, None, "expected an issue object in the response")
    try:
        return Filed(number=int(payload["number"]), id=int(payload["id"]), url=str(payload["html_url"]))
    except (KeyError, TypeError, ValueError) as err:
        raise CallFailed(summary, None, f"issue response missing number, id or html_url: {err}") from err
