/**
 * Vendored from @bytetrue/pi-web-search 0.6.0 (MIT, see ../../THIRD_PARTY_LICENSES.md).
 * Modified: registers web_search only. The upstream web_fetch tool and /web
 * setup command are removed so @zeldrisho/pi-web-fetch owns web_fetch.
 * Providers are configured through the package's config file or env vars.
 */

import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { readConfig } from "./config.js";
import { installProxyDispatcher } from "./proxy.js";
import { registerWebSearchTool } from "./tools.js";

export default async function registerWebTools(pi: ExtensionAPI): Promise<void> {
	// Configure package-scoped proxy transport for this extension only. Uses
	// config `proxy`, else HTTP(S)_PROXY / ALL_PROXY; no-op when unset.
	await installProxyDispatcher(readConfig().proxy);
	registerWebSearchTool(pi);
}
