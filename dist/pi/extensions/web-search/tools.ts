// Vendored from @bytetrue/pi-web-search 0.6.0 (MIT, see ../../THIRD_PARTY_LICENSES.md).
// Modified: only web_search is registered here. The upstream web_fetch tool and
// /web setup command are removed so @zeldrisho/pi-web-fetch owns web_fetch.
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { Type } from "typebox";
import { readConfig } from "./config.js";
import type { SearchResult } from "./providers/types.js";
import { searchWithProvider } from "./search.js";

const MIN_SEARCH_RESULTS = 1;
const MAX_SEARCH_RESULTS = 10;
const DEFAULT_SEARCH_RESULTS = 5;

function clampResultCount(requested: number | undefined): number {
	const value = requested ?? DEFAULT_SEARCH_RESULTS;
	return Math.min(Math.max(value, MIN_SEARCH_RESULTS), MAX_SEARCH_RESULTS);
}

export function formatSearchResults(query: string, results: SearchResult[], backend?: string): string {
	let text = `**Search results for "${query}":**\n`;
	if (backend) text += `Search provider: ${backend}\n`;
	text += "\n";
	results.forEach((result, index) => {
		text += `${index + 1}. **${result.title}**\n   ${result.url}\n   ${result.snippet}\n\n`;
	});
	return text.trimEnd();
}

export function registerWebSearchTool(pi: ExtensionAPI): void {
	pi.registerTool({
		name: "web_search",
		label: "Web Search",
		description: "Search the web for current information. Returns titles, URLs, and snippets from one provider.",
		parameters: Type.Object({
			query: Type.String(),
			max_results: Type.Optional(
				Type.Number({
					default: DEFAULT_SEARCH_RESULTS,
					minimum: MIN_SEARCH_RESULTS,
					maximum: MAX_SEARCH_RESULTS,
				}),
			),
		}),

		async execute(_toolCallId, params, signal, onUpdate) {
			const maxResults = clampResultCount(params.max_results);
			const config = readConfig();
			const outcome = await searchWithProvider(
				config,
				undefined,
				params.query,
				maxResults,
				signal,
				(progress) => {
					onUpdate?.({
						content: [{ type: "text", text: `Searching ${progress.label} for: "${params.query}"...` }],
						details: { query: params.query, backend: progress.provider, resultCount: 0 },
					});
				},
			);

			if (outcome.results.length === 0) {
				return {
					content: [{ type: "text", text: `No results found for "${params.query}". Provider: ${outcome.backend}.` }],
					details: {
						query: params.query,
						backend: outcome.backend,
						attemptedProviders: outcome.attemptedProviders,
						resultCount: 0,
					},
				};
			}
			return {
				content: [{ type: "text", text: formatSearchResults(params.query, outcome.results, outcome.backend) }],
				details: {
					query: params.query,
					backend: outcome.backend,
					attemptedProviders: outcome.attemptedProviders,
					resultCount: outcome.results.length,
					results: outcome.results,
				},
			};
		},
	});
}
