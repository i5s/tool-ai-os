# Security Review

## Checklist
- HTTPS: enforced via Caddy auto-TLS
- Secure cookies: enabled
- Session expiration: enabled
- Auth required on protected endpoints: enabled
- Feature flags protected: per sprint guidance
- Secrets outside repo: via environment variables only
