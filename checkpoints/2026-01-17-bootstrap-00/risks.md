# Risks & Guardrails

- This playbook installs and enables `firewalld`. If your host policy manages firewall differently, confirm compatibility.
- The Nginx vhost is HTTP-only. If the host enforces HTTPS-only via global redirects, ensure it doesn't break `/.well-known` ACME challenges.
- Containers are not deployed yet; upstream ports `18080/18081` must remain localhost-only.
