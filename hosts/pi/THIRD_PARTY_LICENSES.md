# Third-party licenses

The pi build vendors TypeScript extensions from two MIT-licensed upstreams. Each
file below keeps its upstream licence; files marked "modified" were changed for
this build, as their header comments say.

## pi examples (earendil-works/pi)

Source: `examples/extensions/` of the pi repository. Licence: MIT, reproduced in full below.

- extensions/questionnaire.ts (modified: non-TUI fallback)
- extensions/subagent/index.ts (modified: "package" agent source type)
- extensions/subagent/agents.ts (modified: "package" agent source)

```
MIT License

Copyright (c) 2025 Mario Zechner

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.```

## @bytetrue/pi-web-search 0.6.0

Source: `packages/pi-web-search/src/` of https://github.com/ByteTrue/pi-package-mono.
Licence: MIT, as declared by the package's `package.json` (`"license": "MIT"`,
author "byte"). The upstream repository ships no LICENSE file, so the standard MIT
text is reproduced below with that author.

- extensions/web-search/index.ts (modified: registers web_search only)
- extensions/web-search/tools.ts (modified: web_fetch tool and /web command removed)
- extensions/web-search/config.ts
- extensions/web-search/html.ts
- extensions/web-search/proxy.ts
- extensions/web-search/response-body.ts
- extensions/web-search/search.ts
- extensions/web-search/providers/bing.ts
- extensions/web-search/providers/exa-free.ts
- extensions/web-search/providers/factory.ts
- extensions/web-search/providers/json-provider.ts
- extensions/web-search/providers/registry.ts
- extensions/web-search/providers/types.ts

```
MIT License

Copyright (c) byte

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## Original to this project

Not vendored; covered by this repository's own licence.

- extensions/session-end.ts
