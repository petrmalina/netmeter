# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.x     | ✅        |

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly:

1. **Do NOT** open a public issue
2. Email the maintainer or use [GitHub's private vulnerability reporting](https://github.com/petrmalina/netmeter/security/advisories/new)
3. Include a description of the vulnerability, steps to reproduce, and potential impact

You should receive a response within 48 hours. We will work with you to understand and address the issue before any public disclosure.

## Security Best Practices

When using NetMeter:

- Keep your `.env` file out of version control (it's in `.gitignore` by default)
- Use environment variables for sensitive configuration
- Keep dependencies updated (Dependabot is configured for this repo)
- Run the Docker container with minimal privileges
