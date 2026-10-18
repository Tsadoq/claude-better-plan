"""The pi build's tool names, owned here alone.

The pi profile's token map and every pi test import these instead of restating
them, so a renamed tool changes in one place.
"""

from __future__ import annotations

# Registered by the TypeScript vendored under ``hosts/pi/extensions/``.
VENDORED_TOOLS = ("questionnaire", "subagent", "web_search")

# Registered by the npm extension packages the pi manifest depends on
# (``@zeldrisho/pi-web-fetch`` and ``@ssk_dev/rpiv-todo-lean``).
NPM_TOOLS = ("web_fetch", "todo")
