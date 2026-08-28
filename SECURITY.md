# Security Policy

## Supported Scope

This college project receives security fixes on its current main development
line. It is not certified for medical, clinical, or high-risk production use.

## Reporting A Vulnerability

Do not open a public issue containing credentials, tokens, personal data, or a
working exploit. Contact the project maintainer privately with the affected
version, reproduction steps, impact, and a minimal non-personal test case.

## Implemented Controls

- Argon2-based password hashing through `pwdlib`.
- Expiring signed JWT access tokens with restricted claims.
- Generic login failures and dummy-hash verification for unknown accounts.
- Backend authentication, ownership, workflow prerequisite, and admin checks.
- Restricted configured CORS origins and production secret validation.
- Layered image validation, random storage names, path confinement, image
  decoding, dimension limits, decompression-bomb protection, orientation
  normalization, and metadata removal.
- Private temporary storage, expiry, explicit image consent, and cleanup tools.
- Request IDs, safe error envelopes, structured operational logs, security
  headers, and bounded process-local rate limits.
- Dependency lockfiles, audit commands, tests, and CI definitions.

## Deployment Requirements

Use HTTPS, a random JWT secret of at least 32 characters, a non-public MongoDB,
least-privilege service accounts, encrypted storage/backups, restricted firewall
rules, and centralized secret management. Set `ENABLE_HSTS=true` only after HTTPS
is correct. Keep `AI_DEMO_MODE=false` for any non-demonstration environment.

## Known Security Limitations

- Access tokens are stored in `localStorage` and cannot be revoked server-side.
- Rate limits are process-local and do not coordinate across multiple workers.
- Temporary files are local unless a deployment replaces that storage layer.
- There is no malware scanner, content-disarm service, WAF, MFA, email
  verification, password reset, or formal penetration test.
- In-memory operational metrics reset at process restart.

See [PRIVACY.md](PRIVACY.md) for data handling and
[documentation/deployment.md](documentation/deployment.md) for deployment controls.

