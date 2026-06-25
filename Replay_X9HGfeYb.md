# Sprint X-15 — Future Extension Points

## Cloudflare
- Extension point: protocol adapter using existing integration pattern.
- No code change needed if adapter is placed behind `toll.ports.*` or a new `toll.integrations.cloudflare` module.

## Aider
- Use extension point through `toll.agents.adapter_factory`
- Add `toll.agents.aider_adapter`

## Additional Agents
- Register additional agent classes by conforming to `toll.agents.adapter` interface.

## Additional MCP Connectors
- Implement via `toll.mcp.client` extension
- Register through documented service facade method
