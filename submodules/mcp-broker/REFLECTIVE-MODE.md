# Dynamic tool discovery

The broker exposes three meta-tools through both stdio and HTTP. It connects to configured upstream servers on demand, caches complete tool lists in memory and keeps optional registry/override entries compatible.

## Search, describe, invoke

| Tool | Input | Result |
| --- | --- | --- |
| `broker.search` | Optional string `q` and array of configured server IDs `servers` | Compact server/name/title/description summaries |
| `broker.describe` | Required `server` and exact upstream `tool` name | The full definition, including input/output schemas and annotations when provided |
| `broker.invoke` | Required `server`, `tool`; optional `args` object | The unchanged upstream tool result, including error flags and complete content |

Search can be the first operation with a nonempty query; a cold cache does not mean a tool is absent. When the relevant server is known, set `servers` to avoid connecting to unrelated configured servers. Unknown server IDs and malformed arguments fail explicitly.

Search returns summaries, so use the selected tool's actual schema before constructing arguments. A description is not a schema and an example tool name is not proof that your server exposes it. Then invoke with the exact server/tool pair and validated arguments. Already known definitions can be reused while their server contract is unchanged.

The first search content block remains a JSON array for existing consumers. If an upstream list fails, a second text block identifies the failed server IDs and says discovery is incomplete. When no result could be returned and a server failed, `isError` is true. Never treat a partial list as proof that an unlisted tool does not exist.

## Caching and pagination

Search and describe fetch every `tools/list` page before committing a server's list to the cache. Repeated cursors fail instead of looping forever or caching an incomplete list. Later discovery reuses the cached definitions. Invocation alone can establish a connection without listing tools. The pinned SDK replaces its output-validator cache on each list page, so the broker also validates against the complete cached catalog through the SDK's public JSON Schema validator. A successful tool with an output schema must supply matching structured content; an error without structured content is passed through, while structured content that is present must still match its schema.

The cache lasts for this broker process and is cleared by disconnect. There is no TTL or live list-change refresh in this implementation; restart after changing an upstream catalog/configuration. No measured latency or token-saving percentage is promised.

## Optional favorites and legacy registry

`tools.overrides.json` holds favorite names/descriptions; `tools.registry.json` remains compatible with earlier installs. Overrides precede matching registry/upstream summaries. Direct names keep their existing dispatch behavior. Their discovery metadata does not replace the upstream argument contract: use `broker.describe` to inspect it. New setups can leave both files empty and use the three meta-tools.

For configuration syntax see [README](README.md) and [setup](SETUP.md). Credentials remain in the existing secret-resolution layer; this feature does not introduce a new account flow, permission grant, masking guarantee or arbitrary code executor.

## Validate an optimization

Run `npm test` from this directory. The local synthetic tests cover first-query discovery, multiple list pages, server filtering, full schema metadata, partial failures and original invocation output/error flags. They make no account calls. See the [context policy](../../docs/CONTEXT_POLICY.md) for a comparable-task measurement procedure and the distinction between this custom broker, native tool search and programmatic tool calling.
